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
