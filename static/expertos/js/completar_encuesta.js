document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Inicializando módulo de completar encuesta');

    // Variables globales (definidas desde el template)
    const EXPERTO_ID = window.EXPERTO_ID;
    const DASHBOARD_URL = window.DASHBOARD_URL || `/expertos/${EXPERTO_ID}/`;

    const formEncuesta = document.getElementById('formEncuesta');
    if (!formEncuesta) {
        console.error('❌ Formulario no encontrado');
        return;
    }

    // Validación de campos
    const camposRequeridos = formEncuesta.querySelectorAll('[required]');
    camposRequeridos.forEach(campo => {
        campo.addEventListener('blur', function() {
            validarCampo(this);
        });
    });

    function validarCampo(campo) {
        if (!campo.value.trim()) {
            campo.classList.add('is-invalid');
            campo.classList.remove('is-valid');
            return false;
        } else {
            campo.classList.remove('is-invalid');
            campo.classList.add('is-valid');
            return true;
        }
    }

    // Validación de radios de grado científico
    const radiosGrado = document.querySelectorAll('input[name="grado_cientifico"]');
    
    formEncuesta.addEventListener('submit', function(e) {
        e.preventDefault();
        
        let formValido = true;
        
        // Validar campos de texto
        camposRequeridos.forEach(campo => {
            if (!validarCampo(campo)) {
                formValido = false;
            }
        });
        
        // Validar radios de grado científico
        const gradoSeleccionado = Array.from(radiosGrado).some(r => r.checked);
        if (!gradoSeleccionado) {
            radiosGrado[0].classList.add('is-invalid');
            formValido = false;
            mostrarMensaje('⚠️ Debe seleccionar su grado científico.', 'warning');
        }

        if (!formValido) {
            return;
        }

        // Enviar datos realmente
        enviarEncuesta();
    });

    function enviarEncuesta() {
        const btnEnviar = formEncuesta.querySelector('button[type="submit"]');
        const formData = new FormData(formEncuesta);
        
        // Asegurar CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        if (!formData.has('csrfmiddlewaretoken')) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }
        
        btnEnviar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Enviando...';
        btnEnviar.disabled = true;

        fetch(formEncuesta.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            // Depuración: ver respuesta cruda
            return response.text().then(text => {
                console.log('📥 Respuesta cruda del servidor:', text);
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error('❌ Error parseando JSON:', e);
                    throw new Error('Respuesta inválida del servidor');
                }
            });
        })
        .then(data => {
            if (data.success) {
                mostrarMensaje('✅ Encuesta enviada exitosamente', 'success');
                deshabilitarFormulario();
                
                setTimeout(() => {
                    // Redirigir al dashboard
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.href = DASHBOARD_URL;
                    }
                }, 2000);
            } else {
                mostrarMensaje('❌ Error: ' + data.error, 'danger');
                btnEnviar.disabled = false;
                btnEnviar.innerHTML = '<i class="fas fa-paper-plane me-1"></i> Enviar Encuesta';
            }
        })
        .catch(error => {
            console.error('Error en la petición:', error);
            mostrarMensaje('❌ Error de conexión con el servidor', 'danger');
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = '<i class="fas fa-paper-plane me-1"></i> Enviar Encuesta';
        });
    }

    function mostrarMensaje(mensaje, tipo = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${tipo === 'error' ? 'danger' : tipo} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const contenido = document.querySelector('.container');
        contenido.insertBefore(alertDiv, contenido.firstChild);
        
        setTimeout(() => alertDiv.remove(), 5000);
    }

    function deshabilitarFormulario() {
        formEncuesta.querySelectorAll('input, select, textarea, button').forEach(elemento => {
            elemento.disabled = true;
        });
    }

    // Inicialización
    console.log('🚀 Formulario de encuesta inicializado correctamente');
});