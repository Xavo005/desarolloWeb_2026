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
    // Lógica para el Semáforo Visual de Stock (Sustituye la lógica de colores anterior)
    let stockBadge = "";
    let stockValue = parseInt(p.stock_total);

    if (stockValue === 0) {
      stockBadge = `<span style="background-color: #fef0f0; color: #d93025; padding: 4px 8px; border-radius: 4px; font-weight: bold;">Agotado (0)</span>`;
    } else if (stockValue < 50) {
      stockBadge = `<span style="background-color: #fef7e0; color: #b06000; padding: 4px 8px; border-radius: 4px; font-weight: bold;">Bajo (${stockValue})</span>`;
    } else {
      stockBadge = `<span style="background-color: #e6f4ea; color: #0b9b43; padding: 4px 8px; border-radius: 4px; font-weight: bold;">Normal (${stockValue})</span>`;
    }

    // Formateo de Moneda a 2 decimales
    let precioFormateado = p.precio_unitario ? 'S/. ' + parseFloat(p.precio_unitario).toFixed(2) : '—';
    // Formateo de Venta con decimal para mejor lectura
    let ventaFormateada = p.venta_dia ? parseFloat(p.venta_dia).toFixed(1) + ' uds' : '—';

    return `<tr id="row-${p.id}">
      <td><span class="sku-badge">${p.sku}</span></td>
      <td style="font-weight:500">${p.nombre}</td>
      <td>${p.categoria ? `<span class="badge badge-gray">${p.categoria}</span>` : '—'}</td>
      <td>${stockBadge}</td>
      <td>${precioFormateado}</td>
      <td>${ventaFormateada}</td>
      <td style="font-size:12px;color:var(--text-muted)">${p.ubicacion_gondola || '—'}</td>
      <td style="white-space:nowrap;display:flex;gap:6px">
        <button class="btn-edit" onclick="editarProducto(${p.id})" title="Editar" style="padding: 4px 8px; border: none; cursor: pointer; color: #1a73e8; background: transparent;">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button class="btn-delete" onclick="eliminarProducto(${p.id},'${p.nombre.replace(/'/g, '')}')" title="Eliminar" style="padding: 4px 8px; border: none; cursor: pointer; color: #d93025; background: transparent;">
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
  document.getElementById('prod-id').value = p.id;
  document.getElementById('prod-sku').value = p.sku;
  document.getElementById('prod-nombre').value = p.nombre;
  document.getElementById('prod-categoria').value = p.categoria || '';
  document.getElementById('prod-stock').value = p.stock_total;
  document.getElementById('prod-precio').value = p.precio_unitario || '';
  document.getElementById('prod-venta').value = p.venta_dia || '';
  document.getElementById('prod-ubicacion').value = p.ubicacion_gondola || '';
  document.getElementById('form-title').textContent = 'Editar Producto';
  document.getElementById('prod-sku').focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── GUARDAR (crear o actualizar) ──────────────────────────
async function guardarProducto() {
  const id = document.getElementById('prod-id').value;
  const sku = document.getElementById('prod-sku').value.trim();
  const nombre = document.getElementById('prod-nombre').value.trim();

  document.getElementById('sku-error').classList.add('hidden');

  if (!sku || !nombre) {
    showToast('SKU y Nombre son obligatorios', 'warning');
    return;
  }

  const payload = {
    sku,
    nombre,
    categoria: document.getElementById('prod-categoria').value,
    stock_total: parseInt(document.getElementById('prod-stock').value) || 0,
    precio_unitario: parseFloat(document.getElementById('prod-precio').value) || 0,
    venta_dia: parseFloat(document.getElementById('prod-venta').value) || 0,
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
  ['prod-sku', 'prod-nombre', 'prod-categoria', 'prod-stock',
    'prod-precio', 'prod-venta', 'prod-ubicacion'].forEach(id => {
      document.getElementById(id).value = '';
    });
  document.getElementById('sku-error').classList.add('hidden');
}

// ── INIT ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', cargarTablaProductos);
