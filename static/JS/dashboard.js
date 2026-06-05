(function() {
  const el = document.getElementById('fecha-hora');
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleDateString('es-PE', {weekday:'long',year:'numeric',month:'long',day:'numeric'})
      + ' · ' + now.toLocaleTimeString('es-PE', {hour:'2-digit',minute:'2-digit'});
  }
  if (el) {
    tick(); setInterval(tick, 60000);
  }

  // Cargar datos de gráficos
  async function cargarGraficos() {
    const chartStockCatEl = document.getElementById('chartStockCat');
    const chartTendenciasEl = document.getElementById('chartTendencias');
    const statPendientesEl = document.getElementById('stat-pendientes');

    function mostrarSinDatos(canvas) {
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.font = '14px "Inter", sans-serif';
      ctx.fillStyle = "#888";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Sin datos disponibles", w / 2, h / 2);
    }

    try {
      const res = await fetch('/api/dashboard/graficos');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();

      if (!data.success) {
        console.error('Error en data.success:', data.message);
        if (chartStockCatEl) mostrarSinDatos(chartStockCatEl);
        if (chartTendenciasEl) mostrarSinDatos(chartTendenciasEl);
        if (statPendientesEl) statPendientesEl.textContent = '0';
        return;
      }
      
      // Rellenar Ajustes Hoy
      const now = new Date();
      const offset = now.getTimezoneOffset() * 60000;
      const todayStr = new Date(now - offset).toISOString().split('T')[0];
      
      const todayObj = data.tendencia_ajustes.find(item => item.dia === todayStr);
      if (statPendientesEl) statPendientesEl.textContent = todayObj ? todayObj.total : 0;
      
      // 1. Gráfico: Stock por Categoría (Doughnut)
      if (chartStockCatEl) {
        if (data.stock_por_categoria && data.stock_por_categoria.length > 0) {
          const catLabels = data.stock_por_categoria.map(item => item.categoria);
          const catValues = data.stock_por_categoria.map(item => item.total_stock);
          
          new Chart(chartStockCatEl.getContext('2d'), {
            type: 'doughnut',
            data: {
              labels: catLabels,
              datasets: [{
                data: catValues,
                backgroundColor: ['#00A34D','#FFB300','#2196F3','#9C27B0','#E91E63','#00BCD4','#FF5722'],
                borderWidth: 1
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'right',
                  labels: { boxWidth: 12, font: { size: 11, family: "'Inter', sans-serif" } }
                }
              }
            }
          });
        } else {
          mostrarSinDatos(chartStockCatEl);
        }
      }
      
      // 2. Gráfico: Tendencia de Ajustes (Line)
      if (chartTendenciasEl) {
        if (data.tendencia_ajustes && data.tendencia_ajustes.length > 0) {
          const trendLabels = data.tendencia_ajustes.map(item => {
            const parts = item.dia.split('-');
            return parts[2] + '/' + parts[1];
          });
          const trendValues = data.tendencia_ajustes.map(item => item.total);
          
          new Chart(chartTendenciasEl.getContext('2d'), {
            type: 'line',
            data: {
              labels: trendLabels,
              datasets: [{
                label: 'Ajustes',
                data: trendValues,
                borderColor: '#00A34D',
                backgroundColor: 'rgba(0, 163, 77, 0.1)',
                fill: true,
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: '#00A34D'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: {
                y: {
                  beginAtZero: true,
                  ticks: { stepSize: 1, font: { size: 10, family: "'Inter', sans-serif" } },
                  grid: { color: '#E0E0E0' }
                },
                x: {
                  grid: { display: false },
                  ticks: { font: { size: 10, family: "'Inter', sans-serif" } }
                }
              }
            }
          });
        } else {
          mostrarSinDatos(chartTendenciasEl);
        }
      }

    } catch (err) {
      console.error('Error cargando gráficos:', err);
      if (chartStockCatEl) mostrarSinDatos(chartStockCatEl);
      if (chartTendenciasEl) mostrarSinDatos(chartTendenciasEl);
      if (statPendientesEl) statPendientesEl.textContent = '0';
    }
  }
  cargarGraficos();
})();
