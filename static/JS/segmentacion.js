document.addEventListener("DOMContentLoaded", () => {
    // Referencias de la interfaz
    const viewLista = document.getElementById('view-lista');
    const viewForm = document.getElementById('view-formulario');
    const btnNueva = document.getElementById('btnNuevaRegla');
    const btnVolver = document.getElementById('btnVolver');
    const btnGuardar = document.getElementById('btnGuardar');

    // Navegación entre pantallas
    btnNueva.onclick = () => {
        viewLista.classList.add('hidden');
        viewForm.classList.remove('hidden');
    };

    btnVolver.onclick = () => {
        viewForm.classList.add('hidden');
        viewLista.classList.remove('hidden');
    };

    // --- FUNCIÓN PARA GUARDAR ---
    btnGuardar.onclick = async () => {
        const data = {
            producto_id: document.getElementById('selectProducto').value,
            stock_final: document.getElementById('inputFinal').value,
            stock_revendedor: document.getElementById('inputRevendedor').value,
            motivo: document.getElementById('inputMotivo').value,
            // Agregamos límites en 0 por defecto si no tienes los inputs visibles
            limite_compra_final: 0,
            limite_compra_revendedor: 0
        };

        // Validación simple
        if (!data.stock_final || !data.stock_revendedor) {
            alert("Por favor, llena los campos de stock");
            return;
        }

        try {
            const res = await fetch('/api/segmentaciones', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();

            if (result.success) {
                alert("¡Guardado en XAMPP con éxito!");
                // Limpiar formulario y volver a la lista
                viewForm.classList.add('hidden');
                viewLista.classList.remove('hidden');
                cargarSegmentaciones(); // Recargar la lista para ver la nueva tarjeta
            } else {
                alert("Error: " + result.message);
            }
        } catch (error) {
            console.error("Error al guardar:", error);
            alert("No se pudo conectar con el servidor");
        }
    };

    // Cargar datos iniciales
    cargarProductos();
    cargarSegmentaciones();
});

// Cargar productos al select
async function cargarProductos() {
    const select = document.getElementById('selectProducto');
    const res = await fetch('/api/productos');
    const json = await res.json();
    if(json.success) {
        select.innerHTML = json.data.map(p => `<option value="${p.id}">${p.nombre} (Total: ${p.stock_total})</option>`).join('');
    }
}

// Cargar reglas a la lista
async function cargarSegmentaciones() {
    const container = document.getElementById('rulesContainer');
    const res = await fetch('/api/segmentaciones');
    const json = await res.json();
    if(json.success) {
        container.innerHTML = json.data.map(seg => `
            <div class="rule-card">
                <span class="sku">${seg.sku}</span>
                <span class="name">${seg.nombre}</span>
                <div style="display:flex; justify-content:space-between; font-size:12px;">
                    <span>🛒 Cliente: <b>${seg.stock_cliente_final}</b></span>
                    <span>📦 Revend: <b>${seg.stock_revendedor}</b></span>
                </div>
            </div>
        `).join('');
        document.getElementById('statTotal').innerText = json.data.length;
        document.getElementById('statActivas').innerText = json.data.filter(s => s.activo).length;
    }
}