// escanear.js — Lógica del módulo escáner (QuaggaJS)

let scannerActivo  = false;
let ultimoSku      = '';
let scanCooldown   = false; // evita lecturas duplicadas en milisegundos

// ── INICIAR ESCÁNER ───────────────────────────────────────
function iniciarEscaner() {
  const wrap = document.getElementById('scanner-wrap');
  wrap.style.display = 'block';

  Quagga.init({
    inputStream: {
      name: 'Live',
      type: 'LiveStream',
      target: document.querySelector('#interactive'),
      constraints: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'environment', // cámara trasera del celular
      },
    },
    decoder: {
      readers: [
        'ean_reader',        // EAN-13 (supermercados)
        'ean_8_reader',
        'code_128_reader',   // Códigos internos
        'code_39_reader',
      ],
    },
    locate: true,
    frequency: 5, // fotogramas por segundo analizados
  }, (err) => {
    if (err) {
      console.error('[Escáner] Error al iniciar:', err);
      showToast('No se pudo acceder a la cámara. Usa la búsqueda manual.', 'error', 5000);
      return;
    }
    Quagga.start();
    scannerActivo = true;
    document.getElementById('btn-iniciar').style.display = 'none';
    document.getElementById('btn-detener').style.display = 'flex';
  });

  // Evento: código detectado
  Quagga.onDetected((result) => {
    const codigo = result.codeResult.code;
    if (!codigo || scanCooldown || codigo === ultimoSku) return;

    // Cooldown de 2 segundos para evitar disparos dobles
    scanCooldown = true;
    setTimeout(() => { scanCooldown = false; }, 2000);

    ultimoSku = codigo;
    // Vibración táctil si disponible
    if (navigator.vibrate) navigator.vibrate(120);
    buscarProducto(codigo);
  });

  // Dibujar bounding box sobre el código detectado
  Quagga.onProcessed((result) => {
    const canvas = Quagga.canvas.dom.overlay;
    const ctx    = Quagga.canvas.ctx.overlay;
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (result && result.boxes) {
      result.boxes
        .filter(b => b !== result.box)
        .forEach(box => {
          Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, ctx, { color: 'rgba(0,163,77,0.4)', lineWidth: 2 });
        });
    }
    if (result && result.box) {
      Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, ctx, { color: '#00A34D', lineWidth: 3 });
    }
  });
}

// ── DETENER ESCÁNER ───────────────────────────────────────
function detenerEscaner() {
  if (scannerActivo) {
    Quagga.stop();
    scannerActivo = false;
  }
  document.getElementById('btn-iniciar').style.display = 'flex';
  document.getElementById('btn-detener').style.display = 'none';
}

// ── BÚSQUEDA MANUAL ───────────────────────────────────────
function buscarManual() {
  const sku = document.getElementById('sku-manual').value.trim();
  if (!sku) { showToast('Ingresa un SKU para buscar', 'warning'); return; }
  buscarProducto(sku);
}

// ── BUSCAR EN BACKEND ─────────────────────────────────────
async function buscarProducto(sku) {
  showToast(`Buscando SKU: ${sku}…`, 'success', 1500);

  let data;
  try {
    const r = await fetch(`/api/productos/buscar-sku/${encodeURIComponent(sku)}`);
    data = await r.json();
  } catch {
    showToast('Error de conexión', 'error');
    return;
  }

  // Detener cámara al mostrar resultado
  detenerEscaner();

  const sec = document.getElementById('result-section');
  const enc = document.getElementById('result-encontrado');
  const noe = document.getElementById('result-no-encontrado');
  sec.style.display = 'block';

  if (data.success && data.data) {
    const p = data.data;
    enc.style.display = 'block';
    noe.style.display = 'none';

    document.getElementById('r-nombre').textContent    = p.nombre;
    document.getElementById('r-sku').textContent       = p.sku;
    document.getElementById('r-categoria').textContent = p.categoria || 'Sin categoría';
    document.getElementById('r-stock').textContent     = p.stock_total;
    document.getElementById('r-venta').textContent     = p.venta_dia || '—';
    document.getElementById('r-horas').textContent     = p.horas_restantes
      ? (p.horas_restantes >= 9999 ? '∞' : p.horas_restantes + 'h')
      : '—';
    document.getElementById('aj-producto-id').value   = p.id;
    document.getElementById('aj-contado').value        = '';
    document.getElementById('aj-motivo').value         = '';

    // Banner de alerta si hay quiebre
    const banner = document.getElementById('r-alerta-banner');
    if (p.alerta_nivel && p.alerta_nivel !== 'ok') {
      document.getElementById('r-alerta-msg').textContent =
        p.alerta_nivel === 'critico'
          ? `⚠️ QUIEBRE CRÍTICO — Quedan menos de 24h de stock`
          : `Alerta activa: nivel "${p.alerta_nivel}"`;
      banner.classList.remove('hidden');
    } else {
      banner.classList.add('hidden');
    }

    sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else {
    enc.style.display = 'none';
    noe.style.display = 'block';
    document.getElementById('r-sku-noencontrado').textContent = sku;
    sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ── REGISTRAR CONTEO MANUAL ───────────────────────────────
async function registrarConteo() {
  const prodId   = document.getElementById('aj-producto-id').value;
  const contado  = parseInt(document.getElementById('aj-contado').value);
  const motivo   = document.getElementById('aj-motivo').value.trim();

  if (!prodId) { showToast('Error: producto no identificado', 'error'); return; }
  if (isNaN(contado) || contado < 0) { showToast('Ingresa una cantidad válida (≥ 0)', 'warning'); return; }

  const result = await apiPost('/api/conteos', {
    producto_id: +prodId,
    stock_contado: contado,
    motivo,
  }, 'Conteo registrado correctamente');

  if (result) {
    // Actualizar el valor de stock en pantalla
    document.getElementById('r-stock').textContent = contado;
    document.getElementById('aj-contado').value = '';
    document.getElementById('aj-motivo').value  = '';
    showToast('Historial actualizado ✓', 'success');
  }
}

// ── RESET ─────────────────────────────────────────────────
function resetScanner() {
  ultimoSku = '';
  document.getElementById('result-section').style.display = 'none';
  document.getElementById('result-encontrado').style.display = 'none';
  document.getElementById('result-no-encontrado').style.display = 'none';
  document.getElementById('sku-manual').value = '';
}

// ── INIT ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // No iniciamos la cámara automáticamente para no pedir permisos sin acción del usuario
});
