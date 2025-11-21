const tableBody = document.querySelector('#expenses-table tbody');
const dummy = [
  { merchant: 'Netto', date: '2024-05-01', total: 9.42, category: 'supermarché' },
  { merchant: 'Fnac', date: '2024-05-03', total: 199.99, category: 'électronique' },
];
function renderRows(rows){
  tableBody.innerHTML = '';
  rows.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.merchant}</td><td>${row.date}</td><td>${row.total}</td><td>${row.category}</td>`;
    tableBody.appendChild(tr);
  });
}
renderRows(dummy);

document.getElementById('export-csv').addEventListener('click', () => {
  const header = ['merchant','date','total','category'];
  const csv = [header.join(',')].concat(dummy.map(r => `${r.merchant},${r.date},${r.total},${r.category}`)).join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'expenses.csv';
  link.click();
});
