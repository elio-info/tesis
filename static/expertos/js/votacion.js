document.addEventListener('DOMContentLoaded', function() {
    function getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }

    const expertoId = window.EXPERTO_ID;
    const proyectoId = window.PROYECTO_ID;

    if (!expertoId || !proyectoId) {
        console.error('❌ Faltan variables globales: EXPERTO_ID o PROYECTO_ID');
        return;
    }

    // Manejar guardado de votos
    document.querySelectorAll('.guardar-voto').forEach(boton => {
        boton.addEventListener('click', async function() {
            const itemId = this.dataset.itemId;
            
            // Buscar el TR padre
            const tr = this.closest('tr[data-item-id]');
            if (!tr) {
                mostrarToast('❌ Error: Fila no encontrada', 'danger');
                return;
            }
            
            // Buscar controles DENTRO del TR
            const checkbox = tr.querySelector('input[type="checkbox"]');
            const select = tr.querySelector('select.evaluacion-select');
            
            if (!checkbox || !select) {
                mostrarToast('❌ Error: Controles no encontrados', 'danger');
                console.error('Checkbox:', checkbox, 'Select:', select);
                return;
            }
            
            const deAcuerdo = checkbox.checked;
            const evaluacion = select.value;
            
            if (!evaluacion) {
                mostrarToast('❌ Selecciona una evaluación', 'danger');
                return;
            }

            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                mostrarToast('❌ Error CSRF: Token no encontrado', 'danger');
                return;
            }

            try {
                const response = await fetch(`/api/proyecto/${proyectoId}/item/${itemId}/votar/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        experto_id: expertoId,
                        de_acuerdo: deAcuerdo,
                        evaluacion: parseInt(evaluacion)
                    })
                });

                const data = await response.json();
                console.log('🗳️ RESPUESTA:', data);

                if (data.success) {
                    location.reload();
                } else {
                    mostrarToast('❌ ' + data.error, 'danger');
                }
            } catch (error) {
                console.error('❌ Error completo:', error);
                mostrarToast('Error de red: ' + error.message, 'danger');
            }
        });
    });

    // Habilitar botón cuando se selecciona evaluación
    document.querySelectorAll('.evaluacion-select').forEach(select => {
        select.addEventListener('change', function() {
            const itemId = this.dataset.itemId;
            const boton = document.querySelector(`.guardar-voto[data-item-id="${itemId}"]`);
            if (boton) {
                boton.disabled = !this.value;
            }
        });
    });

    function mostrarToast(mensaje, tipo = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            console.error('❌ ToastContainer no encontrado');
            return;
        }
        
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
});