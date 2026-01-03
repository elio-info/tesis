from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class ProyectoManager(models.Manager):
    def con_estadisticas(self):
        """Devuelve proyectos con estadísticas de expertos seleccionados"""
        return self.get_queryset().select_related('investigador').annotate(
            total_expertos_seleccionados=models.Count(
                'lista_chequeo_expertos',
                filter=models.Q(lista_chequeo_expertos__estado='seleccionado')
            )
        )

class ExpertoManager(models.Manager):
    def ordenados_por(self, criterio='id'):
        """Ordena expertos según diferentes criterios"""
        queryset = self.get_queryset().select_related('usuario')
        
        orden_map = {
            'nombre': ('usuario__first_name', 'usuario__last_name'),
            'coeficiente': ('-coeficiente_experticidad',),
            'grado': ('grado_cientifico',),
            'experiencia': ('-anos_experiencia',),
        }
        
        return queryset.order_by(*orden_map.get(criterio, ('id',)))
    
    def con_estado_encuesta(self, proyecto, orden='id'):
        """
        Devuelve expertos con estado_encuesta y ordenamiento aplicado
        """
        from django.db.models import Case, When, CharField
        
        queryset = self.get_queryset().select_related('usuario').annotate(
            estado_encuesta=Case(
                When(
                    encuestas_experticidad__proyecto=proyecto,
                    then='encuestas_experticidad__estado'
                ),
                default=None,
                output_field=CharField()
            )
        )
        
        # Aplicar ordenamiento
        orden_map = {
            'nombre': ['usuario__first_name', 'usuario__last_name'],
            'coeficiente': ['-coeficiente_experticidad'],
            'grado': ['grado_cientifico'],
            'experiencia': ['-anos_experiencia'],
        }
        return queryset.order_by(*orden_map.get(orden, ['id']))

class EncuestaSatisfaccionManager(models.Manager):
    def por_proyecto(self, proyecto):
        """Obtiene todas las encuestas de un proyecto con datos relacionados"""
        return self.filter(proyecto=proyecto).select_related('experto__usuario')
    
    def completadas(self, proyecto=None):
        """Filtra encuestas completadas, opcionalmente por proyecto"""
        qs = self.filter(estado='completada')
        if proyecto:
            qs = qs.filter(proyecto=proyecto)
        return qs
    
    def get_by_experto(self, encuesta_id, experto_id):
        """
        Obtiene una encuesta verificando que pertenezca al experto.
        Raises: Http404 si no existe o no pertenece al experto
        """
        try:
            return self.select_related('proyecto').get(
                id=encuesta_id, 
                experto_id=experto_id
            )
        except self.model.DoesNotExist:
            from django.http import Http404
            raise Http404("Encuesta no encontrada o no tienes permiso para acceder a ella.")
    
    def get_dashboard_encuestas(self, experto, proyectos_cerrados):
        """
        Obtiene encuestas organizadas para el dashboard.
        Returns: dict con listas separadas y contadores
        """
        pendientes = self.filter(
            experto=experto, estado='pendiente'
        ).select_related('proyecto')
        
        no_bloqueadas = []
        bloqueadas = []
        
        for encuesta in pendientes:
            if encuesta.proyecto_id in proyectos_cerrados:
                encuesta.bloqueada = True
                bloqueadas.append(encuesta)
            else:
                encuesta.bloqueada = False
                no_bloqueadas.append(encuesta)
        
        completadas = self.filter(
            experto=experto, estado='completada'
        ).select_related('proyecto').order_by('-fecha_respuesta')
        
        return {
            'pendientes_no_bloqueadas': no_bloqueadas,
            'pendientes_bloqueadas': bloqueadas,
            'completadas': completadas,
            'total_pendientes_no_bloqueadas': len(no_bloqueadas)
        }

class ListaChequeoManager(models.Manager):
    def crear_desde_encuesta(self, encuesta, admin_user):
        """Crea o actualiza registro desde encuesta completada"""
        return self.update_or_create(
            proyecto=encuesta.proyecto,
            experto=encuesta.experto,
            defaults={
                'estado': 'seleccionado',
                'administrador': admin_user,
                'fecha_decision': timezone.now(),
                'comentarios': f'Seleccionado. K={encuesta.coeficiente_k}',
                'coeficiente_experticidad_en_decision': encuesta.coeficiente_k,
                'es_moderador': False
            }
        )
    
    def asignar_moderador(self, proyecto, experto, admin_user):
        """Asigna un experto como moderador"""
        return self.update_or_create(
            proyecto=proyecto,
            experto=experto,
            defaults={
                'estado': 'seleccionado',
                'administrador': admin_user,
                'fecha_decision': timezone.now(),
                'comentarios': 'Moderador del proyecto',
                'coeficiente_experticidad_en_decision': 0,
                'es_moderador': True
            }
        )
    
    def get_dashboard_chats(self, experto):
        """
        Obtiene chats disponibles del experto con toda la metadata necesaria.
        Returns: dict con chats_activos, chats_cerrados, tormentas_activas_count
        """
        chats = self.filter(
            experto=experto, estado='seleccionado'
        ).select_related('proyecto', 'proyecto__investigador').order_by('-fecha_decision')
        
        # Separar en activos y cerrados
        chats_activos = [c for c in chats if c.proyecto.estado_tormenta == 'activa']
        chats_cerrados = [c for c in chats if c.proyecto.estado_tormenta == 'cerrada']
        
        # Contar tormentas activas (solo en cerrados según lógica original)
        tormentas_activas_count = sum(
            1 for c in chats_cerrados if c.proyecto.estado_tormenta == 'activa'
        )
        
        return {
            'todos': chats,
            'activos': chats_activos,
            'cerrados': chats_cerrados,
            'tormentas_activas_count': tormentas_activas_count
        }

class MensajeChatManager(models.Manager):
    def crear_mensaje_validado(self, proyecto_id, experto, contenido):
        """
        Crea un mensaje con validaciones de negocio.
        Returns: tuple (success: bool, mensaje: MensajeChat|None, error: str)
        """
        contenido_limpio = contenido.strip()
        
        if not contenido_limpio:
            return False, None, 'Mensaje vacío'
        
        if len(contenido_limpio) > 1000:
            return False, None, 'Máximo 1000 caracteres permitidos'
        
        try:
            mensaje = self.create(
                proyecto_id=proyecto_id,
                experto=experto,
                contenido=contenido_limpio
            )
            return True, mensaje, None
        except Exception as e:
            return False, None, str(e)
    
    def obtener_recientes(self, proyecto_id, desde_id=0, limite=50):
        """
        Obtiene mensajes recientes para un proyecto.
        Returns: QuerySet de mensajes
        """
        return self.filter(
            proyecto_id=proyecto_id,
            id__gt=desde_id
        ).select_related('experto__usuario').order_by('fecha_envio')[:limite]

class ItemTormentaIdeasManager(models.Manager):
    def crear_desde_chat_moderador(self, proyecto_id, titulo, experto_id, moderador):
        """
        Crea item con validaciones de moderador.
        Returns: tuple (success: bool, item: ItemTormentaIdeas|None, error: str)
        """
        titulo_limpio = titulo.strip()
        if not titulo_limpio:
            return False, None, 'Título vacío'
        
        if not experto_id:
            return False, None, 'Debes asignar un experto'
        
        # Verificar moderador y experto
        lista_mod = ListaChequeo.objects.filter(
            proyecto_id=proyecto_id, experto=moderador, 
            es_moderador=True, estado='seleccionado'
        ).first()
        
        if not lista_mod:
            return False, None, 'No eres moderador del proyecto'
        
        if not ListaChequeo.objects.filter(
            proyecto_id=proyecto_id, experto_id=experto_id, estado='seleccionado'
        ).exists():
            return False, None, 'El experto no pertenece al proyecto'
        
        try:
            item = self.create(
                titulo=titulo_limpio,
                descripcion='Item seleccionado desde chat moderador',
                proyecto_id=proyecto_id,
                experto_id=experto_id,
                experto_propietario_id=experto_id,
                estado='seleccionado'
            )
            return True, item, None
        except Exception as e:
            return False, None, str(e)
    
    def eliminar_por_moderador(self, item_id, proyecto_id, moderador):
        """Elimina item verificando permisos. Returns: tuple (success: bool, error: str)"""
        if not ListaChequeo.objects.filter(
            proyecto_id=proyecto_id, experto=moderador,
            es_moderador=True, estado='seleccionado'
        ).exists():
            return False, 'No eres moderador del proyecto'
        
        try:
            item = self.get(id=item_id, proyecto_id=proyecto_id)
            item.delete()
            return True, None
        except self.model.DoesNotExist:
            return False, 'Item no encontrado'
        except Exception as e:
            return False, str(e)
    
    def actualizar_desde_chat_moderador(self, item_id, proyecto_id, titulo, experto_id, moderador):
        """Actualiza item con validaciones. Returns: tuple (success: bool, item: ItemTormentaIdeas|None, error: str)"""
        titulo_limpio = titulo.strip()
        if not titulo_limpio:
            return False, None, 'Título vacío'
        
        if not experto_id:
            return False, None, 'Debes asignar un experto'
        
        if not ListaChequeo.objects.filter(
            proyecto_id=proyecto_id, experto=moderador,
            es_moderador=True, estado='seleccionado'
        ).exists():
            return False, None, 'No eres moderador del proyecto'
        
        if not ListaChequeo.objects.filter(
            proyecto_id=proyecto_id, experto_id=experto_id, estado='seleccionado'
        ).exists():
            return False, None, 'El experto no pertenece al proyecto'
        
        try:
            item = self.get(id=item_id, proyecto_id=proyecto_id)
            item.titulo = titulo_limpio
            item.experto_id = experto_id
            item.experto_propietario_id = experto_id
            item.save()
            return True, item, None
        except self.model.DoesNotExist:
            return False, None, 'Item no encontrado'
        except Exception as e:
            return False, None, str(e)
    
    def get_items_votacion_context(self, proyecto, experto):
        """
        Obtiene todos los datos necesarios para la vista de votación.
        Returns: dict con items y estadísticas
        """
        # Items por votar (no votados por este experto)
        items_por_votar = self.filter(
            proyecto=proyecto,
            estado='seleccionado'
        ).exclude(
            votos_recibidos__experto=experto
        ).select_related('experto').order_by('-fecha_creacion')
        
        # Items ya votados
        items_votados = self.filter(
            proyecto=proyecto,
            estado='seleccionado',
            votos_recibidos__experto=experto
        ).select_related('experto').order_by('-fecha_creacion')
        
        # Contadores
        total_items = self.filter(proyecto=proyecto, estado='seleccionado').count()
        votados_por_experto = VotoItem.objects.filter(
            experto=experto, proyecto=proyecto
        ).count()
        
        return {
            'items_por_votar': items_por_votar,
            'items_votados': items_votados,
            'total_items': total_items,
            'votados_por_experto': votados_por_experto,
            'pendientes': total_items - votados_por_experto
        }
    
    def get_dashboard_votaciones_pendientes(self, experto, chats_cerrados):
        """
        Obtiene votaciones pendientes para el dashboard.
        Returns: list de dicts con proyecto, cantidad_items, moderador
        """
        votaciones_pendientes = []
        
        for chat in chats_cerrados:
            proyecto = chat.proyecto
            
            # Usar ORM eficiente en lugar de exists() + count()
            items_sin_votar = proyecto.items_ideados.filter(
                estado='seleccionado'
            ).exclude(
                votos_recibidos__experto=experto
            )
            
            count = items_sin_votar.count()
            if count > 0:
                votaciones_pendientes.append({
                    'proyecto': proyecto,
                    'cantidad_items': count,
                    'moderador': proyecto.moderador.usuario.get_full_name() if proyecto.moderador else 'N/A'
                })
        
        return votaciones_pendientes

class VotoItemManager(models.Manager):
    def crear_voto_validado(self, proyecto_id, experto_id, item_id, de_acuerdo, evaluacion):
        """
        Crea un voto con todas las validaciones de negocio.
        Returns: tuple (success: bool, voto: VotoItem|None, error: str)
        """
        # Verificar que el experto pertenece al proyecto
        if not ListaChequeo.objects.filter(
            proyecto_id=proyecto_id,
            experto_id=experto_id,
            estado='seleccionado'
        ).exists():
            return False, None, 'No perteneces a este proyecto'
        
        # Verificar si ya votó
        if self.filter(experto_id=experto_id, item_id=item_id).exists():
            return False, None, 'Ya has votado este item'
        
        try:
            voto = self.create(
                experto_id=experto_id,
                item_id=item_id,
                proyecto_id=proyecto_id,
                de_acuerdo=bool(de_acuerdo),
                evaluacion=int(evaluacion) if evaluacion else None
            )
            return True, voto, None
        except Exception as e:
            return False, None, str(e)
    



class Proyecto(models.Model):
    ESTADO_TORMENTA = [
        ('activa', 'Tormenta de Ideas Activa'),
        ('cerrada', 'Tormenta de Ideas Cerrada'),
    ]
    
    nombre = models.CharField(max_length=255)
    investigador = models.ForeignKey(
        'Experto', 
        on_delete=models.CASCADE, 
        related_name='proyectos_liderados',
        null=True,
        blank=True
    )
    empresa_cliente = models.CharField(max_length=255)
    estado_tormenta = models.CharField(
        max_length=10,
        choices=ESTADO_TORMENTA,
        default='activa',
        verbose_name="Estado de la tormenta de ideas"
    )
    fecha_cierre_tormenta = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de cierre de tormenta"
    )
    
    objects = ProyectoManager()
    
    @property
    def moderador(self):
        """Devuelve el experto moderador del proyecto"""
        try:
            return ListaChequeo.objects.get(
                proyecto=self, 
                es_moderador=True
            ).experto
        except ListaChequeo.DoesNotExist:
            return None
    
    @property
    def moderador_id(self):
        """Devuelve el ID del moderador o None"""
        return self.lista_chequeo_expertos.filter(
            es_moderador=True
        ).values_list('experto_id', flat=True).first()
    
    def proceso_seleccion_finalizado(self):
        """Verifica si el proceso de selección está completo"""
        return self.lista_chequeo_expertos.filter(
            estado='seleccionado'
        ).exists()
    
    def get_encuestas_stats(self):
        """Devuelve estadísticas agregadas de encuestas"""
        encuestas = self.encuestas_experticidad.select_related('experto__usuario')
        completadas = encuestas.filter(estado='completada')
        
        return {
            'todas': encuestas,
            'completadas': completadas,
            'total_completadas': completadas.count(),
        }
    
    def get_estados_encuestas_dict(self):
        """Devuelve dict {experto_id: estado} para AJAX"""
        return dict(
            self.encuestas_experticidad.values_list('experto_id', 'estado')
        )
    
    def get_expertos_seleccionados(self):
        """Obtiene todos los expertos seleccionados con sus datos relacionados"""
        return self.lista_chequeo_expertos.filter(
            estado='seleccionado'
        ).select_related('experto__usuario')
    
    def remover_moderador_actual(self):
        """Remueve el moderador actual del proyecto"""
        self.lista_chequeo_expertos.filter(
            es_moderador=True
        ).update(es_moderador=False)
    
    def finalizar_seleccion_expertos(self, moderador_id, admin_user):
        """
        Finaliza el proceso de selección:
        - Valida encuestas completadas
        - Remueve moderador anterior
        - Crea/actualiza expertos desde encuestas
        - Asigna nuevo moderador
        
        Returns: dict con resultado
        """
        from django.db import transaction
        
        # Validar encuestas completadas
        encuestas_completadas = EncuestaSatisfaccion.objects.filter(
            proyecto=self,
            estado='completada'
        ).select_related('experto')
        
        if not encuestas_completadas.exists():
            return {
                'success': False,
                'error': 'No hay encuestas completadas.'
            }
        
        try:
            with transaction.atomic():
                # 1. Remover moderador anterior
                self.remover_moderador_actual()
                
                # 2. Crear/actualizar registros para cada encuesta
                for encuesta in encuestas_completadas:
                    ListaChequeo.objects.crear_desde_encuesta(encuesta, admin_user)
                
                # 3. Asignar moderador
                experto_mod = Experto.objects.get(id=moderador_id)
                ListaChequeo.objects.asignar_moderador(self, experto_mod, admin_user)
            
            return {
                'success': True,
                'message': f'Proceso finalizado con {encuestas_completadas.count()} expertos.',
                'count': encuestas_completadas.count()
            }
            
        except Experto.DoesNotExist:
            return {
                'success': False,
                'error': 'El moderador seleccionado no existe.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def experto_puede_chatear(self, experto):
        """
        Verifica si un experto tiene acceso al chat.
        Returns: tuple (puede: bool, error_msg: str|None)
        """
        if self.estado_tormenta == 'cerrada':
            return False, 'La tormenta de ideas para este proyecto está cerrada.'
        
        if not self.lista_chequeo_expertos.filter(
            experto=experto,
            estado='seleccionado'
        ).exists():
            return False, 'No tienes acceso al chat de este proyecto.'
        
        return True, None
    
    def es_moderador(self, experto):
        """Verifica si el experto es moderador del proyecto"""
        return self.lista_chequeo_expertos.filter(
            experto=experto,
            es_moderador=True
        ).exists()
    
    def get_contexto_chat(self, experto):
        """
        Obtiene todo el contexto necesario para la vista de chat.
        Returns: dict con toda la información del chat
        """
        puede_chatear, error = self.experto_puede_chatear(experto)
        
        if not puede_chatear:
            return {'error': error}
        
        es_mod = self.es_moderador(experto)
        
        contexto = {
            'puede_acceder': True,
            'es_moderador': es_mod,
            'mensajes': self.mensajes_chat.select_related('experto__usuario').order_by('fecha_envio')[:50],
            'total_expertos': self.lista_chequeo_expertos.filter(estado='seleccionado').count(),
            'items_seleccionados': []
        }
        
        # Si es moderador, agregar items seleccionados
        if es_mod:
            contexto['items_seleccionados'] = self.items_ideados.filter(
                experto=experto,
                estado='seleccionado'
            ).order_by('-fecha_creacion')
        
        return contexto
    
    def validar_acceso_moderador(self, experto):
        """Verifica acceso de moderador. Returns: tuple (valido: bool, error: str|None)"""
        if self.estado_tormenta == 'cerrada':
            return False, 'La tormenta de ideas para este proyecto está cerrada.'
        
        if not ListaChequeo.objects.filter(
            proyecto=self, experto=experto, es_moderador=True, estado='seleccionado'
        ).exists():
            return False, 'Acceso exclusivo para moderador.'
        
        return True, None
    
    def cerrar_tormenta(self):
        """Cierra la tormenta. Returns: tuple (success: bool, error: str|None)"""
        if self.estado_tormenta == 'cerrada':
            return False, 'La tormenta ya está cerrada'
        
        try:
            self.estado_tormenta = 'cerrada'
            self.save(update_fields=['estado_tormenta'])
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_contexto_chat_moderador(self, experto):
        """Obtiene contexto completo para la vista. Returns: dict"""
        valido, error = self.validar_acceso_moderador(experto)
        if not valido:
            return {'error': error}
        
        return {
            'puede_acceder': True,
            'mensajes': self.mensajes_chat.select_related('experto__usuario').order_by('fecha_envio')[:50],
            'items_seleccionados': self.items_ideados.filter(
                estado='seleccionado'
            ).select_related('experto__usuario').order_by('-fecha_creacion'),
            'expertos_proyecto': self.get_expertos_seleccionados_list(),
            'total_expertos': self.lista_chequeo_expertos.filter(
                estado='seleccionado'
            ).count()
        }
    
    def get_expertos_seleccionados_list(self):
        """Retorna lista de objetos Experto seleccionados."""
        listas = self.lista_chequeo_expertos.filter(
            estado='seleccionado'
        ).select_related('experto__usuario')
        return [lista.experto for lista in listas]
    
    def verificar_acceso_experto(self, experto):
        """Verifica si el experto tiene acceso. Returns: tuple (valido: bool, error: str|None)"""
        if not self.lista_chequeo_expertos.filter(
            experto=experto, estado='seleccionado'
        ).exists():
            return False, 'No perteneces a este proyecto.'
        return True, None
    
    def __str__(self):
        return self.nombre

class Experto(models.Model):
    GRADO_CIENTIFICO_CHOICES = [
        ('Doctor', 'Doctor'),
        ('Master', 'Máster'),
        ('Licenciado', 'Licenciado'),
        ('Técnico', 'Técnico Superior'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    coeficiente_experticidad = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    indice_experticidad = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    cargo_actual = models.CharField(max_length=255, blank=True, null=True)
    departamento = models.CharField(max_length=255, blank=True, null=True)
    grado_cientifico = models.CharField(max_length=20, choices=GRADO_CIENTIFICO_CHOICES)
    anos_experiencia = models.IntegerField(default=0)
    
    objects = ExpertoManager()
    
    def get_estadisticas(self):
        """Devuelve estadísticas completas del experto"""
        from django.db.models import Q
        
        encuestas = self.encuestas_experticidad.all()
        aportes = self.items_generados.all()
        
        return {
            'total_encuestas': encuestas.count(),
            'total_aportes': aportes.count(),
            'proyectos_activos': aportes.filter(
                Q(estado='pendiente') | Q(estado='seleccionado')
            ).count(),
        }
    
    def enviar_encuesta(self, proyecto):
        """Crea y envía encuesta de satisfacción para un proyecto"""
        if hasattr(self, 'encuesta_cache'):
            return self.encuesta_cache
            
        encuesta, created = EncuestaSatisfaccion.objects.get_or_create(
            proyecto=proyecto,
            experto=self,
            defaults={
                'cargo_actual': self.cargo_actual or '',
                'anos_experiencia': self.anos_experiencia,
                'grado_cientifico': self.grado_cientifico
            }
        )
        self.encuesta_cache = encuesta
        return encuesta, created
    
    def get_dashboard_data(self):
        """
        Método central que obtiene TODA la data del dashboard.
        Returns: dict completo para la vista
        """
        from .models import ListaChequeo, EncuestaSatisfaccion, VotoItem
        
        # 1. Proyectos cerrados (para lógica de bloqueo)
        proyectos_cerrados = set(
            ListaChequeo.objects.filter(estado='seleccionado')
            .values_list('proyecto_id', flat=True)
        )
        
        # 2. Chats y sus contadores
        chats_data = ListaChequeo.objects.get_dashboard_chats(self)
        
        # 3. Encuestas organizadas
        encuestas_data = EncuestaSatisfaccion.objects.get_dashboard_encuestas(
            self, proyectos_cerrados
        )
        
        # 4. Votaciones pendientes
        votaciones_pendientes = ItemTormentaIdeas.objects.get_dashboard_votaciones_pendientes(
            self, chats_data['cerrados']
        )
        
        return {
            'chats_disponibles': chats_data['todos'],
            'chats_activos': chats_data['activos'],
            'chats_cerrados': chats_data['cerrados'],
            'tormentas_activas_count': chats_data['tormentas_activas_count'],
            'votaciones_pendientes': votaciones_pendientes,
            'total_votaciones_pendientes': len(votaciones_pendientes),
            'pendientes_no_bloqueadas': encuestas_data['pendientes_no_bloqueadas'],
            'encuestas_completadas': encuestas_data['completadas'],
            'pendientes_bloqueadas': encuestas_data['pendientes_bloqueadas'],
            'encuestas_pendientes_no_bloqueadas': encuestas_data['total_pendientes_no_bloqueadas'],
        }
    
    def __str__(self):
        return self.usuario.get_full_name()

class EncuestaSatisfaccion(models.Model):
    INFLUENCIA_CHOICES = [
        ('A', 'Alto'),
        ('M', 'Medio'),
        ('B', 'Bajo'),
    ]
    ESTADO_ENCAPSULA = [
        ('pendiente', 'Pendiente de Completar'),
        ('completada', 'Completada por Experto'),
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
    ]
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_ENCAPSULA,
        default='pendiente'
    )
    proyecto = models.ForeignKey(
        'Proyecto', 
        on_delete=models.CASCADE, 
        related_name='encuestas_experticidad'
    )
    experto = models.ForeignKey(
        'Experto', 
        on_delete=models.CASCADE, 
        related_name='encuestas_experticidad'
    )
    cargo_actual = models.CharField(max_length=255)
    anos_experiencia = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Años de experiencia en el cargo"
    )
    grado_cientifico = models.CharField(max_length=20)
    conocimiento_materia = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Valor del 0 al 10 sobre el grado de conocimientos en la materia",
        null=True,
        blank=True
    )
    influencia_analisis_teoricos = models.CharField(
        max_length=1, 
        choices=INFLUENCIA_CHOICES,
        verbose_name="Análisis teóricos realizados por usted"
    )
    influencia_experiencia = models.CharField(
        max_length=1, 
        choices=INFLUENCIA_CHOICES,
        verbose_name="Su experiencia obtenida"
    )
    influencia_autores_nacionales = models.CharField(
        max_length=1, 
        choices=INFLUENCIA_CHOICES,
        verbose_name="Trabajos de autores nacionales"
    )
    influencia_autores_extranjeros = models.CharField(
        max_length=1, 
        choices=INFLUENCIA_CHOICES,
        verbose_name="Trabajos de autores extranjeros"
    )
    influencia_conocimiento_extranjero = models.CharField(
        max_length=1, 
        choices=INFLUENCIA_CHOICES,
        verbose_name="Su propio conocimiento del estado del problema en el extranjero"
    )
    influencia_intuicion = models.CharField(
        max_length=1, 
        choices=INFLUENCIA_CHOICES,
        verbose_name="Su intuición"
    )
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    coeficiente_k = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Coeficiente de experticidad calculado"
    )

    class Meta:
        unique_together = ['proyecto', 'experto']
        verbose_name = "Encuesta de Experticidad"
        verbose_name_plural = "Encuestas de Experticidad"
    
    objects = EncuestaSatisfaccionManager()
    
    def get_absolute_url(self):
        """URL para acceder a la encuesta individual"""
        from django.urls import reverse
        return reverse('encuesta_detail', args=[self.proyecto.id, self.id])
    
    def puede_ser_editada(self):
        """
        Verifica si la encuesta puede ser editada por el experto.
        Returns: tuple (puede_editar: bool, mensaje_error: str)
        """
        if self.estado != 'pendiente':
            return False, 'Esta encuesta ya ha sido completada.'
        
        # Verificar si la selección de expertos está finalizada
        if self.proyecto.proceso_seleccion_finalizado():
            return False, 'El proceso de selección de expertos ha finalizado.'
        
        return True, None
    
    def procesar_respuestas(self, data, calculadora_k=None):
        """
        Procesa los datos de la encuesta desde request.POST.
        
        Args:
            data: Diccionario con los datos del formulario (request.POST)
            calculadora_k: Callable para calcular el coeficiente K (ej: calcular_coeficiente_k)
        
        Returns:
            tuple (exito: bool, error: str)
        """
        try:
            # Actualizar campos con valores del formulario
            self.cargo_actual = data.get('cargo_actual', '')
            self.anos_experiencia = int(data.get('anos_experiencia', 0))
            self.grado_cientifico = data.get('grado_cientifico', '') or self.grado_cientifico
            self.conocimiento_materia = int(data.get('conocimiento_materia', 5))
            
            # Influencias - defaults a 'M' (Medio)
            influencias = [
                'influencia_analisis_teoricos',
                'influencia_experiencia',
                'influencia_autores_nacionales',
                'influencia_autores_extranjeros',
                'influencia_conocimiento_extranjero',
                'influencia_intuicion',
            ]
            for campo in influencias:
                setattr(self, campo, data.get(campo, 'M'))
            
            # Calcular coeficiente K si se proporciona calculadora
            if calculadora_k:
                self = calculadora_k(self)
            
            self.estado = 'completada'
            self.save()
            
            return True, None
            
        except (ValueError, TypeError) as e:
            return False, f'Error en los datos: {str(e)}'
        except Exception as e:
            return False, str(e)

    def __str__(self):
        return f"Encuesta {self.experto} - {self.proyecto} ({self.fecha_respuesta.date()})"

class ListaChequeo(models.Model):
    ESTADO_SELECCION = [
        ('pendiente', 'Pendiente de Revisión'),
        ('seleccionado', 'Seleccionado para el Proyecto'),
        ('rechazado', 'No Seleccionado'),
    ]
    
    proyecto = models.ForeignKey(
        'Proyecto',
        on_delete=models.CASCADE,
        related_name='lista_chequeo_expertos'
    )
    experto = models.ForeignKey(
        'Experto',
        on_delete=models.CASCADE,
        related_name='selecciones_proyectos'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_SELECCION,
        default='pendiente'
    )
    administrador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selecciones_expertos'
    )
    es_moderador = models.BooleanField(
        default=False,
        verbose_name="¿Es moderador del proyecto?"
    )
    fecha_decision = models.DateTimeField(null=True, blank=True)
    comentarios = models.TextField(blank=True, null=True)
    coeficiente_experticidad_en_decision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    objects = ListaChequeoManager()

    class Meta:
        unique_together = ['proyecto', 'experto']
        verbose_name = "Lista de Chequeo de Experto"
        verbose_name_plural = "Listas de Chequeo de Expertos"
        ordering = ['proyecto', '-coeficiente_experticidad_en_decision']

    def __str__(self):
        return f"{self.experto} - {self.proyecto} ({self.get_estado_display()})"

class ItemTormentaIdeas(models.Model):
    ESTADO_ITEM = [
        ('pendiente', 'Pendiente de Evaluación'),
        ('seleccionado', 'Seleccionado para Desarrollo'),
        ('rechazado', 'Rechazado'),
        ('archivado', 'Archivado'),
    ]
    
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    proyecto = models.ForeignKey(
        Proyecto, 
        on_delete=models.CASCADE, 
        related_name='items_ideados'
    )
    experto = models.ForeignKey(
        Experto, 
        on_delete=models.CASCADE, 
        related_name='items_generados'
    )
    puntuacion = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_ITEM,
        default='pendiente'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    experto_propietario = models.ForeignKey(
        Experto,
        on_delete=models.CASCADE,
        related_name='items_propuestos',
        verbose_name="Experto que propuso el item"
    )
    fecha_edicion = models.DateTimeField(null=True, blank=True)
    
    objects = ItemTormentaIdeasManager()

    class Meta:
        verbose_name = "Item de Tormenta de Ideas"
        verbose_name_plural = "Items de Tormenta de Ideas"
        ordering = ['-fecha_creacion']
    
    def get_info_moderador(self):
        """Retorna info para el moderador."""
        return {
            'experto_nombre': self.experto.usuario.get_full_name(),
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y')
        }
    
    def get_items_votacion_context(self, proyecto, experto):
        """
        Obtiene todos los datos necesarios para la vista de votación.
        Returns: dict con items y estadísticas
        """
        # Items por votar (no votados por este experto)
        items_por_votar = self.filter(
            proyecto=proyecto,
            estado='seleccionado'
        ).exclude(
            votos_recibidos__experto=experto
        ).select_related('experto').order_by('-fecha_creacion')
        
        # Items ya votados
        items_votados = self.filter(
            proyecto=proyecto,
            estado='seleccionado',
            votos_recibidos__experto=experto
        ).select_related('experto').order_by('-fecha_creacion')
        
        # Contadores
        total_items = self.filter(proyecto=proyecto, estado='seleccionado').count()
        votados_por_experto = VotoItem.objects.filter(
            experto=experto, proyecto=proyecto
        ).count()
        
        return {
            'items_por_votar': items_por_votar,
            'items_votados': items_votados,
            'total_items': total_items,
            'votados_por_experto': votados_por_experto,
            'pendientes': total_items - votados_por_experto
        }

    def __str__(self):
        return f"{self.titulo[:50]} - {self.experto.usuario.get_full_name()}"

class MensajeChat(models.Model):
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='mensajes_chat'
    )
    experto = models.ForeignKey(
        Experto,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    objects = MensajeChatManager()
    
    def serializar_para_json(self, experto_id_actual):
        """
        Convierte el mensaje a formato JSON para API.
        """
        return {
            'id': self.id,
            'contenido': self.contenido,
            'fecha_envio': self.fecha_envio.strftime('%d/%m/%Y %H:%M'),
            'experto_nombre': self.experto.usuario.get_full_name(),
            'experto_id': self.experto.id,
            'es_propio': self.experto.id == experto_id_actual
        }
    
    class Meta:
        verbose_name = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"
        ordering = ['fecha_envio']

    def __str__(self):
        return f"{self.experto.usuario.get_full_name()} - {self.proyecto.nombre} ({self.fecha_envio.date()})"

class VotoItem(models.Model):
    NIVEL_EVALUACION_CHOICES = [
        (1, 'Muy Bajo'),
        (2, 'Bajo'),
        (3, 'Medio'),
        (4, 'Alto'),
        (5, 'Muy Alto'),
    ]
    experto = models.ForeignKey(
        Experto,
        on_delete=models.CASCADE,
        related_name='votos_items'
    )
    item = models.ForeignKey(
        ItemTormentaIdeas,
        on_delete=models.CASCADE,
        related_name='votos_recibidos'
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='votaciones_items'
    )
    de_acuerdo = models.BooleanField(
        default=False,
        verbose_name="¿Está de acuerdo con este item?"
    )
    evaluacion = models.IntegerField(
        choices=NIVEL_EVALUACION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Nivel de Evaluación"
    )
    fecha_voto = models.DateTimeField(auto_now_add=True)
    
    objects = VotoItemManager()
    
    class Meta:
        unique_together = ['experto', 'item']
        verbose_name = "Voto de Item"
        verbose_name_plural = "Votos de Items"
        ordering = ['-fecha_voto']
    
    def serializar_para_respuesta(self):
        """Serializa el voto para respuesta JSON."""
        return {
            'id': self.id,
            'item_id': self.item.id,
            'de_acuerdo': self.de_acuerdo,
            'evaluacion': self.evaluacion,
            'fecha_voto': self.fecha_voto.strftime('%d/%m/%Y %H:%M')
        }

    def __str__(self):
        return f"Voto de {self.experto} sobre {self.item.titulo[:30]}"