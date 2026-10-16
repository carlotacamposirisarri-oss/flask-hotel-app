/* Vestige Intelligence — small progressive enhancements. */
(function () {
  const loading = document.getElementById("loading");

  // Long AI calls: show a calm overlay instead of a frozen page.
  document.addEventListener("submit", (e) => {
    const form = e.target;
    const btn = e.submitter;
    const viaBtn = btn && btn.hasAttribute("data-loading-btn");
    if ((form.hasAttribute("data-loading") || viaBtn) && loading && form.checkValidity()) {
      loading.hidden = false;
    }
  });
  window.addEventListener("pageshow", () => { if (loading) loading.hidden = true; });

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const Vestige = {
    /* Interest network graph (d3 force layout). */
    graph(el) {
      if (!el || !window.d3) return;
      const data = JSON.parse(el.dataset.graph);
      const css = getComputedStyle(document.documentElement);
      const color = {
        client: css.getPropertyValue("--ink"), interest: css.getPropertyValue("--accent"),
        circle: css.getPropertyValue("--olive"), purchase: css.getPropertyValue("--sand-2"),
        peer: css.getPropertyValue("--terra"),
      };
      const w = el.clientWidth, h = el.clientHeight;
      const svg = d3.select(el).append("svg").attr("viewBox", [0, 0, w, h]).attr("width", "100%").attr("height", "100%");
      const sim = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id((d) => d.id).distance((l) => (l.kind === "shared" ? 70 : 95)))
        .force("charge", d3.forceManyBody().strength(-260))
        .force("center", d3.forceCenter(w / 2, h / 2))
        .force("collide", d3.forceCollide().radius((d) => d.size + 14));
      const link = svg.append("g").selectAll("line").data(data.links).join("line")
        .attr("stroke", (l) => (l.kind === "shared" ? color.peer : "#cbbfab"))
        .attr("stroke-opacity", 0.7).attr("stroke-dasharray", (l) => (l.kind === "shared" ? "3 3" : null));
      const node = svg.append("g").selectAll("g").data(data.nodes).join("g")
        .style("cursor", (d) => (d.href ? "pointer" : "grab"))
        .on("click", (_, d) => { if (d.href) window.location = d.href; })
        .call(d3.drag()
          .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
          .on("end", (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));
      node.append("circle").attr("r", (d) => d.size).attr("fill", (d) => color[d.group]).attr("stroke", "#fbf9f4").attr("stroke-width", 2);
      node.append("text").text((d) => d.label).attr("x", (d) => d.size + 4).attr("y", 4);
      sim.on("tick", () => {
        data.nodes.forEach((d) => { d.x = Math.max(20, Math.min(w - 80, d.x)); d.y = Math.max(20, Math.min(h - 20, d.y)); });
        link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
        node.attr("transform", (d) => `translate(${d.x},${d.y})`);
      });
    },

    /* Slide editor: reorder, edit, add, remove; serialises to JSON on save. */
    deckEditor() {
      const root = document.getElementById("slides");
      const form = document.getElementById("deck-form");
      const types = JSON.parse(root.dataset.types);
      let slides = JSON.parse(root.dataset.slides);

      const listText = (s) => {
        if (s.type === "metrics") return (s.metrics || []).map((m) => `${m.label} | ${m.value}`).join("\n");
        if (s.type === "bars") return (s.bars || []).map((b) => `${b.label} | ${b.value}`).join("\n");
        if (s.type === "matrix") return [`# ${(s.columns || []).join(" | ")}`, ...(s.rows || []).map((r) => [r.label, ...(r.values || [])].join(" | "))].join("\n");
        return (s.bullets || []).join("\n");
      };
      const listHint = (t) => (t === "metrics" ? "One per line: label | value" : t === "bars" ? "One per line: label | number"
        : t === "matrix" ? "First line: # Column A | Column B; then: row label | 80 | 40" : "Bullets, one per line");

      function render() {
        root.innerHTML = slides.map((s, i) => `
          <div class="slide-ed" data-i="${i}">
            <div class="se-h"><b>${i + 1}</b>
              <select data-f="type">${types.map((t) => `<option ${t === s.type ? "selected" : ""}>${t}</option>`).join("")}</select>
              <span class="grow"></span>
              <button type="button" class="icon" data-act="up" title="Move up">↑</button>
              <button type="button" class="icon" data-act="down" title="Move down">↓</button>
              <button type="button" class="icon" data-act="del" title="Remove">×</button>
            </div>
            <input data-f="title" value="${esc(s.title)}" placeholder="Title">
            <input data-f="subtitle" value="${esc(s.subtitle)}" placeholder="Subtitle (cover / section)">
            <textarea data-f="body" rows="3" placeholder="Body text">${esc(s.body)}</textarea>
            <textarea data-f="list" rows="3" placeholder="${listHint(s.type)}">${esc(listText(s))}</textarea>
          </div>`).join("");
      }

      function collect() {
        slides = [...root.querySelectorAll(".slide-ed")].map((el) => {
          const get = (f) => el.querySelector(`[data-f="${f}"]`).value;
          const type = get("type");
          const lines = get("list").split("\n").map((x) => x.trim()).filter(Boolean);
          const s = { type, title: get("title"), subtitle: get("subtitle"), body: get("body") };
          if (type === "metrics") s.metrics = lines.map((l) => { const [label, value] = l.split("|"); return { label: (label || "").trim(), value: (value || "").trim() }; });
          else if (type === "bars") s.bars = lines.map((l) => { const [label, value] = l.split("|"); return { label: (label || "").trim(), value: parseFloat(value) || 0 }; });
          else if (type === "matrix") {
            const head = lines.find((l) => l.startsWith("#"));
            s.columns = head ? head.slice(1).split("|").map((x) => x.trim()) : [];
            s.rows = lines.filter((l) => !l.startsWith("#")).map((l) => { const [label, ...vals] = l.split("|").map((x) => x.trim()); return { label, values: vals.map((v) => parseFloat(v) || 0) }; });
          } else s.bullets = lines;
          return s;
        });
      }

      root.addEventListener("click", (e) => {
        const act = e.target.dataset.act;
        if (!act) return;
        collect();
        const i = +e.target.closest(".slide-ed").dataset.i;
        if (act === "del") slides.splice(i, 1);
        if (act === "up" && i > 0) [slides[i - 1], slides[i]] = [slides[i], slides[i - 1]];
        if (act === "down" && i < slides.length - 1) [slides[i + 1], slides[i]] = [slides[i], slides[i + 1]];
        render();
      });
      root.addEventListener("change", (e) => { if (e.target.dataset.f === "type") { collect(); render(); } });
      document.getElementById("add-slide").addEventListener("click", () => { collect(); slides.push({ type: "text", title: "New slide", bullets: [] }); render(); });
      form.addEventListener("submit", () => { collect(); document.getElementById("slides-json").value = JSON.stringify(slides); });
      render();
    },
  };
  window.Vestige = Vestige;
})();
