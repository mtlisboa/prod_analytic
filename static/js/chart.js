(() => {
  const NS = "http://www.w3.org/2000/svg";
  const palette = ["#769d17", "#3969ac", "#da7c30", "#7a4eab", "#c43d4b", "#16837a", "#b05b91", "#697079"];
  const tooltip = document.createElement("div");
  tooltip.className = "chart-tooltip";
  tooltip.hidden = true;
  document.body.appendChild(tooltip);

  function showTooltip(event, data, series, point, color) {
    const title = document.createElement("span");
    title.className = "chart-tooltip-title";
    title.textContent = series.label;
    const xValue = document.createElement("span");
    xValue.textContent = `${data.x.label}: ${point.x}${data.x.unit ? ` ${data.x.unit}` : ""}`;
    const yValue = document.createElement("strong");
    yValue.className = "chart-tooltip-y";
    yValue.style.borderLeftColor = color;
    yValue.textContent = `${data.y.label}: ${point.y}${data.y.unit ? ` ${data.y.unit}` : ""}`;
    tooltip.replaceChildren(title, xValue, yValue);
    tooltip.hidden = false;
    const left = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 10);
    const top = Math.max(10, event.clientY - tooltip.offsetHeight - 14);
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function hideTooltip() {
    tooltip.hidden = true;
  }

  function svgElement(name, attributes = {}, text = "") {
    const element = document.createElementNS(NS, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== "") element.textContent = text;
    return element;
  }

  function unique(values) {
    return [...new Set(values.map((value) => String(value)))];
  }

  function sampledIndexes(length, limit = 7) {
    if (length <= limit) return Array.from({length}, (_, index) => index);
    const indexes = new Set([0, length - 1]);
    for (let index = 1; index < limit - 1; index++) indexes.add(Math.round(index * (length - 1) / (limit - 1)));
    return [...indexes].sort((a, b) => a - b);
  }

  function renderChart(container, data) {
    if (!container || !data.series?.length) return;
    const width = Math.max(container.clientWidth, 320);
    const height = Math.max(container.clientHeight, 240);
    const pad = {top: 18, right: 28, bottom: 68, left: 76};
    const chartWidth = width - pad.left - pad.right;
    const chartHeight = height - pad.top - pad.bottom;
    const points = data.series.flatMap((series) => series.points);
    if (!points.length) return;

    const xCategories = data.x.kind === "category" ? unique(points.map((point) => point.x)) : [];
    const yCategories = data.y.kind === "category" ? unique(points.map((point) => point.y)) : [];
    const numericX = points.map((point) => Number(point.x));
    const numericY = points.map((point) => Number(point.y));
    const minX = data.x.kind === "number" ? Math.min(...numericX, 0) : 0;
    const maxX = data.x.kind === "number" ? Math.max(...numericX, 1) : Math.max(xCategories.length - 1, 1);
    const minY = data.y.kind === "number" ? Math.min(...numericY, 0) : 0;
    const maxY = data.y.kind === "number" ? Math.max(...numericY, 1) * 1.08 : Math.max(yCategories.length - 1, 1);
    const xValue = (value) => data.x.kind === "category" ? xCategories.indexOf(String(value)) : Number(value);
    const yValue = (value) => data.y.kind === "category" ? yCategories.indexOf(String(value)) : Number(value);
    const xPixel = (value) => pad.left + ((xValue(value) - minX) / Math.max(maxX - minX, 1)) * chartWidth;
    const yPixel = (value) => pad.top + chartHeight - ((yValue(value) - minY) / Math.max(maxY - minY, 1)) * chartHeight;

    const svg = svgElement("svg", {viewBox: `0 0 ${width} ${height}`, preserveAspectRatio: "xMidYMid meet", "aria-hidden": "true"});
    const grid = svgElement("g", {stroke: "#e2e1d9", "stroke-width": "1"});
    const labels = svgElement("g", {fill: "#777c72", "font-size": "11", "font-family": "DM Sans, sans-serif"});

    const yTicks = data.y.kind === "category"
      ? sampledIndexes(yCategories.length).map((index) => ({value: index, label: yCategories[index]}))
      : Array.from({length: 5}, (_, index) => {
          const value = minY + ((maxY - minY) / 4) * index;
          return {value, label: value.toFixed(value < 10 ? 1 : 0)};
        });
    yTicks.forEach((tick) => {
      const y = pad.top + chartHeight - ((tick.value - minY) / Math.max(maxY - minY, 1)) * chartHeight;
      grid.appendChild(svgElement("line", {x1: pad.left, y1: y, x2: width - pad.right, y2: y}));
      labels.appendChild(svgElement("text", {x: pad.left - 10, y: y + 4, "text-anchor": "end"}, tick.label));
    });

    const xTicks = data.x.kind === "category"
      ? sampledIndexes(xCategories.length).map((index) => ({value: index, label: xCategories[index]}))
      : Array.from({length: 5}, (_, index) => {
          const value = minX + ((maxX - minX) / 4) * index;
          return {value, label: value.toFixed(value < 10 ? 1 : 0)};
        });
    xTicks.forEach((tick) => {
      const x = pad.left + ((tick.value - minX) / Math.max(maxX - minX, 1)) * chartWidth;
      labels.appendChild(svgElement("text", {x, y: height - 40, "text-anchor": "middle"}, tick.label));
    });
    labels.appendChild(svgElement("text", {x: pad.left + chartWidth / 2, y: height - 8, "text-anchor": "middle", "font-weight": "700"}, `${data.x.label}${data.x.unit ? ` (${data.x.unit})` : ""}`));
    const yTitle = svgElement("text", {x: 15, y: pad.top + chartHeight / 2, transform: `rotate(-90 15 ${pad.top + chartHeight / 2})`, "text-anchor": "middle", "font-weight": "700"}, `${data.y.label}${data.y.unit ? ` (${data.y.unit})` : ""}`);
    labels.appendChild(yTitle);
    svg.append(grid, labels);

    data.series.forEach((series, seriesIndex) => {
      const color = palette[seriesIndex % palette.length];
      const ordered = [...series.points];
      if (data.x.kind === "number") ordered.sort((a, b) => Number(a.x) - Number(b.x));
      const path = ordered.map((point, index) => `${index ? "L" : "M"} ${xPixel(point.x)} ${yPixel(point.y)}`).join(" ");
      const visiblePath = svgElement("path", {d: path, fill: "none", stroke: color, "stroke-width": "3", "stroke-linecap": "round", "stroke-linejoin": "round", "vector-effect": "non-scaling-stroke"});
      const hitPath = svgElement("path", {d: path, fill: "none", stroke: "transparent", "stroke-width": "18", "stroke-linecap": "round", "stroke-linejoin": "round", "pointer-events": "stroke", "vector-effect": "non-scaling-stroke"});
      const projected = ordered.map((point) => ({point, x: xPixel(point.x), y: yPixel(point.y)}));
      hitPath.addEventListener("mousemove", (event) => {
        const rect = svg.getBoundingClientRect();
        const mouseX = ((event.clientX - rect.left) / rect.width) * width;
        const mouseY = ((event.clientY - rect.top) / rect.height) * height;
        const nearest = projected.reduce((best, candidate) => {
          const distance = Math.hypot(candidate.x - mouseX, candidate.y - mouseY);
          return !best || distance < best.distance ? {...candidate, distance} : best;
        }, null);
        visiblePath.setAttribute("stroke-width", "5");
        if (nearest) showTooltip(event, data, series, nearest.point, color);
      });
      hitPath.addEventListener("mouseleave", () => {
        visiblePath.setAttribute("stroke-width", "3");
        hideTooltip();
      });
      svg.append(visiblePath, hitPath);
      ordered.forEach((point) => {
        const circle = svgElement("circle", {cx: xPixel(point.x), cy: yPixel(point.y), r: "5", fill: color, stroke: "#fff", "stroke-width": "2", "vector-effect": "non-scaling-stroke"});
        circle.appendChild(svgElement("title", {}, `${series.label}\n${data.x.label}: ${point.x}${data.x.unit ? ` ${data.x.unit}` : ""}\n${data.y.label}: ${point.y}${data.y.unit ? ` ${data.y.unit}` : ""}`));
        circle.addEventListener("mouseenter", (event) => {
          circle.setAttribute("r", "8");
          showTooltip(event, data, series, point, color);
        });
        circle.addEventListener("mousemove", (event) => showTooltip(event, data, series, point, color));
        circle.addEventListener("mouseleave", () => {
          circle.setAttribute("r", "5");
          hideTooltip();
        });
        svg.appendChild(circle);
      });
    });
    container.replaceChildren(svg);
  }

  function mountChart(container, data) {
    if (!container || !data) return;
    renderChart(container, data);
    if (window.ResizeObserver) {
      let frame;
      new ResizeObserver(() => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => renderChart(container, data));
      }).observe(container);
    }
  }

  document.querySelectorAll(".chart-legend").forEach((legend) => {
    legend.querySelectorAll("[data-series-color]").forEach((item, index) => {
      item.style.setProperty("--series-color", palette[index % palette.length]);
    });
  });

  const time = window.FORGE_CHART;
  if (time) {
    mountChart(document.getElementById("productivity-chart"), {
      x: {label: "Tempo", unit: "", kind: "category"},
      y: {label: "Valores", unit: "", kind: "number"},
      series: time.series.map((series) => ({
        label: series.label,
        points: time.labels.map((label, index) => ({x: label, y: series.values[index]})),
      })),
    });
  }
  mountChart(document.getElementById("relation-chart"), window.FORGE_RELATION_CHART);
})();
