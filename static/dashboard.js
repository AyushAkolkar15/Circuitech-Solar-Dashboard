// Fetch charts for fields exposed via field_map variable (passed server-side)
(async function(){
  // find all canvas elements with id pattern chart-<field>
  document.querySelectorAll('canvas[id^="chart-"]').forEach(async function(canvas){
    const id = canvas.id.split('-')[1];
    try {
      const res = await fetch('/api/field/' + id + '?results=30');
      if (!res.ok) return;
      const json = await res.json();
      const labels = json.labels.map(s => new Date(s).toLocaleTimeString());
      const values = json.values.map(v => v === null ? null : Number(v));
      new Chart(canvas.getContext('2d'), {
        type:'line',
        data:{ labels, datasets:[{ data: values, borderColor:'#ff9800', backgroundColor:'rgba(255,193,7,0.16)', fill:true, tension:0.35 }]},
        options:{ plugins:{legend:{display:false}}, scales:{ x:{ display:false }, y:{ beginAtZero:false } } }
      });
      // set latest if element exists
      const latestEl = document.getElementById('latest-' + id);
      if (latestEl){
        latestEl.textContent = values.length ? (values[values.length-1] ?? '--') : '--';
      }
    } catch(e){ console.error('chart load error', e); }
  });
})();