/* Golden Hour calendar — Google-style month grid.
   Renders events.json (same live-layer rows as Upcoming/Map) into a month
   view with event chips, "+N more" overflow, and detail popups. */
(function () {
  "use strict";

  var DENVER = "America/Denver";
  var MAX_CHIPS = 3;

  var CAT_STYLE = {
    music:    ["#e1bee7", "#6a1b9a"],
    arts:     ["#f8bbd0", "#ad1457"],
    outdoors: ["#c8e6c9", "#1b5e20"],
    family:   ["#fff9c4", "#e65100"],
    dining:   ["#ffe0b2", "#bf360c"],
    comedy:   ["#b3e5fc", "#0277bd"],
    speakers: ["#c5cae9", "#283593"],
    dance:    ["#d7ccc8", "#4e342e"]
  };
  function catStyle(cat) {
    return CAT_STYLE[cat] || ["#e0e0e0", "#424242"];
  }

  var dayKeyFmt = new Intl.DateTimeFormat("en-CA", { timeZone: DENVER, year: "numeric", month: "2-digit", day: "2-digit" });
  var timeFmt = new Intl.DateTimeFormat("en-US", { timeZone: DENVER, hour: "numeric", minute: "2-digit", hour12: true });
  var fullDateFmt = new Intl.DateTimeFormat("en-US", { timeZone: DENVER, weekday: "long", month: "long", day: "numeric" });

  function denverKey(iso) { return dayKeyFmt.format(new Date(iso)); }
  function chipTime(iso) {
    return timeFmt.format(new Date(iso)).replace(":00 ", " ").replace(" ", "").toLowerCase();
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function denverToday() {
    var parts = new Intl.DateTimeFormat("en-CA", { timeZone: DENVER, year: "numeric", month: "numeric", day: "numeric" })
      .formatToParts(new Date());
    var p = {};
    parts.forEach(function (x) { p[x.type] = +x.value; });
    return { y: p.year, m: p.month - 1, d: p.day };
  }

  var T = denverToday();
  var TODAY_KEY = T.y + "-" + pad2(T.m + 1) + "-" + pad2(T.d);
  var viewY = T.y, viewM = T.m;
  var minIdx = T.y * 12 + T.m;
  var maxIdx = minIdx + 4;

  var eventsByDay = {};
  var eventsById = {};
  var selectedKey = null; // set once TODAY_KEY exists

  function relLabel(iso) {
    var now = new Date();
    var t = new Date(now.toLocaleString("en-US", { timeZone: DENVER }));
    t.setHours(0, 0, 0, 0);
    var d = new Date(new Date(iso).toLocaleString("en-US", { timeZone: DENVER }));
    d.setHours(0, 0, 0, 0);
    var diff = Math.round((d - t) / 864e5);
    if (diff < 0) return null;
    if (diff === 0) return "Today";
    if (diff === 1) return "Tomorrow";
    return "In " + diff + " days";
  }

  function chipHTML(ev) {
    var st = catStyle(ev.category);
    var cls = denverKey(ev.starts_at) === TODAY_KEY ? "gcal-chip istoday" : "gcal-chip";
    return '<button class="' + cls + '" data-ev="' + esc(ev.id) + '"' +
      ' style="background:' + st[0] + ';color:' + st[1] + '">' +
      '<span class="ct">' + esc(chipTime(ev.starts_at)) + "</span> " + esc(ev.title) + "</button>";
  }

  var MONTHS = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];

  function pad2(n) { return String(n).padStart(2, "0"); }

  function render() {
    var title = document.getElementById("gcal-title");
    title.textContent = MONTHS[viewM] + " " + viewY;

    var idx = viewY * 12 + viewM;
    document.getElementById("gcal-prev").disabled = idx <= minIdx;
    document.getElementById("gcal-next").disabled = idx >= maxIdx;

    var grid = document.getElementById("gcal-grid");
    var html = "";
    // UTC arithmetic keeps the grid aligned regardless of viewer timezone;
    // event keys are always Denver dates.
    var lead = new Date(Date.UTC(viewY, viewM, 1)).getUTCDay(); // Sunday start
    var base = Date.UTC(viewY, viewM, 1 - lead);
    for (var i = 0; i < 42; i++) {
      var d = new Date(base + i * 864e5);
      var key = d.getUTCFullYear() + "-" + pad2(d.getUTCMonth() + 1) + "-" + pad2(d.getUTCDate());
      var inMonth = d.getUTCMonth() === viewM;
      var isToday = d.getUTCFullYear() === T.y && d.getUTCMonth() === T.m && d.getUTCDate() === T.d;
      var evs = (eventsByDay[key] || []).slice().sort(function (a, b) {
        return new Date(a.starts_at) - new Date(b.starts_at);
      });
      html += '<div class="gcal-day' + (inMonth ? "" : " dim") + (isToday ? " istoday" : "") + (key === selectedKey ? " selected" : "") + '" data-day="' + key + '">';
      html += '<div class="gcal-daynum' + (isToday ? " today" : "") + '">' + d.getUTCDate() + "</div>";
      var shown = evs.slice(0, MAX_CHIPS);
      shown.forEach(function (ev) { html += chipHTML(ev); });
      if (evs.length > MAX_CHIPS) {
        html += '<button class="gcal-more" data-day="' + key + '">' + (evs.length - MAX_CHIPS) + " more</button>";
      }
      html += "</div>";
    }
    grid.innerHTML = html;
    renderDayPanel();
  }

  var panelDayFmt = new Intl.DateTimeFormat("en-US", { timeZone: DENVER, weekday: "long", month: "long", day: "numeric" });

  function agendaRowHTML(ev) {
    var st = catStyle(ev.category);
    return '<button class="gcal-arow" data-ev="' + esc(ev.id) + '" style="border-left-color:' + st[1] + '">' +
      '<span class="gcal-atime">' + esc(chipTime(ev.starts_at)) + "</span>" +
      '<span class="gcal-abody"><strong>' + esc(ev.title) + "</strong>" +
      '<span class="gcal-avenue">' + esc(ev.venue) + "</span></span></button>";
  }

  function selectDay(key, scroll) {
    selectedKey = key;
    render();
    if (scroll) {
      var p = document.getElementById("gcal-agenda");
      if (p) p.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function renderDayPanel() {
    var box = document.getElementById("gcal-agenda");
    if (!box) return;
    var key = selectedKey || TODAY_KEY;
    var evs = (eventsByDay[key] || []).slice().sort(function (a, b) { return new Date(a.starts_at) - new Date(b.starts_at); });
    var label = evs.length ? panelDayFmt.format(new Date(evs[0].starts_at))
      : panelDayFmt.format(new Date(key + "T12:00:00"));
    var html = '<div class="gcal-phead"><h3>' + esc(label) + "</h3>" +
      (key === TODAY_KEY ? '<span class="gcal-arel">Today</span>' : "") +
      '<span class="gcal-pcount">' + evs.length + (evs.length === 1 ? " event" : " events") + "</span></div>";
    if (evs.length) evs.forEach(function (ev) { html += agendaRowHTML(ev); });
    else html += '<p class="empty">No events this day.</p>';
    box.innerHTML = html;
  }

  // Desktop hover preview: floating card appended to body (never clipped).
  var tipEl = null;
  function showTip(chip) {
    hideTip();
    var ev = eventsById[chip.getAttribute("data-ev")];
    if (!ev) return;
    tipEl = document.createElement("div");
    tipEl.className = "gcal-tip";
    tipEl.innerHTML = "<strong>" + esc(ev.title) + "</strong><span>" +
      esc(chipTime(ev.starts_at)) + " · " + esc(ev.venue) + "</span>";
    document.body.appendChild(tipEl);
    var r = chip.getBoundingClientRect();
    var tw = Math.min(260, window.innerWidth * 0.7);
    tipEl.style.width = tw + "px";
    var x = Math.max(8, Math.min(r.left + r.width / 2 - tw / 2, window.innerWidth - tw - 8));
    var y = r.top + window.scrollY - tipEl.offsetHeight - 10;
    if (y < window.scrollY + 8) y = r.bottom + window.scrollY + 10;
    tipEl.style.left = x + "px";
    tipEl.style.top = y + "px";
  }
  function hideTip() { if (tipEl) { tipEl.remove(); tipEl = null; } }

  function openEvent(id) {
    var ev = eventsById[id];
    if (!ev) return;
    var st = catStyle(ev.category);
    var rel = relLabel(ev.starts_at);
    var meta = [ev.price_info, ev.age_policy].filter(Boolean).map(esc).join(" · ");
    var html = '<div class="gcal-modal-card">';
    html += '<button class="gcal-x" aria-label="Close">&times;</button>';
    if (ev.image) {
      html += '<img class="gcal-photo" src="../' + esc(ev.image) + '" alt="' + esc(ev.title) + '" loading="lazy">';
    }
    html += '<div class="gcal-modal-body">';
    html += '<p class="gcal-cat" style="background:' + st[0] + ";color:" + st[1] + '">' + esc(ev.category || "event") + "</p>";
    html += "<h3>" + esc(ev.title) + "</h3>";
    html += '<p class="gcal-when"><strong>' + esc(fullDateFmt.format(new Date(ev.starts_at))) + "</strong> · " +
      esc(chipTime(ev.starts_at)) + (rel ? ' · <span class="gcal-rel">' + esc(rel) + "</span>" : "") + "</p>";
    html += '<p class="gcal-venue">' + esc(ev.venue) + "</p>";
    if (meta) html += '<p class="gcal-meta">' + meta + "</p>";
    if (ev.blurb) html += '<p class="gcal-blurb">' + esc(ev.blurb) + "</p>";
    if (ev.fit_note) html += '<p class="gcal-fit">' + esc(/^for\s/i.test(ev.fit_note) ? ev.fit_note : "For: " + ev.fit_note) + "</p>";
    html += '<div class="gcal-links">';
    if (ev.url) html += '<a href="' + esc(ev.url) + '" target="_blank" rel="noopener">Official event page ↗</a>';
    html += '<a href="../map/?event=' + esc(ev.id) + '">View on map ↗</a>';
    html += '<a href="../upcoming/#ev-' + esc(ev.id) + '">Event details ↗</a>';
    html += "</div></div></div>";
    showModal(html);
  }

  function showModal(inner) {
    closeModal();
    var ov = document.createElement("div");
    ov.className = "gcal-overlay";
    ov.innerHTML = inner;
    ov.addEventListener("click", function (e) {
      if (e.target === ov || e.target.classList.contains("gcal-x")) closeModal();
    });
    document.body.appendChild(ov);
    document.addEventListener("keydown", escClose);
  }
  function escClose(e) { if (e.key === "Escape") closeModal(); }
  function closeModal() {
    document.querySelectorAll(".gcal-overlay").forEach(function (x) { x.remove(); });
    document.removeEventListener("keydown", escClose);
  }

  function nav(delta) {
    var idx = viewY * 12 + viewM + delta;
    if (idx < minIdx || idx > maxIdx) return;
    viewY = Math.floor(idx / 12);
    viewM = idx % 12;
    var prefix = viewY + "-" + pad2(viewM + 1);
    if (!selectedKey || selectedKey.slice(0, 7) !== prefix) {
      selectedKey = (TODAY_KEY.slice(0, 7) === prefix) ? TODAY_KEY : prefix + "-01";
    }
    render();
  }

  document.addEventListener("click", function (e) {
    var chip = e.target.closest(".gcal-chip,.gcal-arow");
    if (chip) { openEvent(chip.getAttribute("data-ev")); return; }
    var more = e.target.closest(".gcal-more");
    if (more) { selectDay(more.getAttribute("data-day"), true); return; }
    var day = e.target.closest(".gcal-day");
    if (day) { selectDay(day.getAttribute("data-day"), false); }
  });
  if (window.matchMedia("(hover:hover)").matches) {
    document.addEventListener("mouseover", function (e) {
      var c = e.target.closest(".gcal-chip");
      if (c) showTip(c);
    });
    document.addEventListener("mouseout", function (e) {
      var c = e.target.closest(".gcal-chip");
      if (c && (!e.relatedTarget || !c.contains(e.relatedTarget))) hideTip();
    });
  }
  document.getElementById("gcal-prev").addEventListener("click", function () { nav(-1); });
  document.getElementById("gcal-next").addEventListener("click", function () { nav(1); });
  document.getElementById("gcal-today").addEventListener("click", function () {
    viewY = T.y; viewM = T.m; render();
  });

  fetch("events.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (evs) {
      evs.forEach(function (ev) {
        eventsById[ev.id] = ev;
        var k = denverKey(ev.starts_at);
        (eventsByDay[k] = eventsByDay[k] || []).push(ev);
      });
      if (!selectedKey) selectedKey = TODAY_KEY;
      render();
    })
    .catch(function () {
      document.getElementById("gcal-grid").innerHTML =
        '<p class="empty">Could not load events — please refresh.</p>';
    });
})();
