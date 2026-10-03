/* =====================================================================
   NexaSearch - Algorithm Lab
   Renders the input forms from a config object, posts them to the Flask
   lab endpoints (which run the real Python implementations) and plays
   back the returned step traces.
   ===================================================================== */
(function () {
  "use strict";

  const root = document.getElementById("lab-root");
  if (!root) return;

  const esc = window.NexaEscape || ((s) => String(s));
  const fmt = (value, digits = 3) =>
    (value === null || value === undefined || value === "" ? "-" :
      typeof value === "number" ? value.toFixed(digits) : String(value));

  /* ------------------------------------------------------- lab config */
  const LABS = [
    { id: "binary_search", name: "Binary Search", category: "Searching",
      blurb: "Halve a sorted array until the target is found or the range collapses.",
      fields: [
        { name: "array", label: "Sorted array", type: "text", value: "11 22 33 44 55 66 77 88 99",
          hint: "Space or comma separated integers (max 40). The engine sorts them for you." },
        { name: "target", label: "Target", type: "text", value: "55" }
      ] },
    { id: "kmp", name: "KMP", category: "String Matching",
      blurb: "Build the LPS array, then match without ever moving the text pointer back.",
      fields: [
        { name: "text", label: "Text", type: "text", value: "ABABDABACDABABCABAB" },
        { name: "pattern", label: "Pattern", type: "text", value: "ABABCABAB" }
      ] },
    { id: "rabin_karp", name: "Rabin-Karp", category: "String Matching",
      blurb: "Rolling-hash pre-filter, then verify each candidate window.",
      fields: [
        { name: "text", label: "Text", type: "text", value: "ABABDABACDABABCABAB" },
        { name: "pattern", label: "Pattern", type: "text", value: "ABABCABAB" }
      ] },
    { id: "trie", name: "Trie", category: "Searching",
      blurb: "Insert words character by character, then walk a prefix subtree.",
      fields: [
        { name: "words", label: "Words to insert", type: "textarea",
          value: "machine machine learning machine vision algorithm algorithms algorithm analysis graph graphs graph traversal search searching",
          hint: "Duplicates are allowed - watch the frequency counter move." },
        { name: "prefix", label: "Prefix to look up", type: "text", value: "alg" }
      ] },
    { id: "hash", name: "Hash Table", category: "Searching",
      blurb: "Insert keys, watch collisions appear, compare chaining with linear probing.",
      fields: [
        { name: "keys", label: "Keys", type: "textarea",
          value: "algorithm, algorithms, hashing, hash, trie, search, index, query, rank, ranking",
          hint: "Deliberately similar keys collide - the interesting case." },
        { name: "probe", label: "Key to look up", type: "text", value: "ranking" }
      ] },
    { id: "bfs", name: "BFS", category: "Graph",
      blurb: "Level-by-level traversal of a graph using a FIFO queue.",
      fields: [
        { name: "edges", label: "Edges", type: "text", value: "A-B, A-C, B-D, C-E, D-F, E-F",
          hint: "Comma separated A-B style pairs." },
        { name: "start", label: "Start node", type: "text", value: "A" }
      ] },
    { id: "dfs", name: "DFS", category: "Graph",
      blurb: "Depth-first traversal with an explicit stack, showing backtracking.",
      fields: [
        { name: "edges", label: "Edges", type: "text", value: "A-B, A-C, B-D, C-E, D-F, E-F" },
        { name: "start", label: "Start node", type: "text", value: "A" },
        { name: "mode", label: "Implementation", type: "select",
          options: [["iterative", "Explicit stack"], ["recursive", "Recursive call stack"]] }
      ] },
    { id: "dijkstra", name: "Dijkstra", category: "Graph",
      blurb: "Settle the closest node first using a hand-built binary min-heap.",
      fields: [
        { name: "weighted_edges", label: "Weighted edges", type: "text",
          value: "A-B:4, A-C:2, B-C:1, B-D:5, C-D:8, C-E:10, D-F:6, E-F:3" },
        { name: "start", label: "Source", type: "text", value: "A" },
        { name: "goal", label: "Target (optional)", type: "text", value: "F" }
      ] },
    { id: "merge_sort", name: "Merge Sort", category: "Sorting",
      blurb: "Split into halves, sort recursively, then merge the two sorted runs.",
      fields: [
        { name: "values", label: "Values", type: "text", value: "38 27 43 3 9 82 10 55 1 25" }
      ] },
    { id: "quick_sort", name: "Quick Sort", category: "Sorting",
      blurb: "Partition around a median-of-three pivot, then recurse on both sides.",
      fields: [
        { name: "values", label: "Values", type: "text", value: "38 27 43 3 9 82 10 55 1 25" }
      ] }
  ];

  const state = { current: LABS[0].id, timer: null };

  /* ------------------------------------------------------- rendering */
  function renderShell() {
    root.innerHTML = `
      <div class="pill-group" id="lab-tabs" role="tablist">
        ${LABS.map(lab => `<button type="button" class="pill${lab.id === state.current ? " active" : ""}"
             data-lab="${lab.id}" role="tab">${esc(lab.name)}</button>`).join("")}
      </div>
      <div class="split" style="margin-top:1.2rem">
        <div class="card" id="lab-input"></div>
        <div id="lab-output"><div class="card empty-state">
          <div class="big">&#128218;</div>
          <p>Pick an algorithm, enter input and press <strong>Run</strong> to watch it execute step by step.</p>
        </div></div>
      </div>`;

    root.querySelectorAll("[data-lab]").forEach(button => {
      button.addEventListener("click", () => {
        state.current = button.dataset.lab;
        root.querySelectorAll("[data-lab]").forEach(b => b.classList.toggle("active", b === button));
        renderInput();
        const url = new URL(window.location.href);
        url.searchParams.set("algo", state.current);
        window.history.replaceState({}, "", url);
      });
    });
    renderInput();
  }

  function currentLab() { return LABS.find(lab => lab.id === state.current); }

  function renderInput() {
    const lab = currentLab();
    const form = document.getElementById("lab-input");
    form.innerHTML = `
      <div class="card-head">
        <h3>${esc(lab.name)}</h3>
        <span class="chip chip-brand">${esc(lab.category)}</span>
      </div>
      <p class="muted small">${esc(lab.blurb)}</p>
      <form id="lab-form">
        ${lab.fields.map(field => `
          <div class="field">
            <label for="in-${field.name}">${esc(field.label)}</label>
            ${field.type === "textarea"
              ? `<textarea id="in-${field.name}" name="${field.name}" rows="4">${esc(field.value)}</textarea>`
              : field.type === "select"
                ? `<select id="in-${field.name}" name="${field.name}">
                     ${field.options.map(([value, label]) =>
                        `<option value="${esc(value)}"${value === field.value ? " selected" : ""}>${esc(label)}</option>`).join("")}
                   </select>`
                : `<input type="text" id="in-${field.name}" name="${field.name}" value="${esc(field.value)}">`}
            ${field.hint ? `<p class="tiny muted" style="margin:.3rem 0 0">${esc(field.hint)}</p>` : ""}
          </div>`).join("")}
        <button type="submit" class="btn btn-primary">Run algorithm</button>
      </form>`;

    form.addEventListener("submit", async event => {
      event.preventDefault();
      const button = form.querySelector("button[type=submit]");
      const payload = {};
      new FormData(form).forEach((value, key) => { payload[key] = value; });
      button.disabled = true;
      button.innerHTML = '<span class="spinner"></span> Running';
      const output = document.getElementById("lab-output");
      output.innerHTML = '<div class="card"><p class="muted">Running the Python implementation…</p></div>';
      try {
        const response = await fetch(`/algorithms/lab/${lab.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          output.innerHTML = `<div class="card"><div class="alert alert-err">
            <strong>Could not run ${esc(lab.name)}</strong><p class="small" style="margin:.4rem 0 0">${esc(data.error || "invalid input")}</p>
          </div></div>`;
        } else {
          RENDERERS[lab.id](data, output);
        }
      } catch (error) {
        output.innerHTML = `<div class="card"><div class="alert alert-err">Request failed: ${esc(error.message)}</div></div>`;
      } finally {
        button.disabled = false;
        button.textContent = "Run algorithm";
      }
    });
  }

  /* ------------------------------------------------- shared fragments */
  function complexityBlock(data) {
    const c = data.complexity || {};
    return `
      <div class="card" style="margin-top:1rem">
        <div class="card-head"><h4>Complexity</h4></div>
        <div class="table-wrap"><table>
          <tbody>
            <tr><th>Time</th><td class="mono">${esc(c.time || "-")}</td></tr>
            <tr><th>Space</th><td class="mono">${esc(c.space || "-")}</td></tr>
            <tr><th>Best</th><td class="mono">${esc(c.best || "-")}</td></tr>
            <tr><th>Average</th><td class="mono">${esc(c.average || "-")}</td></tr>
            <tr><th>Worst</th><td class="mono">${esc(c.worst || "-")}</td></tr>
            <tr><th>Measured</th><td class="mono">${fmt(data.time_ms, 4)} ms</td></tr>
          </tbody>
        </table></div>
        ${data.explanation ? `<p class="muted small" style="margin-top:.8rem">${esc(data.explanation)}</p>` : ""}
      </div>`;
  }

  function stepsPanel(steps, describeStep) {
    if (!steps || !steps.length) return "";
    const rows = steps.map((step, index) => `
      <div class="step" data-step="${index}">
        <span class="step-index">${index + 1}</span>
        <span class="step-text">${esc(describeStep ? describeStep(step) : (step.description || JSON.stringify(step)))}</span>
      </div>`).join("");
    return `
      <div class="card" style="margin-top:1rem">
        <div class="card-head">
          <h4>Step-by-step execution</h4>
          <div style="display:flex;gap:.4rem;align-items:center">
            <button type="button" class="btn btn-sm" data-play>Play</button>
            <span class="tiny muted">${steps.length} step(s)</span>
          </div>
        </div>
        <div class="progress" style="margin-bottom:.7rem"><span data-progress></span></div>
        <div class="step-list" data-steps>${rows}</div>
      </div>`;
  }

  function attachPlayback(output, onStep) {
    const steps = output.querySelectorAll("[data-step]");
    if (!steps.length || !onStep) return;
    const progress = output.querySelector("[data-progress]");
    const play = output.querySelector("[data-play]");
    let index = -1;

    function show(next) {
      index = next;
      steps.forEach((el, i) => el.classList.toggle("active", i === index));
      if (steps[index]) steps[index].scrollIntoView({ block: "nearest" });
      if (progress) progress.style.width = ((index + 1) / steps.length * 100) + "%";
      onStep(index);
    }
    steps.forEach(el => el.addEventListener("click", () => show(parseInt(el.dataset.step, 10))));

    if (play) {
      play.addEventListener("click", () => {
        if (state.timer) { clearInterval(state.timer); state.timer = null; play.textContent = "Play"; return; }
        play.textContent = "Pause";
        show(0);
        state.timer = setInterval(() => {
          if (index >= steps.length - 1) {
            clearInterval(state.timer); state.timer = null; play.textContent = "Play";
            return;
          }
          show(index + 1);
        }, 260);
      });
    }
    show(0);
  }

  function textView(text, highlightPositions, patternLength) {
    let html = "";
    for (let i = 0; i < text.length; i++) {
      const inMatch = highlightPositions.some(p => i >= p && i < p + patternLength);
      html += `<span class="ch${inMatch ? " match" : ""}" data-index="${i}">${esc(text[i])}</span>`;
    }
    return html;
  }

  function statChips(pairs) {
    return `<div class="chip-row">${pairs.map(([label, value]) =>
      `<span class="chip">${esc(label)} <strong style="margin-left:.3rem;color:var(--text)">${esc(value)}</strong></span>`).join("")}</div>`;
  }

  /* ------------------------------------------------------- renderers */
  const RENDERERS = {};

  RENDERERS.binary_search = function (data, output) {
    const values = data.input.array;
    const found = data.found;
    output.innerHTML = `
      <div class="card">
        <div class="card-head">
          <h3>Binary Search</h3>
          <span class="chip ${found ? "chip-ok" : "chip-err"}">${found ? `found at index ${data.index}` : "not found"}</span>
        </div>
        ${statChips([["Probes", data.comparisons], ["Array length", values.length],
                     ["Upper bound probes", Math.max(1, values.length.toString(2).length)],
                     ["Recursive depth", data.recursive_depth], ["Naive would need", values.length]])}
        <div class="array-view" id="bs-array" style="margin-top:1rem">
          ${values.map((v, i) => `<span class="array-cell" data-i="${i}">${v}</span>`).join("")}
        </div>
        <p class="muted small" style="margin-top:.8rem">Target = <strong>${esc(data.input.target)}</strong></p>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;

    attachPlayback(output, index => {
      const step = data.steps[index];
      output.querySelectorAll("#bs-array .array-cell").forEach(cell => {
        const i = parseInt(cell.dataset.i, 10);
        cell.classList.toggle("mid", i === step.mid);
        cell.classList.toggle("dead", step.mid !== null && (i < step.low || i > step.high));
        cell.classList.toggle("hit", found && i === data.index);
      });
    });
  };

  RENDERERS.kmp = function (data, output) {
    const text = data.input.text, pattern = data.input.pattern;
    output.innerHTML = `
      <div class="card">
        <div class="card-head">
          <h3>Knuth-Morris-Pratt</h3>
          <span class="chip chip-ok">${data.match_count} match(es)</span>
        </div>
        ${statChips([["Comparisons", data.comparisons], ["Pattern length m", data.pattern.length],
                     ["Naive comparisons", data.naive_comparisons],
                     ["Saving", data.naive_comparisons ? `${(100 - data.comparisons / data.naive_comparisons * 100).toFixed(1)}%` : "-"],
                     ["Positions", data.matches.join(", ") || "-"]])}
        <div class="field" style="margin-top:1rem">
          <label>Pattern</label>
          <div class="text-view">${textView(pattern, [], pattern.length)}</div>
        </div>
        <div class="field">
          <label>Text</label>
          <div class="text-view" id="kmp-text">${textView(text, data.matches, pattern.length)}</div>
        </div>
        <div class="field">
          <label>LPS array (failure function)</label>
          <div class="array-view">
            ${data.lps.map((v, i) => `<span class="array-cell" data-lps="${i}">
              <span class="tiny muted">${i}</span><br>${v}</span>`).join("")}
          </div>
        </div>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;

    attachPlayback(output, index => {
      const step = data.steps[index];
      output.querySelectorAll("#kmp-text .ch").forEach(ch => {
        ch.classList.toggle("active", step && parseInt(ch.dataset.index, 10) === step.i);
      });
    });
  };

  RENDERERS.rabin_karp = function (data, output) {
    const text = data.input.text, pattern = data.input.pattern;
    output.innerHTML = `
      <div class="card">
        <div class="card-head">
          <h3>Rabin-Karp</h3>
          <span class="chip ${data.collisions ? "chip-warn" : "chip-ok"}">${data.collisions} collision(s)</span>
        </div>
        ${statChips([["Hash comparisons", data.hash_comparisons], ["Verification comparisons", data.char_comparisons],
                     ["Pattern hash", data.pattern_hash], ["Matches", data.match_count],
                     ["Agrees with KMP", data.agrees_with_kmp ? "yes" : "no"]])}
        <div class="field" style="margin-top:1rem">
          <label>Text (green = verified match)</label>
          <div class="text-view" id="rk-text">${textView(text, data.matches, pattern.length)}</div>
        </div>
        <div class="field">
          <label>Pattern hash = ${data.pattern_hash} &middot; base 31, modulus 1000003</label>
          <div class="text-view">${textView(pattern, [], pattern.length)}</div>
        </div>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;

    attachPlayback(output, index => {
      const step = data.steps[index];
      output.querySelectorAll("#rk-text .ch").forEach(ch => {
        const position = parseInt(ch.dataset.index, 10);
        ch.classList.toggle("active",
          !!step && position >= step.index && position < step.index + pattern.length);
      });
    });
  };

  RENDERERS.trie = function (data, output) {
    const words = data.input.words;
    output.innerHTML = `
      <div class="card">
        <div class="card-head">
          <h3>Trie insert &amp; prefix search</h3>
          <span class="chip chip-brand">${data.stats.nodes} nodes</span>
        </div>
        ${statChips([["Distinct words", data.stats.distinct_words], ["Nodes", data.stats.nodes],
                     ["Max depth", data.stats.max_depth], ["Characters stored", data.stats.total_characters]])}
        <div class="field" style="margin-top:1rem">
          <label>Suggestions for prefix &ldquo;${esc(data.input.prefix)}&rdquo;</label>
          <div class="chip-row">
            ${data.suggestions.length
              ? data.suggestions.map(s => `<span class="chip chip-ok">${esc(s)}
                  <span class="tiny muted" style="margin-left:.35rem">${s.documents} doc / freq ${s.frequency}</span></span>`).join("")
              : '<span class="muted small">No word starts with this prefix.</span>'}
          </div>
        </div>
        <div class="field">
          <label>Insertion traces (first word)</label>
          <div class="array-view">
            ${(data.insert_traces[0] ? [data.insert_traces[0].word] : []).map(w =>
              [...w].map(c => `<span class="array-cell pat">${esc(c)}</span>`).join("")).join("")}
          </div>
        </div>
        <div class="field">
          <label>Words inserted</label>
          <div class="tag-list">${words.map(w => `<span class="tag">${esc(w)}</span>`).join("")}</div>
        </div>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;
    attachPlayback(output, null);
  };

  RENDERERS.hash = function (data, output) {
    const chain = data.chaining.snapshot, open = data.open_addressing.snapshot;
    output.innerHTML = `
      <div class="card">
        <div class="card-head">
          <h3>Hash Table</h3>
          <span class="chip chip-brand">capacity ${data.input.capacity}</span>
        </div>
        ${statChips([["djb2 hash of probe", data.hash_value], ["Bucket", data.bucket],
                     ["Chaining collisions", data.chaining.stats.collisions],
                     ["Open addressing probes", data.open_addressing.stats.collisions],
                     ["Rehashes", data.chaining.stats.rehashes + data.open_addressing.stats.rehashes]])}
        <div class="grid grid-2" style="margin-top:1rem">
          <div>
            <h4>Separate chaining</h4>
            <div class="bucket-grid">
              ${chain.map((keys, i) => `<div class="bucket${i === data.bucket ? " hit-bucket" : ""}">
                <span class="bucket-idx">bucket ${i}</span>
                ${keys.length ? keys.map(k => `<span class="k">&rarr; ${esc(k)}</span>`).join("") : '<span class="tiny muted">empty</span>'}
              </div>`).join("")}
            </div>
          </div>
          <div>
            <h4>Linear probing</h4>
            <div class="bucket-grid">
              ${open.map((key, i) => `<div class="bucket${i === data.bucket ? " hit-bucket" : ""}">
                <span class="bucket-idx">slot ${i}</span>
                ${key ? `<span class="k">${esc(key)}</span>` : '<span class="tiny muted">empty</span>'}
              </div>`).join("")}
            </div>
          </div>
        </div>
        <p class="muted small" style="margin-top:1rem">
          Lookup of &ldquo;${esc(data.input.probe)}&rdquo;:
          chaining ${data.lookup.chaining ? "hit" : "miss"},
          probing ${data.lookup.open_addressing ? "hit" : "miss"}.
        </p>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;
    attachPlayback(output, null);
  };

  function graphBlock(data, extraHtml) {
    const nodes = data.input.nodes, edges = data.input.edges;
    output.innerHTML = `
      <div class="card">
        <div class="card-head"><h3>${esc(data.title)}</h3></div>
        <div class="graph-canvas-wrap"><canvas class="graph-canvas" id="lab-graph"></canvas></div>
        <div class="graph-legend">
          ${nodes.map(n => `<span><span class="legend-dot" style="background:${nodeColor(n)}"></span>${esc(n)}</span>`).join("")}
        </div>
        ${extraHtml || ""}
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;

    const canvas = output.querySelector("#lab-graph");
    const context = { canvas, nodes, edges, positions: null };
    drawGraph(context, data);
  }

  function nodeColor(node) {
    return window.NexaChart.palette[node.length % window.NexaChart.palette.length];
  }

  function layoutGraph(context) {
    const { nodes } = context;
    const width = context.canvas.clientWidth || 500;
    const height = context.canvas.clientHeight || 460;
    const cx = width / 2, cy = height / 2;
    const radius = Math.min(width, height) / 2 - 60;
    context.positions = {};
    nodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / Math.max(1, nodes.length) - Math.PI / 2;
      context.positions[node] = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) };
    });
  }

  function drawGraph(context, data, visited) {
    if (!context.positions) layoutGraph(context);
    const dpr = window.devicePixelRatio || 1;
    const canvas = context.canvas;
    const width = canvas.clientWidth || 500, height = canvas.clientHeight || 460;
    if (canvas.width !== width * dpr) {
      canvas.width = width * dpr; canvas.height = height * dpr;
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    const seen = new Set(visited || []);
    /* Read the palette off the CSS custom properties so the canvas follows
       the light/dark theme instead of assuming a dark page. */
    const token = (name, fallback) =>
      getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
    const dimEdge = token("--border-strong", "rgba(148,163,208,.4)");
    const dimNode = token("--surface-3", "rgba(148,163,208,.2)");
    const dimLabel = token("--text-3", "#74809f");
    const fontStack = '"Inter var", "Segoe UI", system-ui, sans-serif';

    context.edges.forEach(edge => {
      const a = context.positions[edge[0]], b = context.positions[edge[1]];
      if (!a || !b) return;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = seen.has(edge[0]) && seen.has(edge[1])
        ? "rgba(111,139,255,.75)" : dimEdge;
      ctx.lineWidth = 1.4; ctx.stroke();
      if (edge.length === 3) {
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        ctx.fillStyle = token("--text-2", "rgba(168,179,209,.9)");
        ctx.font = `11px ${fontStack}`;
        ctx.textAlign = "center";
        ctx.fillText(String(edge[2]), mx, my - 5);
      }
    });

    context.nodes.forEach(node => {
      const p = context.positions[node];
      const active = seen.has(node);
      ctx.beginPath();
      ctx.arc(p.x, p.y, active ? 17 : 14, 0, Math.PI * 2);
      ctx.fillStyle = active ? nodeColor(node) : dimNode;
      ctx.fill();
      ctx.strokeStyle = active ? "#fff" : dimEdge;
      ctx.lineWidth = active ? 2 : 1;
      ctx.stroke();
      ctx.fillStyle = active ? "#08122a" : dimLabel;
      ctx.font = `bold 12px ${fontStack}`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(node).slice(0, 2), p.x, p.y);
    });
  }

  RENDERERS.bfs = function (data, output) {
    const levels = (data.levels || []).map((level, i) =>
      `<span class="chip chip-brand">L${i}: ${level.map(esc).join(", ")}</span>`).join("");
    graphBlock(data, `
      <div class="field" style="margin-top:1rem">
        <label>Traversal order</label>
        <div class="tag-list">${data.traversal.map(n => `<span class="tag accent">${esc(n)}</span>`).join("")}</div>
      </div>
      <div class="field">
        <label>BFS levels (FIFO queue drains one level at a time)</label>
        <div class="chip-row">${levels}</div>
      </div>
      <p class="muted small">Edge examinations: ${data.edge_examinations}</p>`);

    attachPlayback(output, index => {
      const visited = data.steps.slice(0, index + 1)
        .filter(s => s.action === "enqueue" || s.action === "dequeue")
        .map(s => String(s.node));
      drawGraph({ canvas: output.querySelector("#lab-graph"),
                  nodes: data.input.nodes, edges: data.input.edges,
                  positions: null }, data, visited);
    });
  };

  RENDERERS.dfs = function (data, output) {
    graphBlock(data, `
      <div class="field" style="margin-top:1rem">
        <label>Traversal order</label>
        <div class="tag-list">${data.traversal.map(n => `<span class="tag accent">${esc(n)}</span>`).join("")}</div>
      </div>
      <p class="muted small">Edge examinations: ${data.edge_examinations}</p>`);
    attachPlayback(output, index => {
      const visited = data.steps.slice(0, index + 1)
        .filter(s => s.action === "visit" || s.action === "call")
        .map(s => String(s.node));
      drawGraph({ canvas: output.querySelector("#lab-graph"),
                  nodes: data.input.nodes, edges: data.input.edges,
                  positions: null }, data, visited);
    });
  };

  RENDERERS.dijkstra = function (data, output) {
    const distances = Object.entries(data.distances || {})
      .sort((a, b) => a[1] - b[1])
      .map(([node, distance]) => `<span class="chip">${esc(node)} &rarr; <strong>${distance}</strong></span>`).join("");
    graphBlock(data, `
      <div class="field" style="margin-top:1rem">
        <label>Settled order (priority queue)</label>
        <div class="tag-list">${(data.settled || []).map(n => `<span class="tag accent">${esc(n)}</span>`).join("")}</div>
      </div>
      <div class="field">
        <label>Final distances</label>
        <div class="chip-row">${distances}</div>
      </div>
      <div class="field">
        <label>Shortest path ${data.goal ? esc(data.goal) : ""}</label>
        <div class="tag-list">${(data.shortest_path || []).map(n => `<span class="tag">${esc(n)}</span>`).join(" -> ") || '<span class="muted small">no target selected</span>'}</div>
        <p class="muted small">Total weight: <strong>${data.shortest_distance !== null && data.shortest_distance !== undefined ? data.shortest_distance : "-"}</strong></p>
      </div>
      <p class="muted small">Relaxations: ${data.relaxations} &middot; heap comparisons: ${data.heap_comparisons}</p>`);

    attachPlayback(output, index => {
      const visited = data.steps.slice(0, index + 1).filter(s => s.action === "settle").map(s => String(s.node));
      drawGraph({ canvas: output.querySelector("#lab-graph"),
                  nodes: data.input.nodes, edges: data.input.edges,
                  positions: null }, data, visited);
    });
  };

  function sortingBlock(data) {
    return `
      <div class="card">
        <div class="card-head">
          <h3>${esc(data.title)}</h3>
          <span class="chip chip-ok">${data.comparisons} comparisons</span>
        </div>
        <div class="field">
          <label>Input</label>
          <div class="array-view" id="sort-in">
            ${data.input.values.map(v => `<span class="array-cell">${v}</span>`).join("")}
          </div>
        </div>
        <div class="field">
          <label>Output</label>
          <div class="array-view" id="sort-out">
            ${data.sorted.map(v => `<span class="array-cell hit">${v}</span>`).join("")}
          </div>
        </div>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;
  }

  RENDERERS.merge_sort = function (data, output) {
    output.innerHTML = sortingBlock(data);
    attachPlayback(output, index => {
      const step = data.steps[index];
      if (!step) return;
      const cells = output.querySelectorAll("#sort-in .array-cell");
      const array = step.array || [];
      cells.forEach((cell, i) => { cell.textContent = array[i] !== undefined ? array[i] : "-"; });
    });
  };

  RENDERERS.quick_sort = function (data, output) {
    output.innerHTML = `
      <div class="card">
        <div class="card-head">
          <h3>Quick Sort</h3>
          <span class="chip chip-ok">${data.comparisons} comparisons</span>
        </div>
        ${statChips([["Partitions", data.partitions], ["Max pivot depth", data.max_depth],
                     ["Space", "O(log n) auxiliary"]])}
        <div class="field" style="margin-top:1rem">
          <label>Input</label>
          <div class="array-view" id="sort-in">
            ${data.input.values.map(v => `<span class="array-cell">${v}</span>`).join("")}
          </div>
        </div>
        <div class="field">
          <label>Output</label>
          <div class="array-view" id="sort-out">
            ${data.sorted.map(v => `<span class="array-cell hit">${v}</span>`).join("")}
          </div>
        </div>
      </div>
      ${stepsPanel(data.steps)}
      ${complexityBlock(data)}`;
    attachPlayback(output, index => {
      const step = data.steps[index];
      if (!step) return;
      const array = step.array || [];
      output.querySelectorAll("#sort-in .array-cell").forEach((cell, i) => {
        cell.textContent = array[i] !== undefined ? array[i] : "-";
        cell.classList.toggle("pivot", i === step.final_index);
      });
    });
  };

  /* ------------------------------------------------------------- boot */
  renderShell();
})();
