/* =====================================================================
   NexaSearch - core front-end behaviour
   Vanilla JS only: theme, autocomplete (Trie-backed), history dock,
   copy buttons, and small helpers. No external libraries.
   ===================================================================== */
(function () {
  "use strict";

  /* ---------------------------------------------------------- theme */
  const THEME_KEY = "nexasearch.theme";
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* private mode */ }
    document.querySelectorAll("[data-theme-chart]").forEach(renderChartFromEl);
  }

  (function initTheme() {
    let stored = null;
    try { stored = localStorage.getItem(THEME_KEY); } catch (e) { stored = null; }
    if (!stored) {
      stored = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light" : "dark";
    }
    root.setAttribute("data-theme", stored);
  })();

  document.addEventListener("click", function (event) {
    const toggle = event.target.closest("#theme-toggle");
    if (!toggle) return;
    applyTheme(root.getAttribute("data-theme") === "light" ? "dark" : "light");
  });

  /* ----------------------------------------------- autocomplete (Trie) */
  function debounce(fn, wait) {
    let timer = null;
    return function () {
      const args = arguments, ctx = this;
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(ctx, args), wait);
    };
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, ch => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
    ));
  }

  function setupAutocomplete(field) {
    const input = field.querySelector("input");
    const list = field.querySelector(".suggestions");
    if (!input || !list) return;

    let items = [];
    let activeIndex = -1;
    let controller = null;

    function close() { list.hidden = true; list.innerHTML = ""; items = []; activeIndex = -1; }

    function highlight() {
      Array.from(list.children).forEach((li, i) => {
        li.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
      });
    }

    function render(data) {
      items = data.suggestions || [];
      if (!items.length) { close(); return; }
      list.innerHTML = items.map(row => `
        <li role="option" data-word="${escapeHtml(row.word)}">
          <span>
            <span class="sug-word">${escapeHtml(row.word)}</span>
            ${row.documents ? `<span class="sug-tag">in ${row.documents} doc${row.documents === 1 ? "" : "s"}</span>` : ""}
          </span>
          <span class="sug-meta">freq ${row.frequency}</span>
        </li>`).join("");
      list.hidden = false;
      list.querySelectorAll("li").forEach(li => {
        li.addEventListener("mousedown", event => {
          event.preventDefault();
          input.value = li.dataset.word;
          close();
          input.form.submit();
        });
      });
      activeIndex = -1;
    }

    const fetchSuggestions = debounce(async function () {
      const term = input.value.trim();
      if (term.length < 2) { close(); return; }
      if (controller) controller.abort();
      controller = new AbortController();
      try {
        const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(term)}&limit=8`,
          { signal: controller.signal, headers: { "Accept": "application/json" } });
        if (response.ok) render(await response.json());
      } catch (error) { /* aborted or offline - keep the typed text */ }
    }, 110);

    input.addEventListener("input", fetchSuggestions);
    input.addEventListener("focus", () => { if (input.value.trim().length >= 2) fetchSuggestions(); });
    input.addEventListener("keydown", event => {
      if (list.hidden) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        activeIndex += event.key === "ArrowDown" ? 1 : -1;
        if (activeIndex < 0) activeIndex = items.length - 1;
        if (activeIndex >= items.length) activeIndex = 0;
        highlight();
      } else if (event.key === "Enter" && activeIndex >= 0) {
        event.preventDefault();
        input.value = items[activeIndex].word;
        close();
        input.form.submit();
      } else if (event.key === "Escape") {
        close();
      }
    });
    document.addEventListener("click", event => { if (!field.contains(event.target)) close(); });
  }

  document.querySelectorAll("[data-autocomplete]").forEach(setupAutocomplete);

  /* ------------------------------------------------------ history dock */
  const dock = document.getElementById("history-dock");
  if (dock) {
    const button = dock.querySelector(".history-toggle");
    const stored = (() => { try { return localStorage.getItem("nexasearch.dock"); } catch (e) { return null; } })();
    if (stored === "collapsed") dock.classList.add("collapsed");
    button.addEventListener("click", () => {
      const collapsed = dock.classList.toggle("collapsed");
      button.setAttribute("aria-expanded", String(!collapsed));
      try { localStorage.setItem("nexasearch.dock", collapsed ? "collapsed" : "open"); } catch (e) {}
    });
  }

  /* --------------------------------------------------- copy buttons */
  document.addEventListener("click", function (event) {
    const button = event.target.closest(".copy-btn");
    if (!button) return;
    const target = document.querySelector(button.dataset.copy);
    if (!target) return;
    const text = target.innerText;
    const done = () => {
      const original = button.textContent;
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = original; }, 1200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(() => {});
    } else {
      const area = document.createElement("textarea");
      area.value = text; document.body.appendChild(area); area.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(area);
    }
  });

  /* ------------------------------------------------- confirm actions */
  document.addEventListener("submit", function (event) {
    const form = event.target;
    const message = form.dataset.confirm;
    if (message && !window.confirm(message)) event.preventDefault();
  });

  /* ------------------------------------------------- filter shortcuts */
  document.querySelectorAll("[data-submit-on-change]").forEach(el => {
    el.addEventListener("change", () => el.form && el.form.submit());
  });

  /* ------------------------------------------------------ bar widths */
  function fillBars(root) {
    root.querySelectorAll("[data-fill]").forEach(el => {
      const value = parseFloat(el.dataset.fill);
      el.style.width = Math.max(0, Math.min(100, value)) + "%";
    });
  }
  fillBars(document);
  window.NexaFillBars = fillBars;

  /* ----------------------------------------------------- counters */
  function countUp(el) {
    const target = parseFloat(el.dataset.count);
    if (!isFinite(target)) return;
    const decimals = (el.dataset.count.split(".")[1] || "").length;
    const duration = 700;
    const start = performance.now();
    function frame(now) {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = (target * eased).toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      if (progress < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  document.querySelectorAll("[data-count]").forEach(countUp);
  window.NexaCountUp = countUp;

  /* ================================================================
     Charts: a tiny canvas plotting library (line + grouped bars).
     No CDN so the project works fully offline.
     ================================================================ */
  const PALETTE = ["#6f8bff", "#22d3ee", "#a855f7", "#34d399", "#fbbf24", "#f87171"];

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function niceMax(value) {
    if (value <= 0) return 1;
    const exp = Math.floor(Math.log10(value));
    const base = Math.pow(10, exp);
    return Math.ceil(value / base) * base;
  }

  function renderChart(canvas, spec) {
    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || canvas.parentElement.clientWidth || 600;
    const cssHeight = canvas.dataset.height ? parseInt(canvas.dataset.height, 10) : 260;
    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    canvas.style.height = cssHeight + "px";
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    const text = cssVar("--text-3") || "#74809f";
    const gridColor = cssVar("--border") || "rgba(148,163,208,.16)";
    const font = '12px "Inter", system-ui, sans-serif';
    ctx.font = font;

    if (!spec || !spec.series || !spec.series.length) return;

    const padding = { top: 16, right: 18, bottom: 34, left: 58 };
    const plotWidth = cssWidth - padding.left - padding.right;
    const plotHeight = cssHeight - padding.top - padding.bottom;
    if (plotWidth <= 10 || plotHeight <= 10) return;

    const logScale = !!spec.log;
    const allValues = spec.series.flatMap(s => s.data.map(p => p.y));
    const positives = allValues.filter(v => v > 0);
    const maxValue = niceMax(Math.max(1, ...allValues));
    const minValue = spec.min !== undefined ? spec.min
      : (logScale && positives.length ? Math.min.apply(null, positives) : 0);
    const logFloor = logScale
      ? Math.log10(Math.max(1e-12, minValue || 1e-12))
      : 0;
    const logCeil = logScale ? Math.log10(Math.max(logFloor + 1, maxValue)) : 0;

    function toY(value) {
      if (logScale) {
        const clamped = Math.max(1e-12, value || 1e-12);
        return padding.top + plotHeight -
          ((Math.log10(clamped) - logFloor) / (logCeil - logFloor || 1)) * plotHeight;
      }
      return padding.top + plotHeight - ((value - minValue) / (maxValue - minValue || 1)) * plotHeight;
    }

    function formatTick(value) {
      if (spec.yFormat) return spec.yFormat(value);
      if (logScale) {
        if (value <= 0) return "";
        const exponent = Math.log10(value);
        return Number.isInteger(exponent) ? "1e" + exponent : value.toExponential(0);
      }
      return String(Math.round(value));
    }

    // grid + y labels
    ctx.strokeStyle = gridColor;
    ctx.fillStyle = text;
    ctx.lineWidth = 1;
    const steps = 4;
    for (let i = 0; i <= steps; i++) {
      const value = logScale
        ? Math.pow(10, logFloor + (i / steps) * (logCeil - logFloor))
        : minValue + (i / steps) * (maxValue - minValue);
      const y = Math.round(toY(value)) + .5;
      ctx.beginPath(); ctx.moveTo(padding.left, y); ctx.lineTo(cssWidth - padding.right, y); ctx.stroke();
      ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(formatTick(value), padding.left - 8, y);
    }

    const labels = spec.labels || [];
    const step = labels.length > 1 ? plotWidth / (labels.length - 1) : plotWidth;
    const xAt = index => spec.bar
      ? padding.left + (index + 0.5) * (plotWidth / Math.max(1, labels.length))
      : padding.left + (labels.length > 1 ? index * step : plotWidth / 2);

    // x labels
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    const skip = labels.length > 12 ? Math.ceil(labels.length / 12) : 1;
    labels.forEach((label, index) => {
      if (index % skip !== 0 && index !== labels.length - 1) return;
      ctx.fillText(String(label), xAt(index), padding.top + plotHeight + 8);
    });

    // series
    spec.series.forEach((series, sIndex) => {
      const color = series.color || PALETTE[sIndex % PALETTE.length];
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = 2;

      if (spec.bar) {
        const groupWidth = (plotWidth / Math.max(1, labels.length));
        const barWidth = Math.max(3, (groupWidth * .72) / spec.series.length);
        series.data.forEach((point, index) => {
          const x = padding.left + index * groupWidth + (groupWidth * .72 - barWidth * spec.series.length) / 2
            + sIndex * barWidth;
          const y = toY(point.y);
          const barHeight = padding.top + plotHeight - y;
          ctx.globalAlpha = .88;
          ctx.beginPath();
          if (ctx.roundRect) ctx.roundRect(x, y, barWidth - 2, Math.max(1, barHeight), 3);
          else ctx.rect(x, y, barWidth - 2, Math.max(1, barHeight));
          ctx.fill();
          ctx.globalAlpha = 1;
        });
      } else {
        ctx.beginPath();
        series.data.forEach((point, index) => {
          const x = xAt(index), y = toY(point.y);
          if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();
        series.data.forEach((point, index) => {
          const x = xAt(index), y = toY(point.y);
          ctx.beginPath(); ctx.arc(x, y, 3.2, 0, Math.PI * 2);
          ctx.fill();
          if (spec.pointLabels) {
            ctx.textAlign = "center"; ctx.textBaseline = "bottom";
            ctx.fillText(spec.pointLabels(point.y), x, y - 6);
          }
        });
      }
    });
  }

  function renderChartFromEl(el) {
    try {
      const spec = JSON.parse(el.dataset.chart);
      renderChart(el, spec);
    } catch (error) {
      console.warn("chart spec invalid", error);
    }
  }

  window.NexaChart = { render: renderChart, palette: PALETTE };
  document.querySelectorAll("[data-chart]").forEach(renderChartFromEl);

  let resizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      document.querySelectorAll("[data-chart]").forEach(renderChartFromEl);
    }, 180);
  });

  /* ------------------------------------------------- generic fetch UI */
  window.NexaPost = async function (url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    });
    let payload = null;
    try { payload = await response.json(); } catch (e) { payload = { error: "invalid response" }; }
    return { ok: response.ok, status: response.status, data: payload };
  };

  window.NexaEscape = escapeHtml;
})();
