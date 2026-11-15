// Browser lab: runs a 32-bit Linux 6.8.12 kernel (v86) in the page and walks through the mini-labs in labs.mjs.
import { LABS, KERNEL_TAG, elixir } from "./labs.mjs";

const BASE = "/.cache/vendor/browser-lab/";
const CMDLINE = "tsc=reliable mitigations=off random.trust_cpu=on console=ttyS0";
const PROMPT = /% $/;                       // the guest shell prompt ends with "% "

const T = {
  en: {
    title: "Browser lab: a real Linux kernel in your browser", back: "All slide decks",
    noticeTitle: "A small, simplified lab.",
    noticeBody: "A real 32-bit Linux 6.8.12 kernel runs inside this page, on an emulated Pentium III with about 100 MB of RAM. Use it to try the ideas (processes, memory, signals, files) when you cannot run the course VM.",
    limitsTitle: "What it can and cannot do",
    limits: [
      "32-bit only, with no compiler, strace, perf, ftrace or bpftrace. The course's real labs need an x86-64 Linux v" + KERNEL_TAG.slice(1) + " machine.",
      "<b>Better, whenever possible:</b> run the real labs in a <b>virtual machine</b> (VirtualBox, KVM or QEMU). <b>Docker</b> is enough for the user-space labs. Use this browser lab only when neither is available.",
      "Everything runs locally in your browser tab and nothing is uploaded. Closing the tab resets the machine.",
    ],
    labsTitle: "Mini-labs", start: "Start the virtual machine", restart: "Restart", interrupt: "Stop (Ctrl+C)", clear: "Clear",
    st: { idle: "Not started. Click Start (downloads about 10 MB).", loading: "Downloading the kernel… {pct}%", booting: "Booting the kernel…",
          ready: "Ready. Run a step on the left, or type in the terminal.", running: "Running…", failed: "Could not start: {err}" },
    setupTitle: "One-time setup",
    setupBody: "The browser lab needs about 13 MB of files that are not stored in git. Clone the repository, then run this in the repository folder:",
    setupAfter: "It downloads the files, starts a local server and opens this page. The page does not work when opened as a plain file.",
    labN: "Lab {i} of {n}", module: "Module {m}", run: "Run", runningBtn: "Running…", ok: "Done: the output is what we expected.",
    bad: "The output was not what we expected. Run it again, or read the terminal.", timeout: "Taking too long. Press Stop (Ctrl+C) and try again.",
    ask: "Think about it", showAnswer: "Show the answer", src: "In the real kernel (Linux " + KERNEL_TAG + ")",
    srcNote: "The guest runs 6.8.12, so details can differ slightly from v6.18.63.", real: "In the course:",
    prev: "← Previous lab", next: "Next lab →",
    doneTitle: "Lab complete", doneBody: "You ran every step.", goNext: "Next lab: {t} →",
    allTitle: "All mini-labs complete", allBody: "Next: repeat these ideas with the real tools (strace, perf, ftrace) on the course VM, or go back to the slides.", goDecks: "Back to the slide decks →",
    stepOf: "Step {i}",
  },
  fa: {
    title: "آزمایشگاه مرورگر: یک کرنل واقعی Linux داخل مرورگر شما", back: "همهٔ اسلایدها",
    noticeTitle: "یک آزمایشگاه کوچک و ساده‌شده.",
    noticeBody: "یک کرنل واقعی ۳۲ بیتی Linux 6.8.12 داخل همین صفحه روی یک Pentium III شبیه‌سازی‌شده با حدود ۱۰۰ مگابایت RAM اجرا می‌شود. وقتی نمی‌توانید ماشین مجازی درس را اجرا کنید، از آن برای امتحان ایده‌ها (process، حافظه، signal، فایل) استفاده کنید.",
    limitsTitle: "چه کارهایی را می‌تواند و نمی‌تواند انجام دهد",
    limits: [
      "فقط ۳۲ بیتی است و compiler، strace، perf، ftrace و bpftrace ندارد. آزمایش‌های واقعی درس به یک ماشین x86-64 با Linux v" + KERNEL_TAG.slice(1) + " نیاز دارند.",
      "<b>در صورت امکان بهتر است:</b> آزمایش‌های واقعی را در یک <b>ماشین مجازی</b> (VirtualBox، KVM یا QEMU) اجرا کنید. برای آزمایش‌های user-space <b>Docker</b> هم کافی است. این آزمایشگاه مرورگر را فقط وقتی استفاده کنید که هیچ‌کدام در دسترس نیست.",
      "همه‌چیز محلی در همین تب مرورگر اجرا می‌شود و چیزی آپلود نمی‌شود. با بستن تب، ماشین از اول شروع می‌شود.",
    ],
    labsTitle: "آزمایش‌های کوچک", start: "راه‌اندازی ماشین مجازی", restart: "راه‌اندازی مجدد", interrupt: "توقف (Ctrl+C)", clear: "پاک کردن",
    st: { idle: "شروع نشده. روی راه‌اندازی بزنید (حدود ۱۰ مگابایت دانلود می‌شود).", loading: "در حال دانلود کرنل… {pct}٪", booting: "در حال boot کرنل…",
          ready: "آماده. یک گام را در سمت چپ اجرا کنید یا در ترمینال تایپ کنید.", running: "در حال اجرا…", failed: "راه‌اندازی نشد: {err}" },
    setupTitle: "راه‌اندازی یک‌باره",
    setupBody: "آزمایشگاه مرورگر به حدود ۱۳ مگابایت فایل نیاز دارد که در git نیستند. مخزن (repository) را clone کنید و سپس در پوشهٔ آن این دستور را اجرا کنید:",
    setupAfter: "فایل‌ها را دانلود می‌کند، یک سرور محلی راه می‌اندازد و همین صفحه را باز می‌کند. اگر صفحه به‌صورت فایل ساده باز شود کار نمی‌کند.",
    labN: "آزمایش {i} از {n}", module: "ماژول {m}", run: "اجرا", runningBtn: "در حال اجرا…", ok: "انجام شد: خروجی همان بود که انتظار داشتیم.",
    bad: "خروجی همان نبود که انتظار داشتیم. دوباره اجرا کنید یا ترمینال را ببینید.", timeout: "بیش از حد طول کشید. توقف (Ctrl+C) را بزنید و دوباره امتحان کنید.",
    ask: "فکر کنید", showAnswer: "نمایش پاسخ", src: "در کرنل واقعی (Linux " + KERNEL_TAG + ")",
    srcNote: "ماشین مجازی 6.8.12 است، پس جزئیات ممکن است کمی با v6.18.63 فرق کند.", real: "در درس:",
    prev: "← آزمایش قبلی", next: "آزمایش بعدی ←",
    doneTitle: "آزمایش کامل شد", doneBody: "همهٔ گام‌ها را اجرا کردید.", goNext: "آزمایش بعدی: {t} ←",
    allTitle: "همهٔ آزمایش‌های کوچک کامل شد", allBody: "گام بعدی: همین ایده‌ها را با ابزارهای واقعی (strace، perf، ftrace) روی ماشین مجازی درس تکرار کنید، یا به اسلایدها برگردید.", goDecks: "بازگشت به اسلایدها ←",
    stepOf: "گام {i}",
  },
};

/* ------------------------------------------------------------------ helpers */
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (s, o) => s.replace(/\{(\w+)\}/g, (_, k) => o[k]);
const store = {
  get(k, d) { try { const v = localStorage.getItem("azad." + k); return v === null ? d : v; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem("azad." + k, v); } catch (e) { /* storage blocked: progress just won't persist */ } },
};
const loadScript = (src) => new Promise((ok, err) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = () => err(new Error("cannot load " + src)); document.head.append(s); });
const loadCss = (href) => { const l = document.createElement("link"); l.rel = "stylesheet"; l.href = href; document.head.append(l); };
/* Lab text: HTML-escaped; in Farsi each English run (commands, names) is isolated so punctuation does not jump around. */
const LATIN = /[A-Za-z0-9\/][A-Za-z0-9_\-.()\/+ :=%'’$]*[A-Za-z0-9_)\/%']|[A-Za-z0-9]/g;
const LT = (o) => (lang === "fa" && o.fa ? esc(o.fa).replace(LATIN, (m) => `<bdi dir="ltr">${m}</bdi>`) : esc(o.en));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const stripAnsi = (s) => s.replace(/\x1b\[[0-9;?]*[A-Za-z]/g, "");

/* ------------------------------------------------------------------ state */
let lang = store.get("lang", "en") === "fa" ? "fa" : "en";
const t = () => T[lang];
const L = (o) => o[lang] || o.en;
let cur = Math.max(0, Math.min(LABS.length - 1, parseInt(store.get("lab.cur", "0"), 10) || 0));
let progress = {};                                   // "labId:stepIndex" -> true
try { progress = JSON.parse(store.get("lab.steps", "{}")) || {}; } catch (e) { progress = {}; }
const saveProgress = () => store.set("lab.steps", JSON.stringify(progress));
const labDone = (lab) => lab.steps.every((_, i) => progress[`${lab.id}:${i}`]);

const vm = { emu: null, term: null, fit: null, started: false, ready: false, busy: false, out: "", outStart: 0, pending: [], assets: false };

/* ------------------------------------------------------------------ static text */
function applyStatic() {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
  document.title = lang === "fa" ? "آزمایشگاه مرورگر · سیستم‌عامل آزاد" : "Browser lab · Azad OS";
  document.querySelectorAll("[data-k]").forEach((e) => { e.textContent = t()[e.dataset.k]; });
  $("#limits").innerHTML = t().limits.map((x) => `<li>${x}</li>`).join("");
  document.querySelectorAll(".seg button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.l === lang)));
  renderSetup();
  setStatus(vm.statusKey || "idle", vm.statusArg);
}

function setStatus(key, arg) {
  vm.statusKey = key; vm.statusArg = arg;
  const el = $("#status");
  el.textContent = fmt(t().st[key] || key, arg || {});
  el.classList.toggle("ready", key === "ready");
}

function renderSetup() {
  const box = $("#setup");
  if (vm.assets && location.protocol !== "file:") { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  $("#term").classList.add("hidden");
  box.innerHTML = `<h3 style="margin:0 0 4px">${esc(t().setupTitle)}</h3><p>${esc(t().setupBody)}</p><pre>git clone &lt;repository-url&gt;\ncd &lt;repository-folder&gt;\nmake browser-lab</pre><p class="muted">${esc(t().setupAfter)}</p>`;
}

/* ------------------------------------------------------------------ chooser + lab */
function renderDots() {
  $("#dots").innerHTML = LABS.map((lab, i) =>
    `<li><button type="button" data-goto="${i}" ${i === cur ? 'aria-current="true"' : ""} class="${labDone(lab) ? "done" : ""}" title="${esc(L(lab.title))}">${labDone(lab) ? "✓ " : ""}${i + 1}</button></li>`).join("");
}

function renderLab() {
  const lab = LABS[cur];
  const steps = lab.steps.map((s, i) => {
    const ok = progress[`${lab.id}:${i}`];
    return `<li class="step ${ok ? "ok" : ""}" data-step="${i}">
      <span class="n" aria-label="${esc(fmt(t().stepOf, { i: i + 1 }))}">${ok ? "✓" : i + 1}</span>
      <p>${LT(s)}</p>
      <div class="cmd"><code>${esc(s.cmd)}</code><button type="button" class="run" data-run="${i}">${esc(t().run)}</button></div>
      <div class="state ${ok ? "ok" : ""}" aria-live="polite">${ok ? esc(t().ok) : ""}</div></li>`;
  }).join("");
  const src = lab.source.map((s) => `<li><a href="${elixir(s.path)}" target="_blank" rel="noopener"><code>${esc(s.path)}</code></a>: ${LT(s)}</li>`).join("");
  $("#labbox").innerHTML = `
    <span class="chip">${esc(fmt(t().module, { m: lab.module }))} · ${esc(fmt(t().labN, { i: cur + 1, n: LABS.length }))}</span>
    <h2>${LT(lab.title)}</h2>
    <p class="muted">${LT(lab.intro)}</p>
    <ol class="steps">${steps}</ol>
    <div class="ask"><h3>${esc(t().ask)}</h3><p>${LT(lab.ask)}</p>
      <details><summary>${esc(t().showAnswer)}</summary><p>${LT(lab.answer)}</p></details></div>
    <div class="src"><h3>${esc(t().src)}</h3><ul>${src}</ul><p class="muted" style="font-size:13px;margin:6px 0 0">${esc(t().srcNote)}</p></div>
    <p class="real">${esc(t().real)} ${LT(lab.real)}</p>
    <div id="finish"></div>
    <div class="nav"><button type="button" data-goto="${cur - 1}" ${cur === 0 ? "disabled" : ""}>${esc(t().prev)}</button>
      <button type="button" data-goto="${cur + 1}" ${cur === LABS.length - 1 ? "disabled" : ""}>${esc(t().next)}</button></div>`;
  renderDots();
  updateRunButtons();
  if (labDone(lab)) showFinish();
}

function updateRunButtons() {
  document.querySelectorAll("button.run").forEach((b) => {
    b.disabled = !vm.ready || vm.busy;
    b.textContent = vm.busy && b.dataset.busy === "1" ? t().runningBtn : t().run;
  });
}

function showFinish() {
  const box = $("#finish");
  if (!box) return;
  const next = LABS[cur + 1];
  box.innerHTML = next
    ? `<div class="finish" role="status"><h3>✓ ${esc(t().doneTitle)}</h3><div>${esc(t().doneBody)}</div>
         <button type="button" class="go" data-goto="${cur + 1}">${esc(fmt(t().goNext, { t: L(next.title) }))}</button></div>`
    : `<div class="finish" role="status"><h3>🎉 ${esc(t().allTitle)}</h3><div>${esc(t().allBody)}</div>
         <a class="go" href="/">${esc(t().goDecks)}</a></div>`;
}

function gotoLab(i) {
  if (i < 0 || i >= LABS.length) return;
  cur = i; store.set("lab.cur", String(i));
  renderLab();
  $("#chooserCard").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ------------------------------------------------------------------ running a step */
async function runStep(i, btn) {
  if (!vm.ready || vm.busy) return;
  const lab = LABS[cur], step = lab.steps[i];
  vm.busy = true; btn.dataset.busy = "1"; updateRunButtons(); setStatus("running");
  const li = $(`.step[data-step="${i}"]`), state = li.querySelector(".state");
  state.textContent = ""; state.className = "state"; li.classList.remove("bad");
  const start = vm.outStart + vm.out.length;
  vm.emu.serial0_send(step.cmd + "\n");
  vm.term.focus();
  await sleep(300);
  const budget = step.timeout || 60000, t0 = Date.now();
  const since = () => vm.out.slice(start - vm.outStart);
  while (!PROMPT.test(since()) && Date.now() - t0 < budget) await sleep(100);
  const finished = PROMPT.test(since());
  const raw = stripAnsi(since()).replace(/\r/g, "");
  const result = raw.slice(raw.indexOf("\n") + 1);          // drop the echoed command line
  const ok = finished && new RegExp(step.expect).test(result);
  btn.dataset.busy = ""; vm.busy = false;
  if (ok) {
    progress[`${lab.id}:${i}`] = true; saveProgress();
    li.classList.add("ok"); li.querySelector(".n").textContent = "✓";
    state.classList.add("ok"); state.textContent = t().ok;
  } else {
    li.classList.add("bad"); state.classList.add("bad"); state.textContent = finished ? t().bad : t().timeout;
  }
  setStatus("ready"); updateRunButtons(); renderDots();
  if (labDone(lab)) showFinish();
}

/* ------------------------------------------------------------------ the virtual machine */
function onSerialByte(b) {
  vm.pending.push(b);
  if (vm.pending.length === 1) requestAnimationFrame(flushSerial);
}
function flushSerial() {
  const bytes = Uint8Array.from(vm.pending); vm.pending.length = 0;
  vm.term.write(bytes);
  vm.out += String.fromCharCode(...bytes);
  if (vm.out.length > 400000) { const cut = vm.out.length - 200000; vm.out = vm.out.slice(cut); vm.outStart += cut; }
  if (!vm.ready && PROMPT.test(vm.out.slice(-8))) {
    vm.ready = true; setStatus("ready");
    for (const id of ["btnInt", "btnClear", "btnRestart"]) $("#" + id).disabled = false;
    updateRunButtons();
  }
}

async function startVM() {
  if (vm.started) return;
  vm.started = true; $("#btnStart").disabled = true; setStatus("loading", { pct: 0 });
  $("#prog").hidden = false;
  try {
    loadCss(BASE + "xterm.css");
    await loadScript(BASE + "libv86.js");
    await loadScript(BASE + "xterm.js");
    await loadScript(BASE + "addon-fit.js");
    const term = new window.Terminal({
      fontSize: matchMedia("(max-width: 640px)").matches ? 12 : 14, cursorBlink: true, fontFamily: 'ui-monospace, Consolas, "JetBrains Mono", monospace', scrollback: 4000,
      theme: { background: "#FFFFFF", foreground: "#0A1633", cursor: "#2F4BB0", selectionBackground: "#C9D4F7",
               black: "#0A1633", red: "#B4123A", green: "#12733A", yellow: "#9A4A00", blue: "#2F4BB0", magenta: "#6D28D9", cyan: "#0E7490", white: "#4A5780",
               brightBlack: "#4A5780", brightRed: "#B4123A", brightGreen: "#12733A", brightYellow: "#9A4A00", brightBlue: "#2F4BB0", brightMagenta: "#6D28D9", brightCyan: "#0E7490", brightWhite: "#0A1633" },
    });
    const fit = new window.FitAddon.FitAddon();
    term.loadAddon(fit); term.open($("#term")); fit.fit();
    addEventListener("resize", () => fit.fit());
    Object.assign(vm, { term, fit });

    const emu = new window.V86({
      wasm_path: BASE + "v86.wasm", memory_size: 128 * 1024 * 1024, vga_memory_size: 2 * 1024 * 1024,
      bios: { url: BASE + "seabios.bin" }, vga_bios: { url: BASE + "vgabios.bin" },
      bzimage: { url: BASE + "buildroot-bzimage68.bin" }, cmdline: CMDLINE,
      autostart: true, disable_keyboard: true, disable_mouse: true, disable_speaker: true,
    });
    vm.emu = emu;
    emu.add_listener("download-progress", (e) => {
      if (!e.total) return;
      const pct = Math.round((e.loaded / e.total) * 100);
      $("#progBar").style.width = pct + "%";
      setStatus("loading", { pct });
    });
    emu.add_listener("emulator-loaded", () => { $("#prog").hidden = true; setStatus("booting"); });
    emu.add_listener("serial0-output-byte", onSerialByte);
    term.onData((d) => emu.serial0_send(d));
  } catch (e) {
    vm.started = false; $("#btnStart").disabled = false; $("#prog").hidden = true;
    setStatus("failed", { err: e.message });
  }
}

function restartVM() {
  if (!vm.emu) return;
  vm.ready = false; vm.busy = false; vm.out = ""; vm.outStart = 0;
  vm.term.reset(); setStatus("booting"); updateRunButtons();
  for (const id of ["btnInt", "btnClear", "btnRestart"]) $("#" + id).disabled = true;
  vm.emu.restart();
}

/* ------------------------------------------------------------------ wiring */
document.addEventListener("click", (e) => {
  const run = e.target.closest("button.run"); if (run) return runStep(parseInt(run.dataset.run, 10), run);
  const go = e.target.closest("[data-goto]"); if (go && !go.disabled) return gotoLab(parseInt(go.dataset.goto, 10));
  const lg = e.target.closest(".seg button");
  if (lg) { lang = lg.dataset.l; store.set("lang", lang); applyStatic(); renderLab(); }
});
$("#btnStart").addEventListener("click", startVM);
$("#btnInt").addEventListener("click", () => { vm.emu && vm.emu.serial0_send("\x03"); vm.term && vm.term.focus(); });
$("#btnClear").addEventListener("click", () => { vm.term && vm.term.clear(); });
$("#btnRestart").addEventListener("click", restartVM);

(async function init() {
  try {
    const r = await fetch(BASE + "manifest.json", { cache: "no-store" });
    vm.assets = r.ok;
  } catch (e) { vm.assets = false; }
  applyStatic();
  renderLab();
  if (!vm.assets) { $("#btnStart").disabled = true; }
})();
