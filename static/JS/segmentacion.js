// ==============================================================================
// UC6 - SEGMENTAR STOCK (Desarrollado por: Gianella)
// Lógica frontend para crear y visualizar reglas de segmentación de inventario.
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
    // ---------------------------------------------------------
    // 1. Referencias a los elementos principales de la interfaz
    // ---------------------------------------------------------
    const vistaListaReglas = document.getElementById('view-lista');
    const vistaFormulario  = document.getElementById('view-formulario');
    const btnNuevaRegla    = document.getElementById('btnNuevaRegla');
    const btnVolver        = document.getElementById('btnVolver');
    const btnGuardarRegla  = document.getElementById('btnGuardar');

    // ---------------------------------------------------------
    // 2. Navegación entre la Lista y el Formulario
    // ---------------------------------------------------------
    // Muestra el formulario para crear una nueva segmentación
    btnNuevaRegla.onclick = () => {
        vistaListaReglas.classList.add('hidden');
        vistaFormulario.classList.remove('hidden');
    };

    // Regresa a la lista principal sin guardar
    btnVolver.onclick = () => {
        vistaFormulario.classList.add('hidden');
        vistaListaReglas.classList.remove('hidden');
    };

    // ---------------------------------------------------------
    // 3. Lógica para GUARDAR una nueva segmentación
    // ---------------------------------------------------------
    btnGuardarRegla.onclick = async () => {
        // Capturamos los datos ingresados por el usuario
        const datosSegmentacion = {
            producto_id: document.getElementById('selectProducto').value,
            stock_final: document.getElementById('inputFinal').value,
            stock_revendedor: document.getElementById('inputRevendedor').value,
            motivo: document.getElementById('inputMotivo').value,
            // Valores por defecto para límites de compra
            limite_compra_final: 0,
            limite_compra_revendedor: 0
        };

        // Verificamos que no haya dejado los campos de stock vacíos
        if (!datosSegmentacion.stock_final || !datosSegmentacion.stock_revendedor) {
            showToast("Por favor, llena ambos campos de stock.", "warning");
            return;
        }

        try {
            // Enviamos la petición al servidor (backend)
            const respuesta = await fetch('/api/segmentaciones', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datosSegmentacion)
            });

            const resultado = await respuesta.json();

            if (resultado.success) {
                // Éxito: Notificamos al usuario y actualizamos la interfaz
                showToast("¡Regla de segmentación guardada con éxito!", "success");
                
                // Ocultar formulario y mostrar lista actualizada
                vistaFormulario.classList.add('hidden');
                vistaListaReglas.classList.remove('hidden');
                cargarSegmentaciones(); // Recargamos la lista visual
            } else {
                // El backend rechazó la petición (ej. no hay stock suficiente)
                showToast("No se pudo guardar: " + resultado.message, "danger");
            }
        } catch (error) {
            console.error("Error al intentar guardar la regla:", error);
            showToast("Error de conexión con el servidor.", "danger");
        }
    };

    // ---------------------------------------------------------
    // 4. Inicialización: Cargar datos al entrar a la página
    // ---------------------------------------------------------
    cargarProductosParaDropdown();
    cargarSegmentaciones();
});

// ==============================================================================
// Funciones Auxiliares (Fetch Data)
// ==============================================================================

/**
 * UC6: Carga la lista de productos disponibles en el <select> del formulario.
 */
async function cargarProductosParaDropdown() {
    const selectProducto = document.getElementById('selectProducto');
    try {
        const respuesta = await fetch('/api/productos');
        const json = await respuesta.json();
        
        if (json.success) {
            // Generamos las opciones del dropdown mostrando el nombre y el stock actual
            selectProducto.innerHTML = json.data.map(producto => 
                `<option value="${producto.id}">${producto.nombre} (Stock Total: ${producto.stock_total})</option>`
            ).join('');
        }
    } catch (error) {
        console.error("Error al cargar productos:", error);
    }
}

/**
 * UC6: Carga y renderiza todas las reglas de segmentación activas en la interfaz.
 */
async function cargarSegmentaciones() {
    const contenedorReglas = document.getElementById('rulesContainer');
    try {
        const respuesta = await fetch('/api/segmentaciones');
        const json = await respuesta.json();
        
        if (json.success) {
            // Renderizamos cada tarjeta de regla de segmentación
            contenedorReglas.innerHTML = json.data.map(segmento => `
                <div class="rule-card">
                    <span class="sku">${segmento.sku}</span>
                    <span class="name">${segmento.nombre}</span>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-top:8px;">
                        <span>🛒 Cliente Final: <b>${segmento.stock_cliente_final}</b> unid.</span>
                        <span>📦 Revendedor: <b>${segmento.stock_revendedor}</b> unid.</span>
                    </div>
                </div>
            `).join('');

            // Actualizamos las estadísticas superiores
            document.getElementById('statTotal').innerText = json.data.length;
            const activas = json.data.filter(s => s.activo).length;
            document.getElementById('statActivas').innerText = activas;
        }
    } catch (error) {
        console.error("Error al cargar segmentaciones:", error);
    }
}