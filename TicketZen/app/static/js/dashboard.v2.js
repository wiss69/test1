const colors = TZ_COLORS();
const donut = document.getElementById('chart-donut');
const bar = document.getElementById('chart-bar');
new Chart(donut, {
  type: 'doughnut',
  data: { labels: ['Supermarché','Électronique','Restauration'], datasets: [{ data: [12,5,3], backgroundColor: [colors.accent, colors.accent2, '#22c55e'] }]},
  options: { plugins: { legend: { position: 'bottom' }}}
});
new Chart(bar, {
  type: 'bar',
  data: { labels: ['Avr','Mai','Juin'], datasets: [{ label: 'Total €', data: [120, 230, 180], backgroundColor: colors.accent }]},
  options: { scales: { y: { beginAtZero: true }}}
});
