/* ================================================================
   SGTM - JavaScript
   Toast notifications & API consumption
   ================================================================ */

document.addEventListener('DOMContentLoaded', function() {
    // ========== AUTO-DISMISS TOASTS ==========
    initToasts();

    // ========== FECHA MÍNIMA EN INPUTS DATE ==========
    initDateInputs();
});

/**
 * Inicializa los toasts: auto-dismiss después de 5 segundos.
 */
function initToasts() {
    const toasts = document.querySelectorAll('.sgtm-toast');
    toasts.forEach(function(toast) {
        setTimeout(function() {
            toast.style.animation = 'toastSlideOut 0.4s ease-in forwards';
            setTimeout(function() { toast.remove(); }, 400);
        }, 5000);
    });

    // Revisar si hay un toast en sessionStorage (para mostrar después de un redirect JS)
    const pendingToast = sessionStorage.getItem("sgtm_pending_toast");
    if (pendingToast) {
        try {
            const toastData = JSON.parse(pendingToast);
            mostrarToastJS(toastData.tipo, toastData.titulo, toastData.mensaje);
            sessionStorage.removeItem("sgtm_pending_toast");
        } catch (e) {}
    }
}

/**
 * Muestra un toast generado 100% en JS con el mismo estilo de Django messages
 */
function mostrarToastJS(tipo, titulo, mensaje) {
    let container = document.querySelector('.sgtm-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'sgtm-toast-container';
        document.querySelector('.main-content').insertBefore(container, document.querySelector('.main-content').firstChild);
    }

    const toast = document.createElement('div');
    toast.className = `sgtm-toast sgtm-toast-${tipo === 'error' ? 'danger' : 'success'}`;
    toast.setAttribute('role', 'alert');
    
    const iconClass = tipo === 'error' ? 'bi-exclamation-circle-fill' : 'bi-check-circle-fill';
    
    toast.innerHTML = `
        <div class="sgtm-toast-icon">
            <i class="bi ${iconClass}"></i>
        </div>
        <div class="sgtm-toast-body">
            <strong>${titulo}</strong>
            <span>${mensaje}</span>
        </div>
        <button class="sgtm-toast-close" onclick="this.parentElement.remove()">
            <i class="bi bi-x-lg"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(function() {
        toast.style.animation = 'toastSlideOut 0.4s ease-in forwards';
        setTimeout(function() { toast.remove(); }, 400);
    }, 5000);
}

/**
 * Setea la fecha mínima al día de hoy en todos los inputs date.
 */
function initDateInputs() {
    const inputFecha = document.getElementById('input-fecha');
    if (inputFecha) {
        const hoy = new Date().toISOString().split('T')[0];
        inputFecha.setAttribute('min', hoy);
        inputFecha.value = hoy;
    }
}

/**
 * Consume la API interna de especialidades y llena el select dinámicamente.
 * Se llama desde index.html al cargar la página.
 */
function cargarEspecialidades() {
    fetch('/api/especialidades/')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('select-especialidad');
            if (!select) return;

            select.innerHTML = '<option value="">Seleccione una especialidad...</option>';

            data.especialidades.forEach(esp => {
                const option = document.createElement('option');
                option.value = esp.id;
                option.textContent = esp.nombre;
                select.appendChild(option);
            });

            // Actualizar el stat del hero si existe
            const statEsp = document.getElementById('stat-especialidades');
            if (statEsp) {
                statEsp.textContent = data.especialidades.length;
            }
        })
        .catch(error => {
            console.error('Error al consumir la API:', error);
            const select = document.getElementById('select-especialidad');
            if (select) {
                select.innerHTML = '<option value="">Error al cargar especialidades</option>';
            }
        });
}
