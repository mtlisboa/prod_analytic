(() => {
  const config = window.FORGE_SIMULATION_ANALYTICS;
  const charts = window.FORGE_CHARTS;
  if (!config || !charts) return;

  const form = document.getElementById("simulation-analysis-form");
  const status = document.getElementById("simulation-analysis-status");
  const fields = new Map(config.fields.map((field) => [field.key, field]));
  const input = (id) => document.getElementById(id);
  const option = (item, selected = false) => {
    const element = document.createElement("option");
    element.value = item.key;
    element.textContent = item.label;
    element.selected = selected;
    return element;
  };

  function populate(select, items, selected) {
    select.replaceChildren(...items.map((item) => option(item, item.key === selected)));
  }

  function fieldOptions(keys) {
    return keys.map((key) => fields.get(key));
  }

  function renderMetrics() {
    input("simulation-time-metrics").replaceChildren(...config.timeMetrics.map((key) => {
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.name = "simulation-time-metric";
      checkbox.value = key;
      checkbox.checked = ["accuracy", "effective_time", "rested_time"].includes(key);
      label.append(checkbox, document.createTextNode(fields.get(key).label));
      return label;
    }));
  }

  function commonParams() {
    const params = new URLSearchParams({
      start_date: input("simulation-start").value,
      end_date: input("simulation-end").value,
    });
    if (input("simulation-subject").value) params.set("subject", input("simulation-subject").value);
    if (input("simulation-goal").value) params.set("meta", input("simulation-goal").value);
    return params;
  }

  async function fetchData(endpoint, params) {
    const response = await fetch(`${endpoint}?${params}`, {credentials: "same-origin"});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `Erro HTTP ${response.status}`);
    return payload;
  }

  function renderLegend(id, series) {
    input(id).replaceChildren(...series.filter((item) => item.points.length).map((item, index) => {
      const label = document.createElement("span");
      label.textContent = item.label;
      label.style.setProperty("--series-color", charts.palette[index % charts.palette.length]);
      return label;
    }));
  }

  function renderChart(chartId, emptyId, legendId, data) {
    const chart = input(chartId);
    const empty = input(emptyId);
    const hasPoints = data.series.some((series) => series.points.length);
    chart.hidden = !hasPoints;
    chart.style.display = hasPoints ? "block" : "none";
    empty.hidden = hasPoints;
    empty.style.display = hasPoints ? "none" : "grid";
    empty.textContent = hasPoints ? "" : "Nenhum simulado encontrado para estes filtros.";
    renderLegend(legendId, data.series);
    if (hasPoints) charts.mount(chart, data);
    else chart.replaceChildren();
  }

  async function run() {
    if (!input("simulation-start").value || !input("simulation-end").value) throw new Error("Informe o período da análise.");
    const metrics = [...document.querySelectorAll('input[name="simulation-time-metric"]:checked')].map((item) => item.value);
    if (!metrics.length) throw new Error("Selecione ao menos um índice para o gráfico temporal.");
    status.textContent = "Atualizando os dois gráficos…";
    status.classList.remove("error");

    const timeParams = commonParams();
    metrics.forEach((metric) => timeParams.append("metric", metric));
    timeParams.set("period", input("simulation-period").value);
    timeParams.set("group_by", input("simulation-time-group").value);
    const dynamicParams = commonParams();
    dynamicParams.set("x", input("simulation-x").value);
    dynamicParams.set("y", input("simulation-y").value);
    dynamicParams.set("aggregation", input("simulation-aggregation").value);
    dynamicParams.set("group_by", input("simulation-dynamic-group").value);

    const [timeData, dynamicData] = await Promise.all([
      fetchData(config.timeEndpoint, timeParams),
      fetchData(config.dynamicEndpoint, dynamicParams),
    ]);
    renderChart("simulation-time-chart", "simulation-time-empty", "simulation-time-legend", timeData);
    renderChart("simulation-dynamic-chart", "simulation-dynamic-empty", "simulation-dynamic-legend", dynamicData);
    input("simulation-dynamic-title").textContent = `${dynamicData.y.label} por ${dynamicData.x.label.toLowerCase()}`;
    status.textContent = "Análise atualizada.";
  }

  function initialize() {
    input("simulation-start").value = config.startDate;
    input("simulation-end").value = config.endDate;
    populate(input("simulation-period"), config.periods, "daily");
    populate(input("simulation-time-group"), config.groups, "none");
    populate(input("simulation-x"), fieldOptions(config.xFields), "subject");
    populate(input("simulation-y"), fieldOptions(config.yFields), "accuracy");
    populate(input("simulation-aggregation"), config.aggregations, "avg");
    populate(input("simulation-dynamic-group"), config.groups, "none");
    renderMetrics();
    run().catch(showError);
  }

  function showError(error) {
    status.textContent = `Não foi possível carregar a análise: ${error.message}`;
    status.classList.add("error");
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    run().catch(showError);
  });
  initialize();
})();
