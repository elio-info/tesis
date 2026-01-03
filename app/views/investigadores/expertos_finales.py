from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from ...models import Proyecto

def lista_chequeo(request, proyecto_id):
    """Vista de lista de chequeo con moderador destacado"""
    proyecto = get_object_or_404(
        Proyecto.objects.select_related('investigador'), 
        id=proyecto_id
    )
    
    return render(request, 'investigadores/expertos_finales.html', {
        'proyecto': proyecto,
        'expertos_finales': proyecto.get_expertos_seleccionados(),
        'moderador': proyecto.moderador,
        'proceso_finalizado': proyecto.proceso_seleccion_finalizado(),
    })

@require_POST
def finalizar_proceso_encuesta(request, proyecto_id):
    """Finaliza el proceso de selección de expertos"""
    try:
        data = json.loads(request.body)
        moderador_id = data.get('moderador_id')
        
        if not moderador_id:
            return JsonResponse({
                'success': False,
                'error': '❌ Debes seleccionar un moderador.'
            }, status=400)
        
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        # Obtener usuario administrador
        admin_user = request.user if request.user.is_authenticated else None
        if not admin_user:
            from django.contrib.auth.models import User
            admin_user = User.objects.filter(is_superuser=True).first()
        
        # Ejecutar toda la lógica en el modelo
        resultado = proyecto.finalizar_seleccion_expertos(moderador_id, admin_user)
        
        if resultado['success']:
            return JsonResponse({
                'success': True,
                'message': f'✅ {resultado["message"]}',
                'redirect_url': f'/proyecto/{proyecto_id}/lista-chequeo/'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'❌ {resultado["error"]}'
            }, status=400)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=500)