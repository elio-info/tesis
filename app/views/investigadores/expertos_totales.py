from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from ...models import Proyecto, Experto, EncuestaSatisfaccion, ListaChequeo
from ..utils.calculos import calcular_coeficiente_k

def seleccion_expertos(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    expertos = Experto.objects.con_estado_encuesta(
        proyecto, 
        orden=request.GET.get('orden', 'id')
    )
    
    if proyecto.categoria:
        expertos = expertos.filter(categoria=proyecto.categoria)
    
    return render(request, 'investigadores/expertos_totales.html', {
        'proyecto': proyecto,
        'expertos': expertos,
        'proceso_finalizado': proyecto.proceso_seleccion_finalizado(),
        'orden_actual': request.GET.get('orden', 'id')
    })

def detalle_experto(request, experto_id):
    """Vista AJAX para ver detalles del experto"""
    experto = get_object_or_404(Experto, id=experto_id)
    
    data = {
        'nombre': experto.usuario.get_full_name(),
        'email': experto.usuario.email,
        'grado': experto.get_grado_cientifico_display(),
        'cargo': experto.cargo_actual or 'No especificado',
        'departamento': experto.departamento or 'No especificado',
        'experiencia': experto.anos_experiencia,
        'coeficiente': str(experto.coeficiente_experticidad or 'N/A'),
        'indice': str(experto.indice_experticidad or 'N/A'),
        **experto.get_estadisticas(),
    }
    
    return JsonResponse(data)

def enviar_encuesta(request, proyecto_id, experto_id):
    """Vista AJAX para enviar encuesta a un experto"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    experto = get_object_or_404(Experto, id=experto_id)
    
    try:
        encuesta, created = experto.enviar_encuesta(proyecto)
        
        if not created:
            return JsonResponse({
                'error': 'El experto ya tiene una encuesta activa'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'Encuesta enviada a {experto.usuario.get_full_name()}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
