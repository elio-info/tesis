document.addEventListener('DOMContentLoaded', function() {
    const btnCerrarTormenta = document.getElementById('btnCerrarTormenta');
    const modalCerrarTormenta = new bootstrap.Modal(document.getElementById('modalCerrarTormenta'));
    const confirmarCerrarTormenta = document.getElementById('confirmarCerrarTormenta');

    btnCerrarTormenta.addEventListener('click', function() {
        modalCerrarTormenta.show();
    });

    confirmarCerrarTormenta.addEventListener('click', async function() {
        try {
            const response = await fetch(`/api/proyecto/${window.PROYECTO_ID}/cerrar-tormenta/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    moderador_id: window.EXPERTO_ID
                })
            });

            const data = await response.json();
            console.log('🔒 RESPUESTA CERRAR:', data);

            if (data.success) {
                // Mostrar mensaje de éxito
                const toastDiv = document.createElement('div');
                toastDiv.className = 'toast align-items-center text-white bg-success border-0';
                toastDiv.innerHTML = `
                    <div class="d-flex">
                        <div class="toast-body">${data.message}</div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                `;
                document.getElementById('toastContainer').appendChild(toastDiv);
                const toast = new bootstrap.Toast(toastDiv);
                toast.show();
                
                // Redirigir después de 2 segundos
                setTimeout(() => {
                    window.location.href = DASHBOARD_URL;
                }, 2000);
            } else {
                alert('❌ Error: ' + data.error);
            }
        } catch (error) {
            console.error('❌ Error de conexión:', error);
            alert('Error de conexión');
        }
        
        modalCerrarTormenta.hide();
    });
});