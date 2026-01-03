from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse, Http404
from django.contrib import messages
from ...models import Experto, Proyecto, ItemTormentaIdeas, VotoItem
import json


def votar_items(request, proyecto_id, experto_id):
    """Vista para que el experto vote items."""
    experto = get_object_or_404(Experto, id=experto_id)
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # Verificar acceso usando el modelo
    valido, error = proyecto.verificar_acceso_experto(experto)
    if not valido:
        return HttpResponseForbidden(error)
    
    # Obtener contexto completo desde el MODELO CORRECTO
    contexto = ItemTormentaIdeas.objects.get_items_votacion_context(proyecto, experto)
    
    return render(request, 'expertos/votacion.html', {
        'experto': experto,
        'proyecto': proyecto,
        **contexto
    })


@require_POST
def api_guardar_voto(request, proyecto_id, item_id):
    """API para guardar el voto de un experto."""
    try:
        data = json.loads(request.body)
        experto_id = data.get('experto_id')
        
        # Validar datos requeridos
        if not experto_id:
            return JsonResponse({
                'success': False, 
                'error': 'Experto no identificado'
            }, status=400)
        
        # Crear voto usando lógica del modelo
        success, voto, error = VotoItem.objects.crear_voto_validado(
            proyecto_id=proyecto_id,
            experto_id=experto_id,
            item_id=item_id,
            de_acuerdo=data.get('de_acuerdo', False),
            evaluacion=data.get('evaluacion')
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'voto': voto.serializar_para_respuesta(),
                'message': 'Voto registrado exitosamente'
            })
        return JsonResponse({'success': False, 'error': error}, status=400)
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Datos inválidos: {str(e)}'}, status=400)
    except Http404:
        return JsonResponse({'success': False, 'error': 'Item o proyecto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'}, status=500)