/* Synchronous head script: theme is resolved before first paint. */
(() => {
  'use strict';
  const base = new URL('../', document.currentScript.src);
  const device = matchMedia('(prefers-color-scheme: dark)');
  let manual;
  try { manual = sessionStorage.getItem('gh-theme'); } catch (_) {}
  const apply = () => {
    const value = manual === 'dark' || manual === 'light' ? manual : device.matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = value;
    const button = document.querySelector('.gh-theme-toggle');
    if (button) {
      button.textContent = value === 'dark' ? 'Light mode ☀' : 'Dark mode ☾';
      button.setAttribute('aria-pressed', String(value === 'dark'));
      button.setAttribute('aria-label', 'Dark theme');
    }
    const manifest = document.querySelector('link[rel="manifest"]');
    if (manifest) manifest.href = new URL(value === 'dark' ? 'manifest-dark.json' : 'manifest.json', base).href;
    document.querySelectorAll('meta[name="theme-color"]').forEach(m => {
      m.content = value === 'dark' ? '#0b1526' : '#faf4e8'; m.removeAttribute('media');
    });
  };
  apply();
  device.addEventListener('change', apply);
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    document.querySelector('.gh-theme-toggle')?.addEventListener('click', () => {
      manual = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      try { sessionStorage.setItem('gh-theme', manual); } catch (_) {}
      apply();
    });
    const format = options => new Intl.DateTimeFormat('en-US', {timeZone:'America/Denver', ...options});
    const date = document.querySelector('.gh-date');
    const updateDate = () => { if (date) { date.textContent = format({weekday:'short',month:'short',day:'numeric',year:'numeric'}).format(new Date()); date.dateTime = new Date().toISOString(); } };
    updateDate(); setInterval(updateDate, 60000);
    const pill = document.querySelector('.gh-weather');
    let last;
    try {
      last = JSON.parse(localStorage.getItem('gh-weather'));
      if (!Number.isFinite(last?.temp) || !Number.isFinite(last?.code) || !Number.isFinite(Date.parse(last?.time))) last = null;
    } catch (_) {}
    const condition = code => code === 0 ? 'Clear' : code <= 3 ? 'Cloudy' : code <= 48 ? 'Fog' : code <= 67 ? 'Rain' : code <= 77 ? 'Snow' : code <= 82 ? 'Showers' : code <= 86 ? 'Snow showers' : 'Thunderstorms';
    const showWeather = stale => {
      if (!pill) return;
      if (!last) { pill.textContent = 'Aspen · Weather unavailable'; return; }
      const time = format({hour:'numeric',minute:'2-digit',month:'short',day:'numeric'}).format(new Date(last.time));
      pill.textContent = `Aspen · ${Math.round(last.temp)}°F · ${condition(last.code)}${stale ? ' · Last reading ' + time + ' MT' : ''}`;
      pill.title = `Open-Meteo · Observed ${time} MT`;
    };
    const weather = async () => {
      showWeather(true);
      try {
        const response = await fetch('https://api.open-meteo.com/v1/forecast?latitude=39.1911&longitude=-106.8175&current=temperature_2m,weather_code&temperature_unit=fahrenheit&timezone=UTC', {signal:AbortSignal.timeout(10000)});
        if (!response.ok) throw new Error('Weather unavailable');
        const {current} = await response.json();
        if (!Number.isFinite(current?.temperature_2m) || !Number.isFinite(current?.weather_code) || !Number.isFinite(Date.parse(current?.time + 'Z'))) throw new Error('Invalid weather');
        last = {temp:current.temperature_2m, code:current.weather_code, time:current.time + 'Z'};
        try { localStorage.setItem('gh-weather', JSON.stringify(last)); } catch (_) {}
        showWeather(false);
      } catch (_) { showWeather(true); }
    };
    weather(); setInterval(weather, 30 * 60000);
    // A cached list must never advertise yesterday's events as upcoming.
    const key = d => {
      const parts = Object.fromEntries(format({year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(d).map(p => [p.type,p.value]));
      return `${parts.year}-${parts.month}-${parts.day}`;
    };
    const prune = () => {
      const cutoff = key(new Date());
      document.querySelectorAll('.gh-event-card[data-starts]').forEach(card => { card.hidden = key(new Date(card.dataset.starts)) < cutoff; });
      const empty = document.querySelector('.gh-list-empty');
      if (empty) empty.hidden = !!document.querySelector('.gh-event-card:not([hidden])');
      const ld = document.querySelector('#gh-event-list');
      if (ld) {
        const list = JSON.parse(ld.textContent);
        list.itemListElement = list.itemListElement.filter(item => key(new Date(item.item.startDate)) >= cutoff).map((item,i) => ({...item,position:i+1}));
        ld.textContent = JSON.stringify(list);
      }
    };
    prune(); setInterval(prune,60000);
    document.addEventListener('click', async e => {
      const button = e.target.closest('.gh-copy'); if (!button) return;
      try { await navigator.clipboard.writeText(button.dataset.copy); button.textContent = 'Copied ✓'; }
      catch (_) { button.textContent = 'Copy unavailable'; }
    });
    if ('serviceWorker' in navigator) navigator.serviceWorker.register(new URL('sw.js',base),{scope:base.pathname}).catch(() => {});
  });
})();
