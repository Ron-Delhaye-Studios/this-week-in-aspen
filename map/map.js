/* Golden Hour event map — date-intelligent rendering.
   Reads events.json (built by build_map.py). No build step needed for the page itself.
   Date logic runs client-side so "Today / In N days" never goes stale. */
(function () {
  "use strict";

  var DENVER = "America/Denver";
  var state = { range: "7", cats: null, includePast: false };

  function denverParts(iso) {
    var d = new Date(iso);
    var fmt = new Intl.DateTimeFormat("en-US", {
      timeZone: DENVER, weekday: "short", month: "short", day: "numeric",
      hour: "numeric", minute: "2-digit", hour12: true
    });
    return { date: d, fmt: fmt };
  }
  function dayKey(iso) {
    var p = new Intl.DateTimeFormat("en-CA", {
      timeZone: DENVER, year: "numeric", month: "2-digit", day: "2-digit"
    }).format(new Date(iso));
    return p; // YYYY-MM-DD in Denver
  }
  function todayKey() { return dayKey(new Date().toISOString()); }
  function diffDays(iso) {
    var a = new Date(todayKey() + "T12:00:00");
    var b = new Date(dayKey(iso) + "T12:00:00");
    return Math.round((b - a) / 86400000);
  }
  function relTag(iso) {
    var n = diffDays(iso);
    if (n < 0) return null;
    if (n === 0) return "Today";
    if (n === 1) return "Tomorrow";
    return "In " + n + " days";
  }
  function imminence(iso) {
    var n = diffDays(iso);
    if (n <= 0) return "now";
    if (n <= 7) return "week";
    if (n <= 30) return "month";
    return "later";
  }
  var COLORS = { now: "#b98a1d", week: "#103d60", month: "#7a8ba0", later: "#c9c2b4", past: "#d8d2c4" };

  function prettyDate(iso) {
    return new Intl.DateTimeFormat("en-US", {
      timeZone: DENVER, weekday: "long", month: "long", day: "numeric"
    }).format(new Date(iso));
  }
  function prettyTime(iso) {
    return new Intl.DateTimeFormat("en-US", {
      timeZone: DENVER, hour: "numeric", minute: "2-digit", hour12: true
    }).format(new Date(iso)).toUpperCase();
  }

  function popupHtml(ev) {
    var tag = relTag(ev.starts_at);
    var tagHtml = tag ? '<span class="ev-rel' + (diffDays(ev.starts_at) <= 1 ? " soon" : "") + '">' +
      tag.replace(/&/g, "&amp;") + "</span>" : "";
    var when = '<p class="ev-date">' + prettyDate(ev.starts_at) + tagHtml + "</p>" +
      '<p class="ev-time">' + prettyTime(ev.starts_at) + "</p>";
    var meta = (ev.venue || "") +
      (ev.price_info ? " · " + ev.price_info : "") +
      (ev.age_policy ? " · " + ev.age_policy : "");
    var link = ev.url ? '<p><a href="' + ev.url.replace(/"/g, "") +
      '" target="_blank" rel="noopener">Details &rarr;</a></p>' : "";
    var xlink = '<p><a href="../upcoming/#ev-' + String(ev.id).replace(/"/g, "") +
      '">Event details &rarr;</a></p>';
    var blurb = ev.blurb ? '<p class="meta">' + ev.blurb.replace(/</g, "&lt;") + "</p>" : "";
    // __GH_IMGROOT__: page-relative prefix for photos ("../" on the live page).
    // null = this context has no photo files (e.g. chat preview) -> skip photos.
    var imgRoot = window.__GH_IMGROOT__ !== undefined ? window.__GH_IMGROOT__ : "../";
    var photo = (imgRoot !== null && ev.image) ? '<img class="ev-photo" src="' + imgRoot +
      String(ev.image).replace(/"/g, "") + '" alt="" loading="lazy">' : "";
    return photo + when + "<h3>" + String(ev.title).replace(/</g, "&lt;") + "</h3>" +
      '<p class="meta">' + String(meta).replace(/</g, "&lt;") + "</p>" + blurb + xlink + link;
  }

  function inRange(ev) {
    var n = diffDays(ev.starts_at);
    if (n < 0) return state.includePast;
    switch (state.range) {
      case "today": return n === 0;
      case "weekend": {
        var dow = new Date(ev.starts_at).toLocaleString("en-US",
          { timeZone: DENVER, weekday: "short" });
        return n <= 7 && (dow === "Fri" || dow === "Sat" || dow === "Sun");
      }
      case "7": return n <= 7;
      case "30": return n <= 30;
      case "all": return true;
      case "past": return true;
      default: return n <= 7;
    }
  }

  var map = L.map("map").setView([39.0, -105.9], 7);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18, attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);
  var cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 48,
    iconCreateFunction: function (c) {
      var n = c.getChildCount();
      var size = n < 5 ? 40 : n < 15 ? 48 : 56;
      return L.divIcon({
        html: '<span style="display:flex;align-items:center;justify-content:center;width:' + size +
          'px;height:' + size + 'px;border-radius:50%;background:#103d60;color:#fff;' +
          'font:700 15px Inter,sans-serif;border:3px solid #fff;' +
          'box-shadow:0 2px 8px rgba(0,0,0,.35)">' + n + '</span>',
        className: "gh-cluster", iconSize: [size, size]
      });
    } });
  map.addLayer(cluster);

  function dot(color, today) {
    var d = today ? 24 : 20;
    var glow = today
      ? "box-shadow:0 0 0 4px rgba(185,138,29,.35),0 2px 8px rgba(0,0,0,.45)"
      : "box-shadow:0 0 0 3px rgba(255,255,255,.65),0 2px 6px rgba(0,0,0,.4)";
    return L.divIcon({
      className: "gh-dot" + (today ? " today" : ""),
      html: '<span style="display:block;width:' + d + 'px;height:' + d + 'px;border-radius:50%;' +
        "background:" + color + ";border:3px solid #fff;" + glow + '"></span>',
      iconSize: [d, d], iconAnchor: [d / 2, d / 2]
    });
  }

  var allEvents = [];

  function render() {
    cluster.clearLayers();
    var shown = 0;
    allEvents.forEach(function (ev) {
      if (state.cats && ev.category && state.cats.indexOf(ev.category) < 0) return;
      if (!inRange(ev)) return;
      var n = diffDays(ev.starts_at);
      var color = n < 0 ? COLORS.past : COLORS[imminence(ev.starts_at)];
      var m = L.marker([ev.lat, ev.lng], { icon: dot(color, n === 0) });
      m.bindPopup(popupHtml(ev), { maxWidth: 300 });
      cluster.addLayer(m);
      shown++;
    });
    var label = shown + (shown === 1 ? " event" : " events");
    if (state.range === "past" || state.includePast) label += " (including past)";
    document.getElementById("count").textContent = label + " on the map.";
  }

  function buildCatChips() {
    var cats = {};
    allEvents.forEach(function (ev) { if (ev.category) cats[ev.category] = 1; });
    var row = document.getElementById("catrow");
    Object.keys(cats).sort().forEach(function (c) {
      var b = document.createElement("button");
      b.className = "chip"; b.textContent = c; b.setAttribute("aria-pressed", "false");
      b.onclick = function () {
        var on = b.getAttribute("aria-pressed") === "true";
        b.setAttribute("aria-pressed", String(!on));
        var active = Array.prototype.slice.call(row.querySelectorAll('[aria-pressed="true"]'))
          .map(function (x) { return x.textContent; });
        state.cats = active.length ? active : null;
        render();
      };
      row.appendChild(b);
    });
  }

  document.querySelectorAll("#controls .chip").forEach(function (b) {
    b.addEventListener("click", function () {
      var r = b.getAttribute("data-range");
      if (r === "past") {
        state.includePast = !state.includePast;
        b.setAttribute("aria-pressed", String(state.includePast));
      } else {
        document.querySelectorAll('#controls .chip[data-range]').forEach(function (x) {
          if (x.getAttribute("data-range") !== "past") x.setAttribute("aria-pressed", "false");
        });
        b.setAttribute("aria-pressed", "true");
        state.range = r;
      }
      render();
    });
  });

  fetch("events.json").then(function (r) { return r.json(); }).then(function (data) {
    allEvents = data.filter(function (ev) {
      return typeof ev.lat === "number" && typeof ev.lng === "number";
    });
    buildCatChips();
    render();
    // Deep link: map/?event=<uuid> focuses that pin and opens its card.
    var focusId = null;
    try { focusId = new URLSearchParams(window.location.search).get("event"); } catch (e) {}
    var focused = false;
    if (focusId) {
      var target = null;
      allEvents.forEach(function (ev) { if (String(ev.id) === focusId) target = ev; });
      if (target) {
        map.setView([target.lat, target.lng], 13);
        // re-render one marker outside the cluster so its popup can open
        var m = L.marker([target.lat, target.lng],
          { icon: dot(diffDays(target.starts_at) < 0 ? COLORS.past : COLORS[imminence(target.starts_at)]) });
        m.bindPopup(popupHtml(target), { maxWidth: 300 }).addTo(map).openPopup();
        focused = true;
      }
    }
    if (!focused && allEvents.length) {
      var pts = allEvents.filter(inRange).map(function (ev) { return [ev.lat, ev.lng]; });
      if (pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.15));
    }
  }).catch(function () {
    document.getElementById("count").textContent = "Event data is not loaded yet.";
  });
})();
