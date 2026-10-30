document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('gh-halloween');
  const header = document.querySelector('.masthead');
  if (!header) return;
  const garland = document.createElement('div');
  garland.className = 'gh-halloween-garland'; garland.setAttribute('aria-hidden','true');
  garland.textContent = '✦ 🦇 ✦ 🎃 ✦ 🦇 ✦'; header.prepend(garland);
  const greeting = document.createElement('aside');
  greeting.className = 'gh-halloween-greeting'; greeting.textContent = 'Happy Halloween, Aspen';
  header.after(greeting);
});
