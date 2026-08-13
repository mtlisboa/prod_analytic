(() => {
  const canvas = document.getElementById("productivity-chart");
  if (!canvas || !window.FORGE_CHART) return;
  const data = window.FORGE_CHART;
  const ctx = canvas.getContext("2d");

  function draw() {
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * ratio;
    canvas.height = rect.height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    const w = rect.width, h = rect.height;
    const pad = { top: 20, right: 18, bottom: 44, left: 46 };
    const cw = w - pad.left - pad.right, ch = h - pad.top - pad.bottom;
    const max = Math.max(...data.values, 1) * 1.15;

    ctx.clearRect(0, 0, w, h);
    ctx.font = "11px DM Sans";
    ctx.fillStyle = "#858980";
    ctx.strokeStyle = "#e2e1d9";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (ch / 4) * i;
      const value = max - (max / 4) * i;
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
      ctx.fillText(value.toFixed(value < 10 ? 1 : 0), 4, y + 4);
    }
    const step = data.values.length > 1 ? cw / (data.values.length - 1) : cw;
    const points = data.values.map((value, i) => ({x: data.values.length > 1 ? pad.left + i * step : pad.left + cw / 2, y: pad.top + ch - (value / max) * ch}));

    const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + ch);
    gradient.addColorStop(0, "rgba(201,244,90,.35)"); gradient.addColorStop(1, "rgba(201,244,90,0)");
    ctx.beginPath(); ctx.moveTo(points[0].x, pad.top + ch); points.forEach(p => ctx.lineTo(p.x, p.y)); ctx.lineTo(points.at(-1).x, pad.top + ch); ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();
    ctx.beginPath(); points.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)); ctx.strokeStyle = "#769d17"; ctx.lineWidth = 3; ctx.lineJoin = "round"; ctx.stroke();
    points.forEach((p, i) => {
      ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI * 2); ctx.fillStyle = "#c9f45a"; ctx.fill(); ctx.strokeStyle = "#26300f"; ctx.lineWidth = 2; ctx.stroke();
      if (data.values.length <= 8 || i % Math.ceil(data.values.length / 7) === 0) {
        ctx.fillStyle = "#858980"; ctx.textAlign = "center"; ctx.fillText(data.labels[i], p.x, h - 14);
      }
    });
  }
  let timer;
  window.addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(draw, 80); });
  draw();
})();
