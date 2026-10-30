document.addEventListener('DOMContentLoaded', () => {
  if (document.body.dataset.page !== 'index.html') return;
  document.body.classList.add('gh-halloween');
  const header = document.querySelector('.masthead');
  if (!header) return;
  const greeting = document.createElement('aside');
  greeting.className = 'gh-halloween-greeting'; greeting.innerHTML = '<span aria-hidden="true">🎃</span> Happy Halloween, Aspen';
  header.after(greeting);
});
