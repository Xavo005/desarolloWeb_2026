// main.js — Toast + Modal utilities (Tottus SGI)

// ── TOAST ──────────────────────────────────────────────────
function showToast(msg, type = 'success', duration = 3000) {
  const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', warning: 'fa-triangle-exclamation' };
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<i class="fa-solid ${icons[type] || icons.success}"></i><span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(120%)'; el.style.transition = '.3s'; }, duration);
  setTimeout(() => el.remove(), duration + 350);
}

// ── MODAL CONFIRMACIÓN ─────────────────────────────────────
let _modalCallback = null;

function showModal(mensaje, onConfirm) {
  document.getElementById('modal-msg').textContent = mensaje;
  document.getElementById('modal-overlay').classList.remove('hidden');
  _modalCallback = onConfirm;
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('modal-cancel').addEventListener('click', () => {
    document.getElementById('modal-overlay').classList.add('hidden');
    _modalCallback = null;
  });
  document.getElementById('modal-confirm').addEventListener('click', () => {
    document.getElementById('modal-overlay').classList.add('hidden');
    if (_modalCallback) { _modalCallback(); _modalCallback = null; }
  });
  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) e.currentTarget.classList.add('hidden');
  });
});

// ── FETCH HELPERS ──────────────────────────────────────────
async function apiDelete(url, msgExito = 'Eliminado correctamente') {
  try {
    const r = await fetch(url, { method: 'DELETE', headers: { 'Content-Type': 'application/json' } });
    const data = await r.json();
    if (data.success) { showToast(msgExito, 'success'); return true; }
    else { showToast(data.message || 'Error al eliminar', 'error'); return false; }
  } catch { showToast('Error de conexión', 'error'); return false; }
}

async function apiPost(url, body, msgExito = 'Guardado correctamente') {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await r.json();
    if (data.success) { showToast(msgExito, 'success'); return data; }
    else { showToast(data.message || 'Error al guardar', 'error'); return null; }
  } catch { showToast('Error de conexión', 'error'); return null; }
}

async function apiPut(url, body, msgExito = 'Actualizado correctamente') {
  try {
    const r = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await r.json();
    if (data.success) { showToast(msgExito, 'success'); return data; }
    else { showToast(data.message || 'Error al actualizar', 'error'); return null; }
  } catch { showToast('Error de conexión', 'error'); return null; }
}
