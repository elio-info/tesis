document.addEventListener('DOMContentLoaded', function() {
    const proyectoId = window.PROYECTO_ID;
    const expertoId = window.EXPERTO_ID;
    const formChat = document.getElementById('formChat');
    const inputMensaje = document.getElementById('inputMensaje');
    const contenedorMensajes = document.getElementById('contenedorMensajes');
    const btnEnviar = document.getElementById('btnEnviar');

    // Obtener el último ID inicial de los mensajes existentes
    const ultimoMensajeExistente = contenedorMensajes.querySelector('[data-mensaje-id]');
    let ultimoId = ultimoMensajeExistente ? parseInt(ultimoMensajeExistente.dataset.mensajeId) : 0;
    console.log('📌 Último ID inicial:', ultimoId);

    let enviando = false; // Prevenir envíos múltiples

    // ==================== FUNCIONES ====================

    function agregarMensajeAlDOM(mensaje, esPropio = false) {
        // PREVENCIÓN DEFINITIVA DE DUPLICADOS
        if (document.querySelector(`[data-mensaje-id="${mensaje.id}"]`)) {
            console.log('⚠️ Duplicado evitado:', mensaje.id);
            return;
        }

        const divMensaje = document.createElement('div');
        divMensaje.className = `mb-3 d-flex ${esPropio ? 'justify-content-end' : 'justify-content-start'}`;
        divMensaje.dataset.mensajeId = mensaje.id;

        const contenido = `
            <div class="mensaje-contenido p-3 rounded ${esPropio ? 'bg-primary text-white' : 'bg-light'}" style="max-width: 75%;">
                <small class="d-block fw-bold mb-1">
                    ${esPropio ? 'Tú' : mensaje.experto_nombre}
                </small>
                ${mensaje.contenido}
                <small class="d-block mt-1 opacity-75">${mensaje.fecha_envio}</small>
            </div>
        `;
        
        divMensaje.innerHTML = contenido;
        contenedorMensajes.appendChild(divMensaje);
        contenedorMensajes.scrollTop = contenedorMensajes.scrollHeight;
        console.log('✅ Mensaje agregado:', mensaje.id);
    }

    async function enviarMensaje(contenido) {
        if (!contenido || enviando) return;
        enviando = true;

        btnEnviar.disabled = true;
        btnEnviar.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch(`/ajax/proyecto/${proyectoId}/chat/${expertoId}/enviar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ contenido: contenido })
            });

            const data = await response.json();

            if (data.success) {
                console.log('📤 Mensaje enviado, esperando polling...');
                ultimoId = data.mensaje.id;
                inputMensaje.value = '';
            } else {
                mostrarToast('❌ ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('❌ Error enviando:', error);
            mostrarToast('Error de conexión', 'danger');
        } finally {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar';
            enviando = false;
        }
    }

    async function obtenerNuevosMensajes() {
        try {
            const url = `/ajax/proyecto/${proyectoId}/chat/${expertoId}/mensajes/?ultimo_id=${ultimoId}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.mensajes.length > 0) {
                data.mensajes.forEach(mensaje => {
                    agregarMensajeAlDOM(mensaje, mensaje.es_propio);
                    ultimoId = mensaje.id;
                });
            }
        } catch (error) {
            console.error('❌ Error polling:', error);
        }
    }

    function mostrarToast(mensaje, tipo = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toastDiv = document.createElement('div');
        toastDiv.className = `toast align-items-center text-white bg-${tipo} border-0`;
        toastDiv.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${mensaje}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        toastContainer.appendChild(toastDiv);
        const toast = new bootstrap.Toast(toastDiv);
        toast.show();
        setTimeout(() => toastDiv.remove(), 5000);
    }

    // ==================== EVENT LISTENERS ====================

    // ENTER en textarea (SIN Shift)
    inputMensaje.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevenir salto de línea
            e.stopPropagation(); // Prevenir otros listeners
            formChat.dispatchEvent(new Event('submit'));
        }
    });

    // Submit del formulario
    formChat.addEventListener('submit', function(e) {
        e.preventDefault();
        const contenido = inputMensaje.value.trim();
        if (contenido) {
            enviarMensaje(contenido);
        }
    });

    console.log('✅ Chat inicializado perfectamente');
});