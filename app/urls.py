from django.urls import path
from .views.investigadores import vistas_principales, expertos_totales, seleccion_expertos, expertos_finales
from .views.expertos import dashboard, encuestas, chat, chat_moderador, votacion

app_name = 'app'

urlpatterns = [
    # Investigadores
    path('', vistas_principales.inicio_investigador, name='inicio_investigador'),
    path('proyecto/crear/', vistas_principales.crear_proyecto, name='crear_proyecto'),
    path('proyecto/<int:proyecto_id>/seleccionar-expertos/', 
        expertos_totales.seleccion_expertos, name='expertos_totales'),
    path('proyecto/<int:proyecto_id>/encuesta/', 
        seleccion_expertos.encuesta_satisfaccion, name='seleccion_expertos'),
    path('proyecto/<int:proyecto_id>/lista-chequeo/', 
        expertos_finales.lista_chequeo, name='expertos_finales'),
    path('proyecto/<int:proyecto_id>/encuesta/<int:encuesta_id>/eliminar/',
        seleccion_expertos.eliminar_experto_encuesta, name='eliminar_experto_encuesta'),
    
    # Expertos
    path('expertos/<int:experto_id>/', 
        dashboard.dashboard_experto, name='dashboard_experto'),
    path('expertos/<int:experto_id>/encuesta/<int:encuesta_id>/', 
        encuestas.completar_encuesta, name='completar_encuesta'),
    
    # Encuestas Ajax
    path('ajax/experto/<int:experto_id>/detalles/', 
        expertos_totales.detalle_experto, name='detalle_experto'),
    path('ajax/proyecto/<int:proyecto_id>/finalizar-proceso/', 
        expertos_finales.finalizar_proceso_encuesta, name='finalizar_proceso_encuesta'),
    path('ajax/proyecto/<int:proyecto_id>/enviar-encuesta/<int:experto_id>/', 
        expertos_totales.enviar_encuesta, name='enviar_encuesta'),
    
    path('ajax/expertos/<int:experto_id>/encuesta/<int:encuesta_id>/guardar/', 
        encuestas.guardar_encuesta_ajax, name='guardar_encuesta_ajax'),
    
    # Rutas para chat
    path('proyecto/<int:proyecto_id>/chat/<int:experto_id>/', 
         chat.chat_proyecto, name='chat_proyecto'),
    path('proyecto/<int:proyecto_id>/chat/<int:experto_id>/moderador/', 
         chat_moderador.chat_moderador, name='chat_moderador'),
    
    path('ajax/proyecto/<int:proyecto_id>/chat/<int:experto_id>/mensajes/', 
         chat.obtener_mensajes_ajax, name='obtener_mensajes_ajax'),
    path('ajax/proyecto/<int:proyecto_id>/chat/<int:experto_id>/enviar/', 
         chat.enviar_mensaje_ajax, name='enviar_mensaje_ajax'),
    
    path('api/proyecto/<int:proyecto_id>/items/', 
        chat_moderador.api_items_moderador, name='api_items_moderador'),
    path('api/proyecto/<int:proyecto_id>/items/<int:item_id>/', 
        chat_moderador.api_eliminar_item, name='api_eliminar_item'),
    path('api/proyecto/<int:proyecto_id>/items/<int:item_id>/editar/', 
        chat_moderador.api_editar_item, name='api_editar_item'),
    path('api/proyecto/<int:proyecto_id>/cerrar-tormenta/', 
        chat_moderador.api_cerrar_tormenta, name='api_cerrar_tormenta'),
    
    # Rutas para votaciones
    path('proyecto/<int:proyecto_id>/votar/<int:experto_id>/', 
         votacion.votar_items, name='votar_items'),
    path('api/proyecto/<int:proyecto_id>/item/<int:item_id>/votar/', 
         votacion.api_guardar_voto, name='api_guardar_voto'),
]