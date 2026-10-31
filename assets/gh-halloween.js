/* Halloween skin — homepage only. Every seasonal element is injected by
   this script and styled by gh-halloween.css; base templates and copy carry
   no seasonal content, so removing the skin removes the whole costume.
   WO#15: dressing ported from the approved concept v3.1 (garland, bats,
   pumpkin hat, Happy Halloween ribbon, moonlit cover). */
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.dataset.page !== 'index.html') return;
  document.body.classList.add('gh-halloween');
  const BAT = '<svg viewBox="0 0 64 32" aria-hidden="true"><path d="M32 14c-3-5-9-8-15-6C11 4 5 5 1 10c5-1 8 1 10 4-3 0-6 1-8 4 6-2 11 0 15 3 5 3 9 3 14-1 5 2 9 2 14-1 4-3 9-5 15-3-2-3-5-4-8-4 2-3 5-5 10-4C59 5 53 4 47 8c-6-2-12 1-15 6z"/></svg>';

  // Garland of pumpkins + bats under the top strip; centre line in the strip.
  const topbar = document.querySelector('.gh-topbar');
  if (topbar && !document.querySelector('.gh-halloween-garland')) {
    const garland = document.createElement('div');
    garland.className = 'gh-halloween-garland'; garland.setAttribute('aria-hidden', 'true');
    garland.innerHTML = '🎃 <span class="sm">🦇</span> 🎃 <span class="sm">👻</span> 🎃 <span class="sm">🦇</span> 🎃 <span class="sm">🌙</span> 🎃 <span class="sm">🦇</span> 🎃';
    topbar.after(garland);
  }
  const center = document.querySelector('.gh-top-center');
  if (center) center.textContent = '🦇 Happy Halloween — This Week in Costume 🦇';

  const header = document.querySelector('.masthead');
  if (!header) return;

  // Bats around the masthead + a pumpkin perched on the wordmark.
  if (!header.querySelector('.hw-bats')) {
    const bats = document.createElement('div');
    bats.className = 'hw-bats'; bats.setAttribute('aria-hidden', 'true');
    bats.innerHTML = BAT.replace('<svg', '<svg class="b1"') + BAT.replace('<svg', '<svg class="b2"')
      + BAT.replace('<svg', '<svg class="b3"') + BAT.replace('<svg', '<svg class="b4"')
      + BAT.replace('<svg', '<svg class="b5"') + BAT.replace('<svg', '<svg class="b6"');
    header.prepend(bats);
  }
  const brand = header.querySelector('.brand');
  if (brand && !brand.querySelector('.hw-pumpkin-hat')) {
    const hat = document.createElement('span');
    hat.className = 'hw-pumpkin-hat'; hat.setAttribute('aria-hidden', 'true'); hat.textContent = '🎃';
    brand.appendChild(hat);
  }
  const kickerText = header.querySelector('.gh-kicker-text');
  if (kickerText) kickerText.textContent = '🎃 From Aspen and Beyond — In Costume 🎃';

  // The ribbon — the concept's "Happy Halloween, Aspen" banner.
  if (!document.querySelector('.gh-halloween-greeting')) {
    const greeting = document.createElement('aside');
    greeting.className = 'gh-halloween-greeting';
    greeting.setAttribute('role', 'note');
    greeting.innerHTML = '<span class="big" aria-hidden="true">🎃</span>'
      + '<span class="hw-ribbon-main"><strong>Happy Halloween, Aspen</strong>'
      + ' <span class="sub">Tonight the Golden Hour wears a costume — same verified guide, after dark.</span></span>'
      + '<span class="big" aria-hidden="true">👻</span>';
    header.after(greeting);
  }

  // The cover in costume: moon, bats, pumpkins, seasonal caption.
  const frame = document.querySelector('.gh-cover-frame');
  if (frame) {
    const tag = frame.querySelector('.gh-cover-tag');
    if (tag) tag.textContent = '🎃 The Cover — Halloween Week 👻';
    const kicker = frame.querySelector('.gh-cover-k');
    if (kicker) kicker.textContent = '🌙 Maroon Bells · By Moonlight';
    const headline = frame.querySelector('.gh-cover-h');
    if (headline) headline.textContent = 'Halloween week, under gold aspens.';
    const moon = document.createElement('div');
    moon.className = 'hw-moon'; moon.setAttribute('aria-hidden', 'true');
    frame.appendChild(moon);
    const heroBats = document.createElement('div');
    heroBats.className = 'hw-hero-bats'; heroBats.setAttribute('aria-hidden', 'true');
    heroBats.innerHTML = BAT.replace('<svg', '<svg class="hb1"') + BAT.replace('<svg', '<svg class="hb2"');
    frame.appendChild(heroBats);
    const pumpkins = document.createElement('div');
    pumpkins.className = 'hw-pumpkins'; pumpkins.setAttribute('aria-hidden', 'true');
    pumpkins.innerHTML = '<span>🎃</span><span class="p2">🎃</span>';
    frame.appendChild(pumpkins);
  }
});
