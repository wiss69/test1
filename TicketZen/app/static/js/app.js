const TZ_I18N = {
  fr: { uploaded: 'Fichier envoyé', analyzing: 'Analyse en cours', done: 'Terminé' },
  en: { uploaded: 'File uploaded', analyzing: 'Analyzing', done: 'Done' }
};
const TZ_COLORS = () => {
  const style = getComputedStyle(document.documentElement);
  return {
    accent: style.getPropertyValue('--accent') || '#38bdf8',
    accent2: style.getPropertyValue('--accent-2') || '#a5b4fc',
  };
};
function showToast(msg){
  const el = document.getElementById('toast');
  if(!el) return;
  el.textContent = msg;
  el.style.display = 'block';
  setTimeout(()=> el.style.display='none', 2500);
}
const langButtons = document.querySelectorAll('.lang-switch .lang');
langButtons.forEach(btn => btn.addEventListener('click', () => {
  langButtons.forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.documentElement.lang = btn.dataset.lang;
}));
