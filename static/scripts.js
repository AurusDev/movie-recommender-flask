// Melhorias de UX simples
addEventListener('load', () => {
  const form = document.querySelector('form');
  if (!form) return;
  form.addEventListener('submit', () => {
    document.querySelectorAll('.card').forEach(c => c.classList.remove('tilt-in'));
  });
});
