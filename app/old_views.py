from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import *
from django.views.decorators.http import require_POST
import json
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db.models import Count, Q, Avg
from django.urls import reverse

def inicio_investigador(request):
    proyectos = Proyecto.objects.all().select_related('investigador').annotate(
        total_expertos_seleccionados=Count(
            'lista_chequeo_expertos',
            filter=Q(lista_chequeo_expertos__estado='seleccionado')
        )
    )
    
    return render(request, 'investigadores/inicio.html', {
        'proyectos': proyectos
    })

def seleccion_expertos(request, proyecto_id):
    """Vista principal de selección de expertos para un proyecto"""
    proyecto = get_object_or_404(Proyecto.objects.select_related('investigador'), id=proyecto_id)
    
    proceso_finalizado = ListaChequeo.objects.filter(
        proyecto=proyecto,
        estado='seleccionado'
    ).exists()
    
    # Obtener todos los expertos con sus métricas calculadas
    expertos = Experto.objects.all().select_related('usuario').order_by('id')
    
    encuestas_estado = dict(
        EncuestaSatisfaccion.objects.filter(proyecto=proyecto).values_list('experto_id', 'estado')
    )
    
    # Función para ordenar (placeholder - puedes implementar lógica real)
    orden = request.GET.get('orden', 'id')
    if orden == 'nombre':
        expertos = expertos.order_by('usuario__first_name', 'usuario__last_name')
    elif orden == 'coeficiente':
        expertos = expertos.order_by('-coeficiente_experticidad')
    elif orden == 'grado':
        expertos = expertos.order_by('grado_cientifico')
    elif orden == 'experiencia':
        expertos = expertos.order_by('-anos_experiencia')
    
    return render(request, 'investigadores/seleccion_expertos.html', {
        'proyecto': proyecto,
        'expertos': expertos,
        'encuestas_estado': encuestas_estado,
        'proceso_finalizado': proceso_finalizado,
        'orden_actual': orden
    })

def detalle_experto(request, experto_id):
    """Vista AJAX para ver detalles del experto"""
    experto = get_object_or_404(Experto.objects.select_related('usuario'), id=experto_id)
    
    # Calcular estadísticas
    encuestas = EncuestaSatisfaccion.objects.filter(experto=experto)
    aportes = AporteExperto.objects.filter(experto=experto)
    
    data = {
        'nombre': experto.usuario.get_full_name(),
        'email': experto.usuario.email,
        'grado': experto.get_grado_cientifico_display(),
        'cargo': experto.cargo_actual or 'No especificado',
        'departamento': experto.departamento or 'No especificado',
        'experiencia': experto.anos_experiencia,
        'coeficiente': str(experto.coeficiente_experticidad or 'N/A'),
        'indice': str(experto.indice_experticidad or 'N/A'),
        'total_encuestas': encuestas.count(),
        'total_aportes': aportes.count(),
        'proyectos_activos': aportes.filter(
            estado__in=['invitado', 'participando']
        ).count(),
    }
    
    return JsonResponse(data)

def enviar_encuesta(request, proyecto_id, experto_id):
    """Vista AJAX para enviar encuesta a un experto"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    experto = get_object_or_404(Experto, id=experto_id)
    
    # Verificar si ya tiene encuesta
    if EncuestaSatisfaccion.objects.filter(proyecto=proyecto, experto=experto).exists():
        return JsonResponse({'error': 'El experto ya tiene una encuesta activa'}, status=400)
    
    try:
        # Crear encuesta con datos del experto
        encuesta = EncuestaSatisfaccion.objects.create(
            proyecto=proyecto,
            experto=experto,
            cargo_actual=experto.cargo_actual or '',
            anos_experiencia=experto.anos_experiencia,
            grado_cientifico=experto.grado_cientifico
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Encuesta enviada a {experto.usuario.get_full_name()}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def encuesta_satisfaccion(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    proceso_finalizado = ListaChequeo.objects.filter(
        proyecto=proyecto,
        estado='seleccionado'
    ).exists()
    
    encuestas = EncuestaSatisfaccion.objects.filter(
        proyecto=proyecto
    ).select_related('experto__usuario').order_by('-estado', 'experto__usuario__first_name')
    
    return render(request, 'investigadores/encuesta_satisfaccion.html', {
        'proyecto': proyecto,
        'encuestas': encuestas,
        'proceso_finalizado': proceso_finalizado,
        'total_completadas': encuestas.filter(estado='completada').count()
    })

def lista_chequeo(request, proyecto_id):
    """Vista de lista de chequeo de expertos"""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    proceso_finalizado = ListaChequeo.objects.filter(
        proyecto=proyecto,
        estado='seleccionado'
    ).exists()
    
    # ⭐ Obtener expertos seleccionados automáticamente (los que completaron encuesta)
    expertos_finales = ListaChequeo.objects.filter(
        proyecto=proyecto,
        estado='seleccionado'
    ).select_related('experto__usuario')
    
    return render(request, 'investigadores/lista_chequeo.html', {
        'proyecto': proyecto,
        'proceso_finalizado': proceso_finalizado,
        'expertos_finales': expertos_finales
    })


def dashboard_experto(request, experto_id):
    """Dashboard del experto con orden: Pendientes (no bloqueadas) → Completadas → Bloqueadas"""
    experto = get_object_or_404(Experto, id=experto_id)
    
    # Proyectos que ya tienen lista final cerrada
    proyectos_cerrados = set(
        ListaChequeo.objects.filter(estado='seleccionado')
        .values_list('proyecto_id', flat=True)
    )
    
    # 1. Obtener TODAS las pendientes
    encuestas_pendientes = EncuestaSatisfaccion.objects.filter(
        experto=experto, 
        estado='pendiente'
    ).select_related('proyecto')
    
    # 2. Dividir en NO bloqueadas y bloqueadas
    pendientes_no_bloqueadas = []
    pendientes_bloqueadas = []
    for encuesta in encuestas_pendientes:
        if encuesta.proyecto_id in proyectos_cerrados:
            encuesta.bloqueada = True
            pendientes_bloqueadas.append(encuesta)
        else:
            encuesta.bloqueada = False
            pendientes_no_bloqueadas.append(encuesta)
    
    # 3. Completadas ordenadas por fecha (más recientes primero)
    encuestas_completadas = EncuestaSatisfaccion.objects.filter(
        experto=experto, 
        estado='completada'
    ).select_related('proyecto').order_by('-fecha_respuesta')
    
    return render(request, 'expertos/inicio_expertos.html', {
        'experto': experto,
        'pendientes_no_bloqueadas': pendientes_no_bloqueadas,  # ⭐ Primero
        'encuestas_completadas': encuestas_completadas,        # ⭐ Segundo
        'pendientes_bloqueadas': pendientes_bloqueadas,        # ⭐ Tercero
        'encuestas_pendientes_no_bloqueadas': len(pendientes_no_bloqueadas),  # Para contador
    })

def completar_encuesta(request, experto_id, encuesta_id):
    """Vista para que el experto complete su encuesta"""
    experto = get_object_or_404(Experto, id=experto_id)
    encuesta = get_object_or_404(EncuestaSatisfaccion, id=encuesta_id, experto=experto)
    
    if encuesta.experto.id != experto_id:
        return HttpResponseForbidden("No tienes permiso para editar esta encuesta")
    
    if encuesta.estado != 'pendiente':
        messages.warning(request, 'Esta encuesta ya ha sido completada.')
        return redirect('app:dashboard_experto', experto_id=experto_id)
    
    if request.method == 'POST':
        try:
            # Procesar respuestas
            encuesta.cargo_actual = request.POST.get('cargo_actual', '')
            encuesta.anos_experiencia = int(request.POST.get('anos_experiencia', 0))
            encuesta.grado_cientifico = request.POST.get('grado_cientifico', '') or encuesta.grado_cientifico
            encuesta.conocimiento_materia = int(request.POST.get('conocimiento_materia', 0))
            
            # Influencias (A=Alto, M=Medio, B=Bajo)
            encuesta.influencia_analisis_teoricos = request.POST.get('influencia_analisis_teoricos', 'M')
            encuesta.influencia_experiencia = request.POST.get('influencia_experiencia', 'M')
            encuesta.influencia_autores_nacionales = request.POST.get('influencia_autores_nacionales', 'M')
            encuesta.influencia_autores_extranjeros = request.POST.get('influencia_autores_extranjeros', 'M')
            encuesta.influencia_conocimiento_extranjero = request.POST.get('influencia_conocimiento_extranjero', 'M')
            encuesta.influencia_intuicion = request.POST.get('influencia_intuicion', 'M')
            
            # Calcular coeficiente K
            encuesta = calcular_coeficiente_k(encuesta)
            
            encuesta.estado = 'completada'
            encuesta.save()
            
            messages.success(request, '¡Encuesta completada exitosamente!')
            return redirect('app:dashboard_experto', experto_id=experto_id)
            
        except Exception as e:
            messages.error(request, f'Error al guardar la encuesta: {str(e)}')
    
    return render(request, 'expertos/completar_encuesta.html', {
        'encuesta': encuesta,
        'experto': experto,
        'INFLUENCIA_CHOICES': EncuestaSatisfaccion.INFLUENCIA_CHOICES
    })

def guardar_encuesta_ajax(request, experto_id, encuesta_id):
    """Procesa la encuesta vía AJAX y devuelve JSON"""
    experto = get_object_or_404(Experto, id=experto_id)
    encuesta = get_object_or_404(EncuestaSatisfaccion, id=encuesta_id, experto=experto)
    
    # Verificar lista cerrada
    lista_cerrada = ListaChequeo.objects.filter(
        proyecto=encuesta.proyecto,
        estado='seleccionado'
    ).exists()
    
    if lista_cerrada:
        return JsonResponse({
            'success': False,
            'error': 'La lista final está cerrada.'
        }, status=403)
    
    try:
        # Procesar datos
        encuesta.cargo_actual = request.POST.get('cargo_actual', '')
        encuesta.anos_experiencia = int(request.POST.get('anos_experiencia', 0))
        encuesta.grado_cientifico = request.POST.get('grado_cientifico', '')
        encuesta.conocimiento_materia = int(request.POST.get('conocimiento_materia', 5))
        
        # Influencias
        encuesta.influencia_analisis_teoricos = request.POST.get('influencia_analisis_teoricos', 'M')
        encuesta.influencia_experiencia = request.POST.get('influencia_experiencia', 'M')
        encuesta.influencia_autores_nacionales = request.POST.get('influencia_autores_nacionales', 'M')
        
        # Continúa con todas las influencias...
        encuesta.influencia_autores_extranjeros = request.POST.get('influencia_autores_extranjeros', 'M')
        encuesta.influencia_conocimiento_extranjero = request.POST.get('influencia_conocimiento_extranjero', 'M')
        encuesta.influencia_intuicion = request.POST.get('influencia_intuicion', 'M')
        
        # Calcular K
        encuesta = calcular_coeficiente_k(encuesta)
        encuesta.estado = 'completada'
        encuesta.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Encuesta completada.',
            'redirect_url': reverse('app:dashboard_experto', args=[experto_id])
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def calcular_coeficiente_k(encuesta):
    """Calcula el coeficiente de experticidad"""
    # Fórmula simplificada
    pesos = {
        'analisis_teoricos': 0.20,
        'experiencia': 0.15,
        'autores_nacionales': 0.10,
        'autores_extranjeros': 0.15,
        'conocimiento_extranjero': 0.20,
        'intuicion': 0.10,
        'conocimiento_materia': 0.10
    }
    
    try:
        # Convertir letras a valores numéricos (A=10, M=7, B=4)
        valor_influencia = {
            'A': 3.0,  # Alto
            'M': 2.0,  # Medio
            'B': 1.0   # Bajo
        }
        
        total = 0
        
        # Sumar influencias
        total += valor_influencia.get(encuesta.influencia_analisis_teoricos, 2) * pesos['analisis_teoricos']
        total += valor_influencia.get(encuesta.influencia_experiencia, 2) * pesos['experiencia']
        total += valor_influencia.get(encuesta.influencia_autores_nacionales, 2) * pesos['autores_nacionales']
        total += valor_influencia.get(encuesta.influencia_autores_extranjeros, 2) * pesos['autores_extranjeros']
        total += valor_influencia.get(encuesta.influencia_conocimiento_extranjero, 2) * pesos['conocimiento_extranjero']
        total += valor_influencia.get(encuesta.influencia_intuicion, 2) * pesos['intuicion']
        
        # Conocimiento de materia (0-10)
        total += (encuesta.conocimiento_materia / 10) * pesos['conocimiento_materia']
        
        # Normalizar a 0-100
        encuesta.coeficiente_k = round(total * 100 / 3, 2)
        
    except:
        encuesta.coeficiente_k = 0.00
    
    return encuesta

def actualizar_estado_encuestas(request, proyecto_id):
    """Endpoint para que JavaScript pregunte el estado actual"""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    estados = EncuestaSatisfaccion.objects.filter(
        proyecto=proyecto
    ).values('experto_id', 'estado')
    
    return JsonResponse(dict(estados))

@csrf_protect
@require_POST
def finalizar_proceso_encuesta(request, proyecto_id):
    """Finaliza el proceso con protección anti-doble ejecución"""
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # ⭐ VERIFICACIÓN ANTI-DOBLE EJECUCIÓN
    if ListaChequeo.objects.filter(proyecto=proyecto, estado='seleccionado').exists():
        return JsonResponse({
            'success': False,
            'error': '⚠️ El proceso ya fue finalizado anteriormente.',
            'redirect_url': f'/proyecto/{proyecto_id}/lista-chequeo/'
        })
    
    try:
        # 1. Obtener encuestas completadas
        encuestas_completadas = EncuestaSatisfaccion.objects.filter(
            proyecto=proyecto,
            estado='completada'
        ).select_related('experto')
        
        if not encuestas_completadas.exists():
            return JsonResponse({
                'success': False,
                'error': 'No hay encuestas completadas para finalizar.'
            })
        
        # 2. Crear registros en ListaChequeo
        for encuesta in encuestas_completadas:
            ListaChequeo.objects.create(
                proyecto=proyecto,
                experto=encuesta.experto,
                estado='seleccionado',
                administrador=request.user if request.user.is_authenticated else None,
                fecha_decision=timezone.now(),
                comentarios=f'Seleccionado automáticamente. K={encuesta.coeficiente_k}',
                coeficiente_experticidad_en_decision=encuesta.coeficiente_k
            )
        
        # 3. Respuesta exitosa
        return JsonResponse({
            'success': True,
            'message': f'✅ Proceso finalizado. {encuestas_completadas.count()} expertos añadidos.',
            'redirect_url': f'/proyecto/{proyecto_id}/lista-chequeo/'
        })
        
    except Exception as e:
        # 4. Manejo de errores
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })