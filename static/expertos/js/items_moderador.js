document.addEventListener('DOMContentLoaded', function() {
    const proyectoId = window.PROYECTO_ID;
    const moderadorId = window.EXPERTO_ID;  // Renombrar para claridad
    const formItem = document.getElementById('formItem');
    const inputItem = document.getElementById('inputItem');
    const selectExpertoItem = document.getElementById('selectExpertoItem');
    const listaItems = document.getElementById('listaItems');
    const modalEditarItem = new bootstrap.Modal(document.getElementById('modalEditarItem'));
    const formEditarItem = document.getElementById('formEditarItem');
    const editItemId = document.getElementById('editItemId');
    const editItemTitulo = document.getElementById('editItemTitulo');
    const editItemExperto = document.getElementById('editItemExperto');
    const btnGuardarEdicion = document.getElementById('btnGuardarEdicion');

    // ==================== AÑADIR ITEM ====================

    formItem.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const titulo = inputItem.value.trim();
        const expertoAsignadoId = selectExpertoItem.value;
        
        if (!titulo) {
            mostrarToast('❌ El título no puede estar vacío', 'danger');
            return;
        }
        
        if (!expertoAsignadoId) {
            mostrarToast('❌ Debes asignar la idea a un experto', 'danger');
            return;
        }

        // === DEBUG EN CONSOLA DEL NAVEGADOR ===
        console.log('📤 ENVIANDO ITEM:');
        console.log('- Titulo:', titulo);
        console.log('- Experto asignado ID:', expertoAsignadoId);
        console.log('- Moderador ID:', moderadorId);
        console.log('- Proyecto ID:', proyectoId);
        console.log('- URL:', `/api/proyecto/${proyectoId}/items/`);
        // =========================================

        try {
            // === CORREGIR LA URL (era la del chat antes) ===
            const response = await fetch(`/api/proyecto/${proyectoId}/items/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    titulo: titulo,
                    descripcion: 'Item desde chat moderador',
                    experto_id: expertoAsignadoId,  // El experto al que se asigna
                    moderador_id: moderadorId        // ¡EL MODERADOR QUE ESTÁ CREANDO!
                })
            });

            const data = await response.json();
            console.log('📥 RESPUESTA:', data);  // Ver la respuesta

            if (data.success) {
                agregarItemAlDOM(data.item);
                inputItem.value = '';
                selectExpertoItem.value = '';
                mostrarToast('✅ Idea añadida', 'success');
            } else {
                console.error('❌ Error en respuesta:', data.error);
                mostrarToast('❌ ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('❌ Error de conexión:', error);
            mostrarToast('Error de conexión', 'danger');
        }
    });

    function agregarItemAlDOM(item) {
        const divItem = document.createElement('div');
        divItem.className = 'alert alert-success py-2 px-3 mb-2 d-flex justify-content-between align-items-center';
        divItem.dataset.itemId = item.id;
        divItem.innerHTML = `
            <div class="flex-grow-1">
                <span class="small d-block">${item.titulo}</span>
                <small class="text-muted">
                    <i class="fas fa-user-circle"></i> ${item.experto_nombre}
                </small>
            </div>
            <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-link text-primary p-0 editar-item" 
                        data-item-id="${item.id}" 
                        data-item-titulo="${item.titulo}"
                        data-experto-id="${item.experto_id}"
                        title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-link text-danger p-0 eliminar-item" 
                        data-item-id="${item.id}"
                        title="Eliminar">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        listaItems.appendChild(divItem);
    }

    // ==================== ELIMINAR ITEM ====================

    listaItems.addEventListener('click', async function(e) {
        // Manejar eliminación
        if (e.target.closest('.eliminar-item')) {
            const btnEliminar = e.target.closest('.eliminar-item');
            const itemId = btnEliminar.dataset.itemId;
            
            if (!confirm('¿Eliminar esta idea?')) return;

            try {
                // Ojo: DELETE con body JSON puede no funcionar en algunos navegadores
                const response = await fetch(`/api/proyecto/${proyectoId}/items/${itemId}/?experto_id=${moderadorId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });

                const data = await response.json();
                console.log('🗑️ RESPUESTA ELIMINAR:', data);

                if (data.success) {
                    btnEliminar.closest('.alert').remove();
                    mostrarToast('✅ Idea eliminada', 'success');
                } else {
                    mostrarToast('❌ ' + data.error, 'danger');
                }
            } catch (error) {
                console.error('❌ Error eliminando:', error);
                mostrarToast('Error de conexión', 'danger');
            }
        }
        
        // Manejar edición
        if (e.target.closest('.editar-item')) {
            const btnEditar = e.target.closest('.editar-item');
            const itemId = btnEditar.dataset.itemId;
            const tituloActual = btnEditar.dataset.itemTitulo;
            const expertoActualId = btnEditar.dataset.expertoId;
            
            editItemId.value = itemId;
            editItemTitulo.value = tituloActual;
            editItemExperto.value = expertoActualId;
            
            modalEditarItem.show();
        }
    });

    // ==================== EDITAR ITEM ====================

    btnGuardarEdicion.addEventListener('click', async function() {
        const itemId = editItemId.value;
        const nuevoTitulo = editItemTitulo.value.trim();
        const nuevoExpertoId = editItemExperto.value;
        
        if (!nuevoTitulo) {
            mostrarToast('❌ El título no puede estar vacío', 'danger');
            return;
        }
        
        if (!nuevoExpertoId) {
            mostrarToast('❌ Debes asignar la idea a un experto', 'danger');
            return;
        }

        try {
            const response = await fetch(`/api/proyecto/${proyectoId}/items/${itemId}/editar/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    titulo: nuevoTitulo,
                    experto_id: nuevoExpertoId,
                    moderador_id: moderadorId  // ¡Enviar moderador_id!
                })
            });

            const data = await response.json();
            console.log('✏️ RESPUESTA EDITAR:', data);

            if (data.success) {
                const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
                if (itemElement) {
                    const tituloSpan = itemElement.querySelector('span.small');
                    tituloSpan.textContent = data.item.titulo;
                    
                    const expertoSmall = itemElement.querySelector('small.text-muted');
                    expertoSmall.innerHTML = `<i class="fas fa-user-circle"></i> ${data.item.experto_nombre}`;
                    
                    const btnEditar = itemElement.querySelector('.editar-item');
                    btnEditar.dataset.itemTitulo = data.item.titulo;
                    btnEditar.dataset.expertoId = data.item.experto_id;
                }
                
                modalEditarItem.hide();
                mostrarToast('✅ Idea actualizada', 'success');
            } else {
                mostrarToast('❌ ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('❌ Error editando:', error);
            mostrarToast('Error de conexión', 'danger');
        }
    });

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

    console.log('✅ Items moderador inicializado con funciones de edición');
});