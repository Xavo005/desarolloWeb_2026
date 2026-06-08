// Control visual del tiempo de actualización
document.getElementById('last-update').textContent = new Date().toLocaleTimeString('es-PE', {
  hour: '2-digit', 
  minute: '2-digit'
});

// Funciones locales para el Modal
function abrirEditar(id, nombre, unidades, venta, estado, stockMinimo) {
  document.getElementById('edit-alerta-id').value = id;
  document.getElementById('edit-modal-title').textContent = `Editar: ${nombre}`;
  document.getElementById('edit-unidades').value = unidades;
  document.getElementById('edit-venta').value = venta;
  document.getElementById('edit-estado').value = estado;
  
  // Logica para modo dinámico
  const modo = document.getElementById('edit-modo').value;
  const grupoVenta = document.getElementById('grupo-venta');
  const grupoStockMinimo = document.getElementById('grupo-stock-minimo');
  const inputVenta = document.getElementById('edit-venta');
  const infoVenta = document.getElementById('info-venta-dinamica');
  const inputStockMinimo = document.getElementById('edit-stock-minimo');

  if (modo === 'dinamico') {
    grupoVenta.style.display = '';
    grupoStockMinimo.style.display = 'none';
    inputVenta.setAttribute('readonly', true);
    inputVenta.style.backgroundColor = '#f9f9f9';
    inputVenta.style.cursor = 'not-allowed';
    infoVenta.style.display = 'block';
  } else {
    grupoVenta.style.display = 'none';
    grupoStockMinimo.style.display = '';
    inputVenta.removeAttribute('readonly');
    inputVenta.style.backgroundColor = '';
    inputVenta.style.cursor = '';
    infoVenta.style.display = 'none';
    if (inputStockMinimo) inputStockMinimo.value = stockMinimo;
  }

  limpiarErrores();
  document.getElementById('modal-edit-alerta').classList.remove('hidden');
}

function cerrarEditar() {
  document.getElementById('modal-edit-alerta').classList.add('hidden');
}

// Cerrar al hacer click fuera
document.getElementById('modal-edit-alerta').addEventListener('click', function(e) {
  if (e.target === this) cerrarEditar();
});

// --- VALIDACIÓN EN TIEMPO REAL (Estilo del Profesor) ---

const form = document.getElementById('form-edit-alerta');
const inputUnidades = document.getElementById('edit-unidades');
const inputVenta = document.getElementById('edit-venta');

function showError(input, message) {
  input.classList.add('error');
  const errorEl = document.getElementById('error-' + input.name.replace('_', '-'));
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.style.display = 'block';
  }
}

function showSuccess(input) {
  input.classList.remove('error');
  const errorEl = document.getElementById('error-' + input.name.replace('_', '-'));
  if (errorEl) {
    errorEl.style.display = 'none';
  }
}

function limpiarErrores() {
  inputUnidades.classList.remove('error');
  inputVenta.classList.remove('error');
  const errorUnid = document.getElementById('error-unidades');
  const errorVenta = document.getElementById('error-venta');
  if(errorUnid) errorUnid.style.display = 'none';
  if(errorVenta) errorVenta.style.display = 'none';
}

function validarCampo(input) {
  const val = parseFloat(input.value);
  if (isNaN(val) || input.value.trim() === '') {
    showError(input, 'Este campo es obligatorio');
    return false;
  }
  if (val < 0) {
    showError(input, 'No se permiten valores negativos');
    return false;
  }
  showSuccess(input);
  return true;
}

// Listeners de entrada
if (inputUnidades) inputUnidades.addEventListener('input', () => validarCampo(inputUnidades));
if (inputVenta) inputVenta.addEventListener('input', () => validarCampo(inputVenta));

// Validación al enviar
if (form) {
  form.addEventListener('submit', function(e) {
    const modo = document.getElementById('edit-modo').value;
    const v1 = validarCampo(inputUnidades);
    let v2 = true;
    if (modo === 'dinamico') {
      v2 = validarCampo(inputVenta);
    } else {
      const inputSM = document.getElementById('edit-stock-minimo');
      if (inputSM) v2 = validarCampo(inputSM);
    }
    if (!v1 || !v2) {
      e.preventDefault();
    }
  });
}

// Handler para botones de eliminar alerta con modal Tottus
document.querySelectorAll('.btn-eliminar-alerta').forEach(function(btn) {
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    var url    = btn.getAttribute('data-url');
    var nombre = btn.getAttribute('data-nombre');
    showModal('Descartar la alerta de ' + nombre, function() {
      window.location.href = url;
    });
  });
});
