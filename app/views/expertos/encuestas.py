from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from ...models import Experto, EncuestaSatisfaccion
from ..utils.calculos import calcular_coeficiente_k

def completar_encuesta(request, experto_id, encuesta_id):
    experto = get_object_or_404(Experto, id=experto_id)
    encuesta = EncuestaSatisfaccion.objects.get_by_experto(encuesta_id, experto_id)
    
    puede_editar, mensaje_error = encuesta.puede_ser_editada()
    if not puede_editar:
        messages.warning(request, mensaje_error)
        return redirect('app:dashboard_experto', experto_id=experto_id)
    
    # Definir los campos de influencia con sus labels
    encuesta_influencias = [
        ('influencia_analisis_teoricos', 'Análisis teóricos realizados por usted'),
        ('influencia_experiencia', 'Su experiencia obtenida'),
        ('influencia_autores_nacionales', 'Trabajos de autores nacionales'),
        ('influencia_autores_extranjeros', 'Trabajos de autores extranjeros'),
        ('influencia_conocimiento_extranjero', 'Su propio conocimiento del estado del problema en el extranjero'),
        ('influencia_intuicion', 'Su intuición'),
    ]
    
    if request.method == 'POST':
        exito, error = encuesta.procesar_respuestas(request.POST, calcular_coeficiente_k)
        if exito:
            messages.success(request, '¡Encuesta completada exitosamente!')
            return redirect('app:dashboard_experto', experto_id=experto_id)
        else:
            messages.error(request, f'Error al guardar la encuesta: {error}')
    
    return render(request, 'expertos/completar_encuesta.html', {
        'encuesta': encuesta,
        'experto': experto,
        'encuesta_influencias': encuesta_influencias,
        'INFLUENCIA_CHOICES': EncuestaSatisfaccion.INFLUENCIA_CHOICES
    })


@require_POST
def guardar_encuesta_ajax(request, experto_id, encuesta_id):
    """
    Procesa la encuesta vía AJAX y devuelve JSON.
    """
    try:
        # Obtener objetos con verificación automática de permisos
        encuesta = EncuestaSatisfaccion.objects.get_by_experto(encuesta_id, experto_id)
        
        # Verificar si se puede editar
        puede_editar, error = encuesta.puede_ser_editada()
        if not puede_editar:
            return JsonResponse({'success': False, 'error': error}, status=403)
        
        # Procesar usando lógica del modelo
        exito, error = encuesta.procesar_respuestas(request.POST, calcular_coeficiente_k)
        
        if exito:
            return JsonResponse({
                'success': True,
                'message': 'Encuesta completada.',
                'redirect_url': reverse('app:dashboard_experto', args=[experto_id])
            })
        else:
            return JsonResponse({'success': False, 'error': error}, status=500)
            
    except Http404 as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'}, status=500)
