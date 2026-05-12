// productos.js — CRUD completo de catálogo de productos

let todosLosProductos = []; // cache para filtro client-side

// ── CARGAR TABLA ──────────────────────────────────────────
async function cargarTablaProductos() {
  const tbody = document.getElementById('prod-tbody');
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-muted)"><i class="fa-solid fa-spinner fa-spin"></i> Cargando…</td></tr>';

  const r = await fetch('/api/productos?todos=1');
  const d = await r.json();
  if (!d.success) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--danger)">Error al cargar productos</td></tr>';
    return;
  }
  todosLosProductos = d.data;
  renderTabla(d.data);
}

function renderTabla(data) {
  const tbody = document.getElementById('prod-tbody');
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:48px;color:var(--text-muted)">
      <i class="fa-solid fa-box-open" style="font-size:36px;display:block;margin-bottom:12px;opacity:.3"></i>
      No hay productos registrados. ¡Agrega el primero!
    </td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(p => {
    const nivelStock = p.venta_dia > 0
      ? Math.round((p.stock_total / p.venta_dia) * 24)
      : null;
    const colorStock = !nivelStock ? '' : nivelStock <= 24 ? 'color:var(--danger);font-weight:700'
      : nivelStock <= 72 ? 'color:var(--warning);font-weight:700' : '';

    return `<tr id="row-${p.id}">
      <td><span style="font-family:monospace;font-size:12px;background:var(--bg);padding:2px 8px;border-radius:6px">${p.sku}</span></td>
      <td style="font-weight:500">${p.nombre}</td>
      <td>${p.categoria ? `<span class="badge badge-gray">${p.categoria}</span>` : '—'}</td>
      <td style="${colorStock}">${p.stock_total}</td>
      <td>${p.precio_unitario ? 'S/. ' + parseFloat(p.precio_unitario).toFixed(2) : '—'}</td>
      <td>${p.venta_dia ? p.venta_dia + ' uds' : '—'}</td>
      <td style="font-size:12px;color:var(--text-muted)">${p.ubicacion_gondola || '—'}</td>
      <td style="white-space:nowrap;display:flex;gap:6px">
        <button class="btn-edit" onclick="editarProducto(${p.id})" title="Editar">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button class="btn-delete" onclick="eliminarProducto(${p.id},'${p.nombre.replace(/'/g,'')}')" title="Eliminar">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>`;
  }).join('');
}

// ── FILTRO CLIENT-SIDE ────────────────────────────────────
function filtrarTabla(q) {
  q = q.trim().toLowerCase();
  if (!q) { renderTabla(todosLosProductos); return; }
  const filtrado = todosLosProductos.filter(p =>
    p.nombre.toLowerCase().includes(q) ||
    p.sku.toLowerCase().includes(q) ||
    (p.categoria || '').toLowerCase().includes(q)
  );
  renderTabla(filtrado);
}

// ── EDITAR: rellena el formulario ─────────────────────────
function editarProducto(id) {
  const p = todosLosProductos.find(x => x.id === id);
  if (!p) return;
  document.getElementById('prod-id').value         = p.id;
  document.getElementById('prod-sku').value         = p.sku;
  document.getElementById('prod-nombre').value      = p.nombre;
  document.getElementById('prod-categoria').value   = p.categoria || '';
  document.getElementById('prod-stock').value       = p.stock_total;
  document.getElementById('prod-precio').value      = p.precio_unitario || '';
  document.getElementById('prod-venta').value       = p.venta_dia || '';
  document.getElementById('prod-ubicacion').value   = p.ubicacion_gondola || '';
  document.getElementById('form-title').textContent = 'Editar Producto';
  document.getElementById('prod-sku').focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── GUARDAR (crear o actualizar) ──────────────────────────
async function guardarProducto() {
  const id     = document.getElementById('prod-id').value;
  const sku    = document.getElementById('prod-sku').value.trim();
  const nombre = document.getElementById('prod-nombre').value.trim();

  document.getElementById('sku-error').classList.add('hidden');

  if (!sku || !nombre) {
    showToast('SKU y Nombre son obligatorios', 'warning');
    return;
  }

  const payload = {
    sku,
    nombre,
    categoria:         document.getElementById('prod-categoria').value,
    stock_total:       parseInt(document.getElementById('prod-stock').value)   || 0,
    precio_unitario:   parseFloat(document.getElementById('prod-precio').value) || 0,
    venta_dia:         parseFloat(document.getElementById('prod-venta').value)  || 0,
    ubicacion_gondola: document.getElementById('prod-ubicacion').value.trim(),
  };

  let result;
  if (id) {
    result = await apiPut(`/api/productos/${id}`, payload, 'Producto actualizado');
  } else {
    result = await apiPost('/api/productos', payload, 'Producto creado');
  }

  if (result) {
    limpiarFormProd();
    cargarTablaProductos();
  } else if (!id) {
    // Puede ser SKU duplicado
    document.getElementById('sku-error-msg').textContent = 'Ese SKU ya existe en el catálogo.';
    document.getElementById('sku-error').classList.remove('hidden');
  }
}

// ── ELIMINAR ──────────────────────────────────────────────
function eliminarProducto(id, nombre) {
  showModal(`¿Desactivar el producto "${nombre}" del catálogo?`, async () => {
    const ok = await apiDelete(`/api/productos/${id}`, 'Producto desactivado');
    if (ok) cargarTablaProductos();
  });
}

// ── LIMPIAR FORMULARIO ────────────────────────────────────
function limpiarFormProd() {
  document.getElementById('prod-id').value = '';
  document.getElementById('form-title').textContent = 'Nuevo Producto';
  ['prod-sku','prod-nombre','prod-categoria','prod-stock',
   'prod-precio','prod-venta','prod-ubicacion'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('sku-error').classList.add('hidden');
}

// ── INIT ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', cargarTablaProductos);
