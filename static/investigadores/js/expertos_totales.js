document.addEventListener('DOMContentLoaded', function() {
    const proyectoId = window.PROYECTO_ID;
	
	const procesoFinalizado = document.getElementById('proceso-finalizado')?.value === 'true';
    
    if (procesoFinalizado) {
        console.log('⚠️ Proceso finalizado detectado. Los botones estarán deshabilitados.');
	}

    // ===== MÉTODO ROBUSTO PARA OBTENER CSRF TOKEN =====
    function getCSRFToken() {
        // Método 1: Desde meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken && metaToken.getAttribute('content')) {
            return metaToken.getAttribute('content');
        }
        
        // Método 2: Desde formulario oculto
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput && tokenInput.value) {
            return tokenInput.value;
        }
        
        // Método 3: Desde cookies
        const cookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        if (cookie) {
            return cookie.split('=')[1];
        }
        
        console.error('❌ No se encontró el token CSRF');
        return '';
    }

    // Ordenamiento
    const ordenSelect = document.getElementById('ordenSelect');
    if (ordenSelect) {
        ordenSelect.addEventListener('change', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('orden', this.value);
            window.location.href = url.toString();
        });
    }

    // Búsqueda en tiempo real
    const buscarInput = document.getElementById('buscarInput');
    const btnBuscar = document.getElementById('btnBuscar');

    function filtrarTabla() {
        const texto = buscarInput ? buscarInput.value.toLowerCase() : '';
        const filas = document.querySelectorAll('#tablaExpertos tbody tr');

        filas.forEach(fila => {
            if (fila.querySelector('td[colspan]')) return; // Skip "no hay datos"

            const nombre = fila.cells[0].textContent.toLowerCase();
            const cargo = fila.cells[2].textContent.toLowerCase();

            if (nombre.includes(texto) || cargo.includes(texto)) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    }

    if (buscarInput) {
        buscarInput.addEventListener('keyup', filtrarTabla);
    }
    if (btnBuscar) {
        btnBuscar.addEventListener('click', filtrarTabla);
    }

    // Modal de confirmación de encuesta
    let expertoActual = null;
    const modalConfirmarEl = document.getElementById('modalConfirmarEncuesta');
    const modalConfirmar = modalConfirmarEl ? new bootstrap.Modal(modalConfirmarEl) : null;
    const nombreExpertoSpan = document.getElementById('nombreExpertoEncuesta');

    document.querySelectorAll('.btn-encuestar:not([disabled])').forEach(btn => {
        btn.addEventListener('click', function() {
            expertoActual = {
                expertoId: this.dataset.expertoId,
                nombre: this.closest('tr').cells[0].textContent.trim()
            };
            if (nombreExpertoSpan) {
                nombreExpertoSpan.textContent = expertoActual.nombre;
            }
            modalConfirmar?.show();
        });
    });

    // ===== ENVIAR ENCUENTA CON CSRF CORRECTO =====
    const btnConfirmarEncuesta = document.getElementById('btnConfirmarEncuesta');
    if (btnConfirmarEncuesta) {
        btnConfirmarEncuesta.addEventListener('click', function() {
            if (!expertoActual) {
                console.error('No hay experto seleccionado');
                return;
            }

            const csrfToken = getCSRFToken(); // Usar la función robusta
            
            // Verificar token antes de enviar
            if (!csrfToken) {
                alert('Error: No se pudo obtener el token CSRF. Actualiza la página.');
                return;
            }

            // Añadir log para depuración
            console.log('Enviando encuesta...', {
                proyectoId: proyectoId,
                expertoId: expertoActual.expertoId,
                csrfToken: csrfToken.substring(0, 10) + '...' // Solo para log
            });

            fetch(`/ajax/proyecto/${proyectoId}/enviar-encuesta/${expertoActual.expertoId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                modalConfirmar?.hide();

                if (data.success) {
                    mostrarToast('success', data.message);
                    // Desactivar botón
                    const btn = document.querySelector(
                        `.btn-encuestar[data-experto-id="${expertoActual.expertoId}"]`
                    );
                    if (btn) {
                        btn.disabled = true;
                        btn.innerHTML = '<i class="fas fa-poll me-1"></i> Enviada';
                        btn.classList.remove('btn-outline-primary');
                        btn.classList.add('btn-secondary');
                    }
                } else {
                    mostrarToast('error', data.error || 'Error al enviar encuesta');
                }
            })
            .catch(error => {
                console.error('Error en la petición:', error);
                modalConfirmar?.hide();
                mostrarToast('error', 'Error de conexión con el servidor');
            });
        });
    }

    // Ver detalles de experto
    const modalDetallesEl = document.getElementById('modalDetallesExperto');
    const modalDetalles = modalDetallesEl ? new bootstrap.Modal(modalDetallesEl) : null;
    const detallesContent = document.getElementById('detallesExpertoContent');

    document.querySelectorAll('.btn-ver-detalles').forEach(btn => {
        btn.addEventListener('click', function() {
            const expertoId = this.dataset.expertoId;

            fetch(`/ajax/experto/${expertoId}/detalles/`)
                .then(response => response.json())
                .then(data => {
                    if (detallesContent) {
                        detallesContent.innerHTML = `
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Nombre:</strong> ${data.nombre}</p>
                                    <p><strong>Email:</strong> ${data.email}</p>
                                    <p><strong>Grado:</strong> ${data.grado}</p>
                                    <p><strong>Cargo:</strong> ${data.cargo}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Departamento:</strong> ${data.departamento}</p>
                                    <p><strong>Años de Experiencia:</strong> ${data.experiencia}</p>
                                    <p><strong>Coeficiente K:</strong> ${data.coeficiente}</p>
                                    <p><strong>Índice:</strong> ${data.indice}</p>
                                </div>
                            </div>
                            <hr>
                            <div class="row">
                                <div class="col-12">
                                    <h6>Estadísticas</h6>
                                    <p>Total de encuestas: ${data.total_encuestas}</p>
                                    <p>Proyectos activos: ${data.proyectos_activos}</p>
                                    <p>Total de aportes: ${data.total_aportes}</p>
                                </div>
                            </div>
                        `;
                    }
                    modalDetalles?.show();
                })
                .catch(error => {
                    console.error('Error al cargar detalles:', error);
                    mostrarToast('error', 'Error al cargar los detalles del experto');
                });
        });
    });

    // Botones de acción
    const btnDetener = document.getElementById('btnDetener');
    if (btnDetener) {
        btnDetener.addEventListener('click', function() {
            if (confirm('¿Está seguro de detener el proceso de selección?')) {
                mostrarToast('info', 'Proceso detenido');
            }
        });
    }

    document.getElementById('btnCerrar')?.addEventListener('click', function() {
		window.location.href = '/'; // Vuelve a lista de proyectos
	});
	
	if (window.location.pathname.includes('/expertos/')) {
		const expertoIdActual = window.location.pathname.split('/')[2];
		console.log('Experto ID actual:', expertoIdActual);
	}
	
	//setInterval(() => {
	//	if (window.location.pathname.includes('seleccionar-expertos')) {
	//		location.reload();
	//	}
	//}, 30000);
});

// ===== FUNCIONES GLOBALES =====
function mostrarToast(tipo, mensaje) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        console.warn('No se encontró el contenedor de toasts');
        return;
    }

    const id = 'toast' + Date.now();

    const toastHtml = `
        <div id="${id}" class="toast align-items-center text-white bg-${tipo === 'success' ? 'success' : 'danger'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${mensaje}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastEl = document.getElementById(id);
    if (toastEl) {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        setTimeout(() => toastEl.remove(), 6000);
    }
}