/**
 * UC6: Muestra la vista previa del stock disponible del producto seleccionado.
 */
function cargarProducto(idProducto) {
  const stockTotal = mapaStockTotal[idProducto];
  if (!stockTotal && stockTotal !== 0) { 
    document.getElementById('stock-preview').classList.add('hidden'); 
    return; 
  }
  
  document.getElementById('stock-disponible').textContent = stockTotal;
  document.getElementById('stock-preview').classList.remove('hidden');
  actualizarPreview();
}

/**
 * UC6: Valida en tiempo real que el stock asignado no supere el disponible.
 */
function actualizarPreview() {
  const idProducto = document.getElementById('producto-select').value;
  if (!idProducto) return;
  
  const stockTotal = mapaStockTotal[idProducto] || 0;
  const stockAsignado = (+document.getElementById('stock-final').value || 0)
                      + (+document.getElementById('stock-revend').value || 0);
                      
  const alertaExceso = document.getElementById('stock-warn');
  
  if (stockAsignado > stockTotal) { 
    alertaExceso.classList.remove('hidden'); 
  } else { 
    alertaExceso.classList.add('hidden'); 
  }
}
