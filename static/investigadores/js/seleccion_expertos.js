document.addEventListener('DOMContentLoaded', function() {
    const proyectoId = window.PROYECTO_ID;

    function getCSRFToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.getAttribute('content');
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) return tokenInput.value;
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        if (cookie) return cookie.split('=')[1];
        return '';
    }

    function mostrarToast(mensaje, tipo = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const id = 'toast' + Date.now();
        const toastHtml = `
            <div id="${id}" class="toast align-items-center text-white bg-${tipo === 'success' ? 'success' : tipo === 'error' ? 'danger' : tipo} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${mensaje}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toast = new bootstrap.Toast(document.getElementById(id));
        toast.show();
        setTimeout(() => document.getElementById(id)?.remove(), 6000);
    }

    const btnFinalizarProceso = document.getElementById('btnFinalizarProceso');
    
    if (btnFinalizarProceso) {
        btnFinalizarProceso.addEventListener('click', async function() {
            const radioSeleccionado = document.querySelector('input[name="moderador_id"]:checked');
            if (!radioSeleccionado) {
                mostrarToast('⚠️ Debes seleccionar un moderador antes de finalizar', 'warning');
                return;
            }

            if (!confirm('¿Finalizar proceso con moderador asignado?')) {
                return;
            }

            btnFinalizarProceso.disabled = true;
            btnFinalizarProceso.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Finalizando...';

            try {
                const response = await fetch(`/ajax/proyecto/${proyectoId}/finalizar-proceso/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ moderador_id: radioSeleccionado.value })
                });

                const text = await response.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    console.error('Error parseando JSON:', e);
                    throw new Error('Respuesta inválida del servidor');
                }

                if (data.success) {
                    mostrarToast('✅ Proceso finalizado', 'success');
                    document.querySelectorAll('input[name="moderador_id"]').forEach(radio => {
                        radio.disabled = true;
                    });
                    setTimeout(() => {
                        window.location.href = data.redirect_url || `/proyecto/${proyectoId}/lista-chequeo/`;
                    }, 2000);
                } else {
                    mostrarToast('❌ Error: ' + data.error, 'danger');
                    btnFinalizarProceso.disabled = false;
                    btnFinalizarProceso.innerHTML = '<i class="fas fa-clipboard-check me-1"></i> Finalizar Proceso';
                }
            } catch (error) {
                console.error('Error:', error);
                mostrarToast('❌ Error de conexión', 'danger');
                btnFinalizarProceso.disabled = false;
                btnFinalizarProceso.innerHTML = '<i class="fas fa-clipboard-check me-1"></i> Finalizar Proceso';
            }
        });
    }
	
	document.querySelectorAll('.btn-eliminar-experto').forEach(button => {
		button.addEventListener('click', async function() {
			const encuestaId = this.dataset.encuestaId;
			const expertoNombre = this.dataset.expertoNombre;
			
			if (!confirm(`¿Eliminar al experto "${expertoNombre}"? Esta acción no se puede deshacer.`)) {
				return;
			}
			
			const row = this.closest('tr');
			const originalHtml = this.innerHTML;
			
			// Deshabilitar botón durante la petición
			this.disabled = true;
			this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Eliminando...';
			
			try {
				const response = await fetch(`/proyecto/${proyectoId}/encuesta/${encuestaId}/eliminar/`, {
					method: 'POST',
					headers: {
						'X-CSRFToken': getCSRFToken(),
						'X-Requested-With': 'XMLHttpRequest',
						'Content-Type': 'application/json',
					}
				});
				
				const data = await response.json();
				
				if (data.success) {
					mostrarToast(data.message, 'success');
					// Remover la fila de la tabla con efecto fade
					row.style.transition = 'opacity 0.5s';
					row.style.opacity = '0';
					setTimeout(() => row.remove(), 500);
					
					// Verificar si quedan filas
					const remainingRows = document.querySelectorAll('#tablaEncuesta tbody tr').length;
					if (remainingRows === 0) {
						location.reload(); // Recargar para mostrar mensaje "no hay expertos"
					}
				} else {
					mostrarToast('❌ Error: ' + data.error, 'danger');
					// Restaurar botón
					this.disabled = false;
					this.innerHTML = originalHtml;
				}
			} catch (error) {
				console.error('Error:', error);
				mostrarToast('❌ Error de conexión al eliminar', 'danger');
				// Restaurar botón
				this.disabled = false;
				this.innerHTML = originalHtml;
			}
		});
	});

    console.log('✅ seleccion_expertos.js inicializado');
});