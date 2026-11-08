/* WO-GH-UPCOMING-FIX (LUNA build, 2026-11-06): the missing /upcoming/ renderer.
   The page shipped as a static shell whose only data scripts were
   gh-calendar-sync.js (data adapter) and gh-week.js (window math) — nothing
   ever rendered rows, so the baked Oct 31 – Nov 06 window and the empty
   state were all a visitor could ever see.

   Contract (all pre-existing on the page — nothing here renames it):
   - Data: window.GHCalSync.load() -> { local, regional, exported_at, counts }.
     The adapter already drops events whose end_day < today (Denver) and
     sorts soonest-first. `local` (aurelian-local / Around Aspen) feeds this
     page, per the adapter's own header note.
   - Window: PR #30 rolling discovery — start Denver-today; when no start
     falls within 7 days, fall forward to the next 5 upcoming (horizon).
     The Sat–Fri GHWeek preset (WO21) does NOT match the adapter's
     all-events-by-start ordering (an in-progress timed event sorts before
     a multi-day all-day one already under way), so the window is computed
     here on start_day.
   - Markup: the site's own card system (same classes as /events/).
   - Standing rules: ended events never render (the adapter enforces it);
     an event with no verified image gets NO media header (the typographic
     card is the design, not a fallback); cover/range text is generated
     from live data at render time, never hand-written.
   - Failure: if the feed cannot load, the honest empty state stays and
     says so. This script never invents events. */
(() => {
  "use strict";

  const grid = document.querySelector(".gh-event-grid");
  const rangeEl = document.querySelector(".gh-week-range");
  const emptyEl = document.querySelector(".gh-list-empty");
  const ldEl = document.getElementById("gh-event-list");
  if (!grid || !window.GHCalSync) return;

  const DENVER = "America/Denver";
  const dayFmt = new Intl.DateTimeFormat("en-US", {
    timeZone: DENVER, weekday: "short", month: "short", day: "numeric"
  });
  const timeFmt = new Intl.DateTimeFormat("en-US", {
    timeZone: DENVER, hour: "numeric", minute: "2-digit"
  });
  const rangeFmt = new Intl.DateTimeFormat("en-US", {
    timeZone: DENVER, month: "short", day: "numeric"
  });
  const yearFmt = new Intl.DateTimeFormat("en-US", { timeZone: DENVER, year: "numeric" });

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  function addDays(dateStr, n) {
    const d = new Date(dateStr + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }

  function whenLabel(row) {
    if (row.all_day) {
      const a = dayFmt.format(new Date(row.starts_at));
      if (row.end_day && row.end_day !== row.start_day) {
        return a + " – " + dayFmt.format(new Date(row.ends_at)) + " · All day";
      }
      return a + " · All day";
    }
    return dayFmt.format(new Date(row.starts_at)) + " · " +
      timeFmt.format(new Date(row.starts_at)) + " MT";
  }

  function rangeLabel(rows, horizon) {
    if (!rows.length) return "";
    const byTime = [...rows].sort((a,b)=>Date.parse(a.starts_at)-Date.parse(b.starts_at));
    const first = byTime[0], last = byTime[byTime.length - 1];
    const a = rangeFmt.format(new Date(first.starts_at));
    const b = rangeFmt.format(new Date((last.all_day ? last.ends_at : last.starts_at)));
    const yr = yearFmt.format(new Date(last.starts_at));
    return (horizon ? "Coming up · " : "") +
      (a === b ? a : a + " – " + b) + ", " + yr + " · MT";
  }

  function cardHTML(row) {
    const media = row.image
      ? '<figure class="gh-card-media"><img class="gh-artwork" alt="' +
        esc(row.title) + ' — official event imagery" loading="lazy" decoding="async" src="../' +
        esc(row.image) + '"/></figure>'
      : "";
    const cls = row.image ? "gh-event-card gh-card has-media" : "gh-event-card gh-card gh-typographic";
    const detail = window.GHCalSync.detailUrl(row);
    const link = '<div class="gh-card-actions"><a class="btn" href="' + esc(detail) + '">Event details →</a></div>';
    const blurb = row.blurb ? "<p>" + esc(row.blurb) + "</p>" : "";
    const venue = row.venue ? '<p class="gh-card-venue">' + esc(row.venue) + "</p>" : "";
    return '<article class="' + cls + '" data-starts="' + esc(row.starts_at) + '">' +
      (media ? '<a class="gh-card-image-link" href="' + esc(detail) + '" aria-label="' + esc(row.title) + ' — event details">' + media + '</a>' : "") +
      '<div class="gh-card-body">' +
      '<p class="gh-card-kicker">' + esc(row.category || "event") + "</p>" +
      "<time datetime=\"" + esc(row.starts_at) + "\">" + esc(whenLabel(row)) + "</time>" +
      '<h2><a class="gh-card-link" href="' + esc(detail) + '">' + esc(row.title) + "</a></h2>" +
      venue + blurb + link +
      "</div></article>";
  }

  function jsonLd(rows) {
    if (!ldEl) return;
    const items = rows.map((row, i) => ({
      "@type": "ListItem",
      position: i + 1,
      item: {
        "@type": "Event",
        name: row.title,
        startDate: row.starts_at,
        endDate: row.ends_at || row.starts_at,
        location: row.venue ? { "@type": "Place", name: row.venue } : undefined,
        url: window.GHCalSync.canonicalUrl(row)
      }
    }));
    ldEl.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: grid.dataset.ghScope === 'all' ? "Events — The Golden Hour" : "This Week — The Golden Hour",
      itemListElement: items
    });
  }

  grid.replaceChildren();
  if (rangeEl) rangeEl.textContent = '';
  if (emptyEl) { emptyEl.hidden = false; emptyEl.textContent = 'Finding what’s on…'; }
  jsonLd([]);
  let rendered='', pending=false, selected='all';
  const filterBox=grid.dataset.ghScope==='all'?document.querySelector('.gh-filters'):null;
  if(filterBox)filterBox.addEventListener('click',event=>{const button=event.target.closest('button[data-filter]');if(button){selected=button.dataset.filter;refresh();}});
  async function refresh(){
    if(pending)return;pending=true;
    try {
    const data=await window.GHCalSync.load();
    const today = window.GHCalSync.todayKey();
    const all = grid.dataset.ghScope === 'all';
    const rows = (all ? [...data.local,...data.regional] : data.local || []).filter((r) => r.verified === true && r.end_day >= today).sort(window.GHCalSync.compare);
    const inWeek = rows.filter((r) => r.start_day <= addDays(today, 6));
    const horizon = inWeek.length === 0;
    if(filterBox){
      const categories=[...new Set(rows.map(row=>row.category))].filter(value=>value&&value!=='event');
      const filters=[['all','All'],...categories.map(value=>[value,value.charAt(0).toUpperCase()+value.slice(1)])];
      if(!filters.some(([value])=>value===selected))selected='all';
      filterBox.innerHTML=filters.map(([value,label])=>'<button type="button" data-filter="'+esc(value)+'" aria-pressed="'+(value===selected)+'">'+esc(label)+'</button>').join('');
    }
    const show = all ? rows.filter(row=>selected==='all'||row.category===selected) : horizon ? rows.slice(0, 5) : inWeek;

    const signature=JSON.stringify([today,selected,show]);if(signature===rendered)return;rendered=signature;
    if (rangeEl && show.length) rangeEl.textContent = rangeLabel(show, horizon);
    if (show.length) {
      grid.innerHTML = show.map(cardHTML).join("");
      if (emptyEl) emptyEl.hidden = true;
      jsonLd(show);
    } else {
      grid.replaceChildren();if(emptyEl)emptyEl.hidden=false;
      if (rangeEl) rangeEl.textContent = '';
      if (emptyEl) emptyEl.textContent = 'Explore the Calendar for later dates.';
      jsonLd([]);
    }
  } catch (_) {
    rendered='';
    grid.replaceChildren();jsonLd([]);
    if (rangeEl) rangeEl.textContent = '';
    if (emptyEl) {emptyEl.hidden = false;emptyEl.textContent = 'The calendar is temporarily unavailable. Please try again.';}
    /* Feed unavailable: the page's honest empty state remains, worded as-is.
       Nothing is fabricated to fill the grid. */
  } finally {pending=false;}
  }
  refresh();setInterval(refresh,60000);addEventListener('pageshow',refresh);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
})();
