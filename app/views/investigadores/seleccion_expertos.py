from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from ...models import Proyecto, Experto, EncuestaSatisfaccion

def encuesta_satisfaccion(request, proyecto_id):
    """Vista principal de encuestas de satisfacción"""
    proyecto = get_object_or_404(
        Proyecto.objects.select_related('investigador'), 
        id=proyecto_id
    )
    
    stats = proyecto.get_encuestas_stats()
    
    return render(request, 'investigadores/seleccion_expertos.html', {
        'proyecto': proyecto,
        'encuestas': stats['todas'],
        'encuestas_completadas': stats['completadas'],
        'proceso_finalizado': proyecto.proceso_seleccion_finalizado(),
        'total_completadas': stats['total_completadas'],
        'moderador_actual_id': proyecto.moderador_id,
    })

def actualizar_estado_encuestas(request, proyecto_id):
    """Endpoint para actualización vía AJAX"""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    return JsonResponse(proyecto.get_estados_encuestas_dict())

@require_http_methods(["POST", "DELETE"])
def eliminar_experto_encuesta(request, proyecto_id, encuesta_id):
    encuesta = get_object_or_404(
        EncuestaSatisfaccion.objects.select_related('experto'), 
        id=encuesta_id,
        proyecto_id=proyecto_id
    )
    
    experto_nombre = encuesta.experto.usuario.get_full_name()
    encuesta.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Experto {experto_nombre} eliminado correctamente',
            'encuesta_id': encuesta_id
        })
    
    return redirect('app:seleccion_expertos', proyecto_id=proyecto_id)