const token = window.TZ_PIN;
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const fileInput = document.getElementById('file-input');

async function pollStatus(){
  const res = await fetch(`/api/intake/${token}/status`);
  const data = await res.json();
  statusEl.textContent = `PIN: ${token} · ${data.state}`;
  if(data.state === 'done' && data.result){
    renderResult(data.result);
  }
}

function renderResult(result){
  resultEl.innerHTML = `
    <div>Marchand: <strong>${result.merchant || 'n/a'}</strong></div>
    <div>Date: ${result.date || 'n/a'}</div>
    <div>Total: ${result.total || 'n/a'}</div>
    <div>Catégorie: ${result.category || 'n/a'}</div>
  `;
}

async function upload(){
  if(!fileInput.files.length){ return showToast('Choisissez un fichier'); }
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  const res = await fetch(`/api/intake/${token}/upload`, { method:'POST', body: form });
  const data = await res.json();
  if(data.ok){ showToast(TZ_I18N.fr.uploaded); pollStatus(); }
  else { showToast(data.error || 'Erreur'); }
}

async function analyze(){
  const res = await fetch(`/api/intake/${token}/analyze`, { method:'POST' });
  const data = await res.json();
  if(data.ok){ showToast(TZ_I18N.fr.analyzing); pollStatus(); }
  else { showToast(data.error || 'Erreur'); }
}

document.getElementById('upload-btn').addEventListener('click', upload);
document.getElementById('analyze-btn').addEventListener('click', analyze);
setInterval(pollStatus, 4000);
pollStatus();
