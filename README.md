# Sistema de Gestión de Proyectos con Expertos

Una aplicación Django para la gestión colaborativa de calidad de proyectos.

## 📋 Características Principales
- **Gestión de Roles**: Investigadores, Expertos y Moderadores
- **Tormenta de Ideas**: Chat colaborativo con creación y gestión de items
- **Votaciones**: Sistema de votación sobre items generados
- **Selección de Expertos**: Workflow completo con encuestas de satisfacción
- **Dashboards Personalizados**: Interfaz adaptada por rol de usuario

## 🏗️ Arquitectura
Este proyecto sigue el patrón "Views Delgadas, Modelos Gordos":
- **Las vistas** solo orquestan llamadas a los modelos
- **La lógica de negocio** reside en los managers y métodos de modelo
- **API endpoints** separados para operaciones AJAX
- **Templates específicos** por rol (experto vs moderador)

## 📦 Requisitos
- Python 3.8+
- Django 4.2+
- Base de datos SQLite

## 🎯 Flujo de Trabajo

### 1. Configuración Inicial
El investigador es automáticamente el primer experto registrado (`Experto.objects.first()`)

### 2. Crear Proyecto
El investigador crea un nuevo proyecto desde su dashboard

### 3. Selección de Expertos
- Enviar encuestas de satisfacción a expertos
- Expertos completan encuestas
- Sistema valida expertos según criterios

### 4. Tormenta de Ideas
- Moderador inicia chat colaborativo
- Todos los expertos pueden añadir items
- Moderador edita/elimina items en tiempo real

### 5. Votación
- Cierre de tormenta genera votaciones automáticas
- Expertos votan cada item
- Sistema calcula consenso y estadísticas

### 6. Finalización
- Investigador selecciona expertos finales
- Proceso se cierra y genera reportes

📂 Estructura de Directorios
```text
📁 app/
    📁 migrations/
        📁 __pycache__/
        📄 0001_initial.py
        📄 __init__.py
    📁 templates/
        📁 expertos/
            📄 base_expertos.html
            📄 chat_moderador.html
            📄 chat_proyecto.html
            📄 completar_encuesta.html
            📄 inicio_expertos.html
            📄 resultados_votacion.html
            📄 votacion.html
        📁 investigadores/
            📄 base_investigadores.html
            📄 crear_proyecto.html
            📄 detalle_proyecto.html
            📄 expertos_finales.html
            📄 expertos_totales.html
            📄 inicio.html
            📄 seleccion_expertos.html
    📁 templatetags/
        📁 __pycache__/
        📄 __init__.py
        📄 custom_tags.py
    📁 views/
        📁 __pycache__/
        📁 api/
            📁 __pycache__/
            📄 __init__.py
        📁 expertos/
            📁 __pycache__/
            📄 __init__.py
            📄 chat.py
            📄 chat_moderador.py
            📄 dashboard.py
            📄 encuestas.py
            📄 votacion.py
        📁 investigadores/
            📁 __pycache__/
            📄 __init__.py
            📄 expertos_finales.py
            📄 expertos_totales.py
            📄 seleccion_expertos.py
            📄 vistas_principales.py
        📁 utils/
            📁 __pycache__/
            📄 __init__.py
            📄 calculos.py
        📄 __init__.py
    📄 __init__.py
    📄 admin.py
    📄 apps.py
    📄 forms.py
    📄 models.py
    📄 old_models.py
    📄 old_views.py
    📄 signals.py
    📄 tests.py
    📄 urls.py
📁 project/
    📁 __pycache__/
    📄 __init__.py
    📄 asgi.py
    📄 settings.py
    📄 urls.py
    📄 wsgi.py
📁 static/
    📁 bootstrap/
        📁 bootstrap/
            📁 css/
                📄 bootstrap.min.css
            📁 js/
                📄 bootstrap.bundle.min.js
        📁 fontawesome/
            📁 css/
                📄 all.min.css
            📁 webfonts/
                📄 fa-brands-400.woff2
                📄 fa-regular-400.woff2
                📄 fa-solid-900.woff2
                📄 fa-v4compatibility.woff2
        📁 jquery/
            📄 jquery.min.js
    📁 expertos/
        📁 css/
            📄 completar_encuesta.css
            📄 style.css
        📁 js/
            📄 chat_proyecto.js
            📄 completar_encuesta.js
            📄 completar_tormenta.js
            📄 items_moderador.js
            📄 main.js
            📄 votacion.js
    📁 investigadores/
        📁 css/
            📄 expertos_finales.css
            📄 expertos_totales.css
            📄 seleccion_expertos.css
            📄 style.css
        📁 js/
            📄 expertos_finales.js
            📄 expertos_totales.js
            📄 main.js
            📄 seleccion_expertos.js
📁 venv/
📄 .gitignore
📄 datos.json
📄 db.sqlite3
📄 estructura_carpetas.py
📄 estructura_completa.txt
📄 manage.py
📄 migrations.py
📄 README.md
```

# 🔌 API Endpoints

## Investigadores
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/proyecto/<id>/seleccionar-expertos/` | Listar expertos |
| POST | `/ajax/proyecto/<id>/enviar-encuesta/<exp>/` | Enviar encuesta |
| DELETE | `/proyecto/<id>/encuesta/<id>/eliminar/` | Eliminar encuesta |

## Expertos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/expertos/<id>/` | Dashboard |
| POST | `/expertos/<id>/encuesta/<id>/guardar/` | Guardar encuesta |

## Chat
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/proyecto/<id>/chat/<exp>/` | Vista chat |
| GET | `/ajax/.../mensajes/` | Obtener mensajes |
| POST | `/ajax/.../enviar/` | Enviar mensaje |

## Moderador
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/proyecto/<id>/items/` | Crear item |
| PUT | `/api/proyecto/<id>/items/<id>/` | Editar item |
| DELETE | `/api/proyecto/<id>/items/<id>/` | Eliminar item |
| POST | `/api/proyecto/<id>/cerrar-tormenta/` | Cerrar tormenta |

## Votaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/proyecto/<id>/votar/<exp>/` | Vista votación |
| POST | `/api/proyecto/<id>/item/<id>/votar/` | Guardar voto |
