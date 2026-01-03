from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib import messages
from ...models import Experto, Proyecto, MensajeChat
import json


def chat_proyecto(request, proyecto_id, experto_id):
    """
    Vista del chat. Solo orquesta llamadas al modelo.
    """
    experto = get_object_or_404(Experto, id=experto_id)
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # Obtener contexto completo desde el modelo
    contexto = proyecto.get_contexto_chat(experto)
    
    # Manejar errores de acceso
    if 'error' in contexto:
        if 'cerrada' in contexto['error']:
            messages.warning(request, contexto['error'])
            return redirect('app:dashboard_experto', experto_id=experto.id)
        return HttpResponseForbidden(contexto['error'])
    
    # Seleccionar template según rol
    template = 'expertos/chat_moderador.html' if contexto['es_moderador'] else 'expertos/chat_proyecto.html'
    
    return render(request, template, {
        'proyecto': proyecto,
        'experto': experto,
        **contexto  # Expandir todo el contexto
    })


@require_POST
def enviar_mensaje_ajax(request, proyecto_id, experto_id):
    """
    Envía mensaje. Lógica delegada al modelo.
    """
    experto = get_object_or_404(Experto, id=experto_id)
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # Verificar acceso usando el modelo
    puede_chatear, error = proyecto.experto_puede_chatear(experto)
    if not puede_chatear:
        return JsonResponse({'success': False, 'error': error}, status=403)
    
    try:
        data = json.loads(request.body)
        contenido = data.get('contenido', '')
        
        # Crear mensaje usando el manager
        success, mensaje, error = MensajeChat.objects.crear_mensaje_validado(
            proyecto_id, experto, contenido
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'mensaje': mensaje.serializar_para_json(experto_id)
            })
        return JsonResponse({'success': False, 'error': error}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def obtener_mensajes_ajax(request, proyecto_id, experto_id):
    """
    Obtiene mensajes nuevos. Solo orquestación.
    """
    experto = get_object_or_404(Experto, id=experto_id)
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # Verificar acceso
    puede_chatear, error = proyecto.experto_puede_chatear(experto)
    if not puede_chatear:
        return JsonResponse({'success': False, 'error': error}, status=403)
    
    try:
        ultimo_id = int(request.GET.get('ultimo_id', 0))
        
        # Obtener mensajes usando el manager
        mensajes = MensajeChat.objects.obtener_recientes(proyecto_id, ultimo_id, 20)
        
        return JsonResponse({
            'success': True,
            'mensajes': [
                m.serializar_para_json(experto.id) for m in mensajes
            ]
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)