(() => {
  const config = window.FORGE_ANALYTICS;
  const charts = window.FORGE_CHARTS;
  if (!config || !charts) return;

  const metadataQuery = `
    query AnalysisBuilderMetadata {
      analysisFields {
        key label kind unit groupable
        supportedFunctions { key label }
      }
      analysisCatalog {
        exercises { id name }
        techniques { id name }
      }
    }
  `;
  const analysisQuery = `
    query RunAnalysis($time: TimeAnalysisInput!, $comparison: ComparisonAnalysisInput!) {
      timeAnalysis(input: $time) {
        x { label unit kind } y { label unit kind }
        series { label points { x y } }
      }
      comparisonAnalysis(input: $comparison) {
        x { label unit kind } y { label unit kind }
        series { label points { x y } }
      }
    }
  `;

  const form = document.getElementById("analysis-form");
  const status = document.getElementById("analysis-status");
  const fieldsList = document.getElementById("analysis-fields");
  const timeLines = document.getElementById("time-lines");
  const startInput = document.getElementById("analysis-start");
  const endInput = document.getElementById("analysis-end");
  const exerciseInput = document.getElementById("analysis-exercises");
  const techniqueInput = document.getElementById("analysis-technique");
  let fields = [];

  async function graphql(query, variables = {}) {
    const response = await fetch(config.endpoint, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({query, variables}),
    });
    const payload = await response.json();
    if (!response.ok || payload.errors?.length) {
      throw new Error(payload.errors?.map((error) => error.message).join(" ") || `Erro HTTP ${response.status}`);
    }
    return payload.data;
  }

  function option(value, label, selected = false) {
    const item = document.createElement("option");
    item.value = value;
    item.textContent = label;
    item.selected = selected;
    return item;
  }

  function populateFieldSelect(select, selected) {
    select.replaceChildren(...fields.map((field) => option(field.key, field.label, field.key === selected)));
  }

  function populateFunctions(fieldSelect, functionSelect, selected, numericOutputOnly = false) {
    const field = fields.find((item) => item.key === fieldSelect.value);
    const available = numericOutputOnly && field.kind === "CATEGORY"
      ? field.supportedFunctions.filter((item) => item.key !== "RAW")
      : field.supportedFunctions;
    functionSelect.replaceChildren(...available.map((item) => option(item.key, item.label, item.key === selected)));
    if (!functionSelect.value) functionSelect.selectedIndex = 0;
  }

  function preferredFunction(fieldKey) {
    if (fields.find((field) => field.key === fieldKey)?.kind === "CATEGORY") return "COUNT";
    if (fieldKey === "SET_POSITION") return "COUNT";
    return "AVG";
  }

  function createTimeLine(fieldKey = "WEIGHT", functionKey = "AVG") {
    const row = document.createElement("div");
    row.className = "axis-line";
    const fieldWrap = document.createElement("div");
    fieldWrap.className = "field";
    const fieldLabel = document.createElement("label");
    fieldLabel.textContent = "Campo da linha";
    const fieldSelect = document.createElement("select");
    populateFieldSelect(fieldSelect, fieldKey);
    fieldWrap.append(fieldLabel, fieldSelect);
    const functionWrap = document.createElement("div");
    functionWrap.className = "field";
    const functionLabel = document.createElement("label");
    functionLabel.textContent = "Função";
    const functionSelect = document.createElement("select");
    functionWrap.append(functionLabel, functionSelect);
    populateFunctions(fieldSelect, functionSelect, functionKey, true);
    fieldSelect.addEventListener("change", () => populateFunctions(fieldSelect, functionSelect, preferredFunction(fieldSelect.value), true));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "input-tool danger";
    remove.textContent = "Remover";
    remove.addEventListener("click", () => {
      if (timeLines.children.length > 1) row.remove();
    });
    row.append(fieldWrap, functionWrap, remove);
    timeLines.appendChild(row);
  }

  function renderGroups(container, name, defaultField = "") {
    const groupable = fields.filter((field) => field.groupable);
    container.replaceChildren(...groupable.map((field) => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.name = name;
      input.value = field.key;
      input.checked = field.key === defaultField;
      label.append(input, document.createTextNode(field.label));
      return label;
    }));
  }

  function checkedValues(name) {
    return [...document.querySelectorAll(`input[name="${name}"]:checked`)].map((input) => input.value);
  }

  function selectedExerciseIds() {
    return [...exerciseInput.selectedOptions].map((item) => item.value);
  }

  function lineInputs() {
    return [...timeLines.querySelectorAll(".axis-line")].map((row) => {
      const selects = row.querySelectorAll("select");
      return {field: selects[0].value, function: selects[1].value};
    });
  }

  function renderLegend(container, series) {
    container.replaceChildren(...series.map((item, index) => {
      const label = document.createElement("span");
      label.textContent = item.label;
      label.style.setProperty("--series-color", charts.palette[index % charts.palette.length]);
      return label;
    }));
  }

  function showChart(containerId, emptyId, legendId, data) {
    const empty = document.getElementById(emptyId);
    const hasPoints = data.series.some((series) => series.points.length);
    empty.hidden = hasPoints;
    empty.textContent = hasPoints ? "" : "Nenhum dado encontrado para esta consulta.";
    renderLegend(document.getElementById(legendId), data.series);
    charts.mount(document.getElementById(containerId), data);
  }

  async function runAnalysis() {
    status.textContent = "Executando consultas GraphQL…";
    status.classList.remove("error");
    const xField = document.getElementById("x-field");
    const xFunction = document.getElementById("x-function");
    const yField = document.getElementById("y-field");
    const yFunction = document.getElementById("y-function");
    const common = {
      startDate: startInput.value,
      endDate: endInput.value,
      exerciseIds: selectedExerciseIds(),
      techniqueId: techniqueInput.value || null,
    };
    const data = await graphql(analysisQuery, {
      time: {
        ...common,
        period: document.getElementById("time-period").value,
        lines: lineInputs(),
        groupBy: checkedValues("time-group"),
      },
      comparison: {
        ...common,
        x: {field: xField.value, function: xFunction.value},
        y: {field: yField.value, function: yFunction.value},
        groupBy: checkedValues("comparison-group"),
      },
    });
    showChart("productivity-chart", "time-chart-empty", "time-chart-legend", data.timeAnalysis);
    showChart("relation-chart", "comparison-chart-empty", "comparison-chart-legend", data.comparisonAnalysis);
    document.getElementById("comparison-title").textContent = `${data.comparisonAnalysis.y.label} em função de ${data.comparisonAnalysis.x.label}`;
    status.textContent = "Análise atualizada pela API GraphQL.";
  }

  async function initialize() {
    try {
      const data = await graphql(metadataQuery);
      fields = data.analysisFields;
      fieldsList.replaceChildren(...fields.map((field) => {
        const card = document.createElement("article");
        card.className = "analysis-field-card";
        const title = document.createElement("strong");
        title.textContent = field.label;
        const meta = document.createElement("span");
        meta.textContent = `${field.kind === "NUMBER" ? "Numérico" : "Categoria"}${field.unit ? ` · ${field.unit}` : ""}`;
        const functions = document.createElement("small");
        functions.textContent = field.supportedFunctions.map((item) => item.label).join(", ");
        card.append(title, meta, functions);
        return card;
      }));
      exerciseInput.replaceChildren(...data.analysisCatalog.exercises.map((item) => option(item.id, item.name)));
      techniqueInput.append(...data.analysisCatalog.techniques.map((item) => option(item.id, item.name)));
      startInput.value = config.startDate;
      endInput.value = config.endDate;
      createTimeLine("WEIGHT", "AVG");
      createTimeLine("REST", "AVG");
      createTimeLine("SET_POSITION", "COUNT");
      renderGroups(document.getElementById("time-groups"), "time-group", "EXERCISE");
      renderGroups(document.getElementById("comparison-groups"), "comparison-group", "EXERCISE");
      const xField = document.getElementById("x-field");
      const xFunction = document.getElementById("x-function");
      const yField = document.getElementById("y-field");
      const yFunction = document.getElementById("y-function");
      populateFieldSelect(xField, "SET_POSITION");
      populateFieldSelect(yField, "WEIGHT");
      populateFunctions(xField, xFunction, "RAW");
      populateFunctions(yField, yFunction, "RAW");
      xField.addEventListener("change", () => populateFunctions(xField, xFunction, "RAW"));
      yField.addEventListener("change", () => populateFunctions(yField, yFunction, "RAW"));
      form.hidden = false;
      status.textContent = "Campos carregados. Configure ou execute a análise padrão.";
      await runAnalysis();
    } catch (error) {
      status.textContent = `Não foi possível carregar a análise: ${error.message}`;
      status.classList.add("error");
    }
  }

  document.getElementById("add-time-line").addEventListener("click", () => createTimeLine());
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await runAnalysis();
    } catch (error) {
      status.textContent = `Erro na consulta: ${error.message}`;
      status.classList.add("error");
    }
  });
  initialize();
})();
