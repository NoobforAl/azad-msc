/* azad-deck.js: shared reveal.js boot for every Azad deck.
 * - Injects the footer (course tag at the start edge, "07 / 18" at the end edge) on content slides.
 * - Injects the corner logo and the title-slide logo tile. data-logo may name .svg or .png:
 *   if the .svg is missing the matching .png is used, and if neither exists a dashed placeholder shows.
 * - Initializes Reveal with the design-system settings (1920x1080, RTL from <html dir>).
 * - Adds a small toolbar (bottom corner, appears on hover or key T): transition picker, animations on/off,
 *   speed, fullscreen, PDF export. Keys: A = animations on/off, T = toolbar.
 * - PDF: the toolbar button reloads the deck in print mode and opens the print dialog (choose "Save as PDF",
 *   margins: none, background graphics: on). Headless export and PPTX: `make pdf` / `make pptx`.
 *
 * Usage, at the end of <body>:
 *   <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
 *   <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js"></script>
 *   <script src="<rel>/_shared/theme/azad-deck.js" data-course="Advanced OS · 00 Setup"
 *           data-logo="<rel>/_shared/brand/azad-logo.svg"></script>
 */
(function () {
  "use strict";
  const me = document.currentScript;
  const course = me.dataset.course || "";
  const logoSrc = me.dataset.logo || "";
  const siteRoot = new URL("../../", me.src);   // <site root>/_shared/theme/azad-deck.js -> <site root>/
  // This deck's course page, e.g. <root>/term-1/advanced-operating-systems/ (null if the path is unexpected)
  const courseUrl = (() => {
    const here = decodeURIComponent(location.pathname), base = decodeURIComponent(siteRoot.pathname);
    const seg = here.startsWith(base) ? here.slice(base.length).split("/") : [];
    return /^term-\d+$/.test(seg[0] || "") && seg[1] ? new URL(seg[0] + "/" + seg[1] + "/", siteRoot).href : null;
  })();
  const rtl = document.documentElement.dir === "rtl";
  const params = new URLSearchParams(location.search);
  const printing = params.has("print-pdf");
  const exporting = params.has("export");   // used by _shared/tools/export_deck.py: final state, no chrome, no motion
  const toFa = (s) => s; // slide numbers stay Latin digits (design system section 9)

  const store = {
    get(k, d) { try { const v = localStorage.getItem("azad." + k); return v === null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("azad." + k, v); } catch (e) { /* private mode: setting just won't persist */ } },
  };

  const slides = Array.from(document.querySelectorAll(".reveal .slides > section"));
  const total = slides.length;
  const pad = (n) => String(n).padStart(2, "0");
  const noChrome = (s) =>
    s.classList.contains("layout-title") || s.classList.contains("layout-section");
  const t = (en, fa) => (rtl ? fa : en);

  let resolvedLogo = "";

  function addLogo(section) {
    if (resolvedLogo) {
      const el = document.createElement("img");
      el.className = "corner-logo";
      el.src = resolvedLogo;
      el.alt = "Islamic Azad University";
      section.appendChild(el);
    } else {
      const el = document.createElement("div");
      el.className = "corner-logo logo-placeholder";
      el.textContent = t("[University logo]", "[لوگوی دانشگاه]");
      section.appendChild(el);
    }
  }

  function decorate() {
    slides.forEach((s, i) => {
      if (noChrome(s)) return;
      const f = document.createElement("div");
      f.className = "footer";
      f.innerHTML = `<span class="course"></span><span class="slide-no">${toFa(pad(i + 1))} / ${pad(total)}</span>`;
      f.querySelector(".course").textContent = course;
      s.appendChild(f);
      addLogo(s);
    });
    // Title slide logo tile
    document.querySelectorAll(".layout-title .logo-tile").forEach((tile) => {
      tile.innerHTML = "";
      if (resolvedLogo) {
        const el = document.createElement("img");
        el.src = resolvedLogo; el.alt = "Islamic Azad University";
        tile.appendChild(el);
      } else {
        const el = document.createElement("div");
        el.className = "logo-placeholder";
        el.textContent = t("[University logo]", "[لوگوی دانشگاه]");
        tile.appendChild(el);
      }
    });
  }

  /* ---------- toolbar ---------- */
  const TRANSITIONS = ["fade", "slide", "convex", "concave", "zoom", "none"];

  function toast(msg) {
    const el = document.createElement("div");
    el.className = "azad-toast"; el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3600);
  }

  function setAnimations(on) {
    document.documentElement.classList.toggle("no-anim", !on);
    store.set("anim", on ? "on" : "off");
    const b = document.querySelector('.azad-bar [data-act="anim"]');
    if (b) { b.setAttribute("aria-pressed", String(on)); b.textContent = on ? t("Animations: on", "انیمیشن: روشن") : t("Animations: off", "انیمیشن: خاموش"); }
  }

  function exportPdf() {
    const u = new URL(location.href);
    u.searchParams.set("print-pdf", "");
    u.searchParams.set("autoprint", "1");
    location.href = u.toString();
  }

  function buildToolbar() {
    const zone = document.createElement("div"); zone.className = "azad-hot-zone";
    const bar = document.createElement("div"); bar.className = "azad-bar"; bar.setAttribute("role", "toolbar");
    bar.setAttribute("aria-label", t("Deck tools", "ابزار اسلاید"));
    const wanted = params.get("transition") || store.get("transition", "fade");
    const cur = TRANSITIONS.includes(wanted) ? wanted : "fade";
    bar.innerHTML = `
      <a class="azad-lnk" href="${siteRoot.href}">⌂ ${t("Home", "خانه")}</a>
      ${courseUrl ? `<a class="azad-lnk" href="${courseUrl}">☰ ${t("Course", "درس")}</a>` : ""}
      <span class="sep"></span>
      <select data-act="transition" aria-label="${t("Slide transition", "افکت گذار")}">
        ${TRANSITIONS.map((n) => `<option value="${n}"${n === cur ? " selected" : ""}>${t("Transition", "گذار")}: ${n}</option>`).join("")}
      </select>
      <button data-act="anim" aria-pressed="true"></button>
      <select data-act="speed" aria-label="${t("Animation speed", "سرعت انیمیشن")}">
        ${[["0.5", "0.5×"], ["1", "1×"], ["1.5", "1.5×"], ["2", "2×"]].map(([v, l]) => `<option value="${v}">${t("Speed", "سرعت")} ${l}</option>`).join("")}
      </select>
      <span class="sep"></span>
      <button data-act="full">${t("Fullscreen", "تمام‌صفحه")}</button>
      <button data-act="pdf">${t("Export PDF", "خروجی PDF")}</button>
      <button data-act="pptx">${t("PPTX", "PPTX")}</button>`;
    const fab = document.createElement("button");
    fab.type = "button"; fab.className = "azad-fab"; fab.textContent = "⋯";
    fab.setAttribute("aria-label", t("Deck menu", "منوی اسلاید"));
    fab.addEventListener("click", () => bar.classList.toggle("open"));
    document.body.append(zone, bar, fab);

    const speed = store.get("speed", "1");
    document.documentElement.style.setProperty("--speed", speed);
    bar.querySelector('[data-act="speed"]').value = speed;
    setAnimations(store.get("anim", "on") === "on" && !matchMedia("(prefers-reduced-motion: reduce)").matches);

    bar.addEventListener("change", (e) => {
      const act = e.target.dataset.act;
      if (act === "transition") { Reveal.configure({ transition: e.target.value, backgroundTransition: e.target.value }); store.set("transition", e.target.value); }
      if (act === "speed") { document.documentElement.style.setProperty("--speed", e.target.value); store.set("speed", e.target.value); }
      e.target.blur();
    });
    bar.addEventListener("click", (e) => {
      const act = e.target.dataset && e.target.dataset.act;
      if (act === "anim") setAnimations(document.documentElement.classList.contains("no-anim"));
      if (act === "full") (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {});
      if (act === "pdf") exportPdf();
      if (act === "pptx") toast(t("PPTX is exported from the terminal:  make pptx M=<module>  (see USAGE.md)", "خروجی PPTX از ترمینال: make pptx M=<شماره ماژول> (راهنما: USAGE.md)"));
    });
    Reveal.addKeyBinding({ keyCode: 65, key: "A", description: "Animations on/off" }, () => setAnimations(document.documentElement.classList.contains("no-anim")));
    Reveal.addKeyBinding({ keyCode: 84, key: "T", description: "Show/hide deck toolbar" }, () => bar.classList.toggle("open"));
  }

  /* On the last slide, offer the next deck (lesson -> its labs -> next module). The list comes from the local
   * server (/_decks.json); if it is not there (plain file, other server) nothing is shown. */
  async function setupNext() {
    let list;
    try {
      const r = await fetch(new URL("_decks.json", siteRoot), { cache: "no-store" });
      if (!r.ok) return;
      list = await r.json();
    } catch (e) { return; }
    const here = decodeURIComponent(location.pathname);
    const path = (p) => decodeURIComponent(new URL(p, siteRoot).pathname);
    const i = list.findIndex((d) => path(d.en) === here || (d.fa && path(d.fa) === here));
    if (i < 0) return;
    const fa = !!list[i].fa && path(list[i].fa) === here;
    const next = list[i + 1];
    const href = new URL(next ? (fa && next.fa ? next.fa : next.en) : (courseUrl || siteRoot.href), siteRoot).href;
    const label = next ? (fa ? next.title.fa : next.title.en) : "";
    const el = document.createElement("div");
    el.className = "azad-next"; el.setAttribute("role", "status"); el.hidden = true;
    const msg = document.createElement("span");
    msg.textContent = fa ? "✓ تمام شد" : "✓ Finished";
    const a = document.createElement("a");
    a.href = href;
    if (next) a.title = label;
    a.textContent = next ? (fa ? "بعدی: " + label + " ←" : "Next: " + label + " →")
                         : (fa ? "بازگشت به فهرست درس ←" : "Back to the course →");
    el.append(msg, a);
    document.body.append(el);
    // Position-based on purpose: in reveal's scroll view (phones) isLastSlide() is true from the start.
    const onLast = () => Reveal.getIndices().h >= Reveal.getTotalSlides() - 1;   // decks here are flat: one slide per index
    const sync = () => { el.hidden = !onLast(); };
    Reveal.on("slidechanged", sync); Reveal.on("fragmentshown", sync); document.addEventListener("scroll", sync, { capture: true, passive: true });   // scroll view scrolls <body>, not the window sync();
    Reveal.addKeyBinding({ keyCode: 13, key: "Enter", description: "On the last slide: open the next deck" },
      () => { if (!el.hidden) location.href = href; });
  }

  /* Portrait phones show the 16:9 slide very small: suggest landscape once per visit. */
  function rotateHint() {
    if (!matchMedia("(orientation: portrait) and (max-width: 700px)").matches) return;
    try { if (sessionStorage.getItem("azad.rotate")) return; } catch (e) { /* private mode: just show it */ }
    const el = document.createElement("div");
    el.className = "azad-rotate"; el.setAttribute("role", "note");
    const msg = document.createElement("span");
    msg.textContent = t("Turn your phone sideways for a bigger slide.", "برای اسلاید بزرگ‌تر، گوشی را افقی کنید.");
    const ok = document.createElement("button");
    ok.type = "button"; ok.textContent = t("OK", "باشه");
    ok.addEventListener("click", () => { el.remove(); try { sessionStorage.setItem("azad.rotate", "1"); } catch (e) { /* ignore */ } });
    el.append(msg, ok); document.body.append(el);
  }

  function boot() {
    decorate();
    const wanted = params.get("transition") || store.get("transition", "fade");
    const transition = printing || exporting ? "none" : (TRANSITIONS.includes(wanted) ? wanted : "fade");
    Reveal.initialize({
      width: 1920, height: 1080, margin: 0, minScale: 0.1, maxScale: 2,
      hash: true, center: false, rtl: rtl,
      transition: transition, transitionSpeed: "default", backgroundTransition: transition,
      slideNumber: false, showNotes: false,
      controls: false,   // arrows collided with the footer pill; keys, clicker and swipe still navigate
      pdfMaxPagesPerSlide: 1, pdfSeparateFragments: false,
      plugins: typeof RevealNotes !== "undefined" ? [RevealNotes] : [],
    }).then(() => {
      document.documentElement.dataset.slides = String(total);   // read by the exporter via --dump-dom
      if (exporting) {
        document.documentElement.classList.add("no-anim", "export");
        return;
      }
      if (printing) {
        document.documentElement.classList.add("no-anim");
        if (params.has("autoprint")) setTimeout(() => window.print(), 1200);
        return;
      }
      rotateHint();   // portrait phones show a 16:9 slide at ~7 px text, so suggest landscape (dismissible)
      buildToolbar();
      setupNext();
    });
  }

  /* Resolve the logo: the given path, then the same name with .png, else the placeholder. */
  function tryLoad(src) {
    return new Promise((ok) => { const i = new Image(); i.onload = () => ok(src); i.onerror = () => ok(""); i.src = src; });
  }
  (async function () {
    if (logoSrc) {
      resolvedLogo = await tryLoad(logoSrc);
      if (!resolvedLogo && /\.svg$/i.test(logoSrc)) resolvedLogo = await tryLoad(logoSrc.replace(/\.svg$/i, ".png"));
    }
    boot();
  })();
})();
