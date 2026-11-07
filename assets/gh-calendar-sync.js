/* WO-GH-CAL-05: AURELIAN calendar sync adapter.
   Loads calendar/calendar-sync.json — the two-engine AURELIAN export
   (aurelian-local = Around Aspen, aurelian-regional = Regional Events
   Intelligence; those are the only sources) — once, normalizes its events
   into the site's live-layer row shape, drops events that have ended, and
   splits them by source: `local` feeds the core views (homepage week
   section, /upcoming/), `regional` feeds /calendar/.
   Future re-exports replace the JSON file-for-file; nothing here changes. */
(() => {
  "use strict";

  const DENVER = "America/Denver";
  const dayFmt = new Intl.DateTimeFormat("en-CA", { timeZone: DENVER, year: "numeric", month: "2-digit", day: "2-digit" });
  const dayKey = (d) => dayFmt.format(d);
  const todayKey = () => dayKey(new Date());

  // Denver UTC offset (e.g. "-07:00") at a given UTC instant, via Intl.
  function denverOffset(utcDate) {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: DENVER, year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
    }).formatToParts(utcDate);
    const p = {};
    parts.forEach((x) => { p[x.type] = x.value; });
    const asUTC = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second);
    let diff = Math.round((asUTC - utcDate.getTime()) / 60000);
    const sign = diff < 0 ? "-" : "+";
    diff = Math.abs(diff);
    return sign + String(Math.floor(diff / 60)).padStart(2, "0") + ":" + String(diff % 60).padStart(2, "0");
  }

  // "YYYY-MM-DD" (a Denver calendar date) -> ISO instant at Denver midnight.
  function denverMidnightISO(dateStr) {
    return dateStr + "T00:00:00" + denverOffset(new Date(dateStr + "T00:00:00Z"));
  }

  function addDays(dateStr, n) {
    const d = new Date(dateStr + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }

  function cleanText(raw) {
    let t = String(raw == null ? "" : raw);
    t = t.replace(/<\s*br\s*\/?\s*>/gi, "\n")
         .replace(/<\/p\s*>/gi, "\n\n")
         .replace(/<[^>]+>/g, "");
    t = t.replace(/&nbsp;/g, " ")
         .replace(/&amp;/g, "&")
         .replace(/&lt;/g, "<")
         .replace(/&gt;/g, ">")
         .replace(/&quot;/g, '"')
         .replace(/&#0?39;|&apos;/g, "'");
    return t;
  }

  function extractUrl(text) {
    const m = String(text).match(/https?:\/\/[^\s<>"')\]]+/);
    return m ? m[0].replace(/[.,;:]+$/, "") : "";
  }

  // AURELIAN descriptions carry boilerplate lines (header, score, master ID,
  // source/official URL lines). Strip those, keep the editorial text, and
  // surface the first URL as the event's official link.
  function makeBlurb(raw) {
    const text = cleanText(raw);
    const url = extractUrl(text);
    const lines = text.split(/\n+/)
      .map((s) => s.trim())
      .filter(Boolean)
      .filter((s) => !/^AURELIAN EVENT$/i.test(s))
      .filter((s) => !/^MASTER ID:/i.test(s))
      .filter((s) => !/^AURELIAN Score:/i.test(s))
      .filter((s) => !/^Trip Type:/i.test(s))
      .filter((s) => !/^(Official|Source):\s*https?:\/\//i.test(s))
      .map((s) => s.replace(/^(What|Where|Why it matters|Tickets):\s*/i, ""));
    let blurb = lines.join(" ").replace(/\s+/g, " ").trim();
    if (blurb.length > 400) {
      blurb = blurb.slice(0, 400).replace(/\s+\S*$/, "") + "…";
    }
    return { blurb, url };
  }

  function normalize(ev) {
    const made = makeBlurb(ev.description);
    const base = {
      id: ev.id,
      source: ev.source,
      title: ev.title,
      venue: ev.venue || "",
      category: (ev.categories && ev.categories[0]) || "event",
      price_info: "",
      age_policy: "",
      fit_note: "",
      url: ev.url || made.url || "",
      blurb: made.blurb,
      image: ev.image || "",
      slug: "sync-" + String(ev.id).replace(/[^a-zA-Z0-9_-]/g, "-"),
      place_key: ev.place_key || "",
      verified: ev.verified !== false
    };
    if (ev.all_day) {
      // Export carries all-day events as date-only strings. The end date is
      // exclusive when it follows the start date (Google convention); a
      // same-day end means a single-day event.
      const startDate = String(ev.start).slice(0, 10);
      let endDate = String(ev.end || ev.start).slice(0, 10);
      if (endDate > startDate) endDate = addDays(endDate, -1);
      base.all_day = true;
      base.start_day = startDate;
      base.end_day = endDate;
      base.starts_at = denverMidnightISO(startDate);
      base.ends_at = denverMidnightISO(endDate);
    } else {
      base.all_day = false;
      base.starts_at = ev.start;
      base.ends_at = ev.end || ev.start;
      base.start_day = dayKey(new Date(ev.start));
      base.end_day = dayKey(new Date(base.ends_at));
    }
    return base;
  }

  let promise = null;
  function load() {
    if (promise) return promise;
    const self = document.querySelector('script[src$="gh-calendar-sync.js"]');
    const jsonUrl = new URL("../calendar/calendar-sync.json", self.src);
    promise = fetch(jsonUrl, { cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error("Calendar sync feed unavailable");
        return r.json();
      })
      .then((data) => {
        const today = todayKey();
        const rows = (data.events || [])
          .map(normalize)
          .filter((row) => row.end_day >= today)
          .sort((a, b) => (Date.parse(a.starts_at) - Date.parse(b.starts_at)) || a.title.localeCompare(b.title));
        return {
          local: rows.filter((row) => row.source === "aurelian-local"),
          regional: rows.filter((row) => row.source === "aurelian-regional"),
          exported_at: data.exported_at || "",
          counts: data.counts || {}
        };
      });
    return promise;
  }

  window.GHCalSync = { load, dayKey, todayKey };
})();
