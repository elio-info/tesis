from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from ...models import Experto, Proyecto, ItemTormentaIdeas
import json


def chat_moderador(request, proyecto_id, experto_id):
    """Vista exclusiva para moderador."""
    experto = get_object_or_404(Experto, id=experto_id)
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    contexto = proyecto.get_contexto_chat_moderador(experto)
    
    if 'error' in contexto:
        if 'cerrada' in contexto['error']:
            messages.warning(request, contexto['error'])
            return redirect('app:dashboard_experto', experto_id=experto.id)
        return HttpResponseForbidden(contexto['error'])
    
    return render(request, 'expertos/chat_moderador.html', {
        'proyecto': proyecto,
        'experto': experto,
        **contexto
    })


@require_POST
def api_cerrar_tormenta(request, proyecto_id):
    """Cierra la tormenta de ideas."""
    try:
        data = json.loads(request.body)
        moderador = get_object_or_404(Experto, id=data.get('moderador_id'))
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        # Verificar acceso
        valido, error = proyecto.validar_acceso_moderador(moderador)
        if not valido:
            return JsonResponse({'success': False, 'error': error}, status=403)
        
        # Cerrar usando el modelo
        success, error = proyecto.cerrar_tormenta()
        
        if success:
            return JsonResponse({'success': True, 'message': 'Tormenta cerrada exitosamente'})
        return JsonResponse({'success': False, 'error': error}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def api_items_moderador(request, proyecto_id):
    """Crea items desde el chat del moderador."""
    try:
        data = json.loads(request.body)
        moderador = get_object_or_404(Experto, id=data.get('moderador_id'))
        
        success, item, error = ItemTormentaIdeas.objects.crear_desde_chat_moderador(
            proyecto_id, data.get('titulo'), data.get('experto_id'), moderador
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'item': {'id': item.id, 'titulo': item.titulo, **item.get_info_moderador()}
            })
        return JsonResponse({'success': False, 'error': error}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE"])
def api_eliminar_item(request, proyecto_id, item_id):
    """Elimina item."""
    try:
        moderador = get_object_or_404(Experto, id=request.GET.get('experto_id'))
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        valido, error = proyecto.validar_acceso_moderador(moderador)
        if not valido:
            return JsonResponse({'success': False, 'error': error}, status=403)
        
        success, error = ItemTormentaIdeas.objects.eliminar_por_moderador(item_id, proyecto_id, moderador)
        
        if success:
            return JsonResponse({'success': True, 'message': 'Item eliminado'})
        return JsonResponse({'success': False, 'error': error}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["PUT"])
def api_editar_item(request, proyecto_id, item_id):
    """Edita item."""
    try:
        data = json.loads(request.body)
        moderador = get_object_or_404(Experto, id=data.get('moderador_id'))
        
        success, item, error = ItemTormentaIdeas.objects.actualizar_desde_chat_moderador(
            item_id, proyecto_id, data.get('titulo'), data.get('experto_id'), moderador
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'item': {'id': item.id, 'titulo': item.titulo, **item.get_info_moderador()}
            })
        return JsonResponse({'success': False, 'error': error}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)