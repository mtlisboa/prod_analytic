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
  const comparisonLines = document.getElementById("comparison-lines");
  const startInput = document.getElementById("analysis-start");
  const endInput = document.getElementById("analysis-end");
  const exerciseSearchInput = document.getElementById("analysis-exercise-search");
  const exerciseResults = document.getElementById("analysis-exercise-results");
  const selectedExercisesContainer = document.getElementById("analysis-selected-exercises");
  const techniqueInput = document.getElementById("analysis-technique");
  let fields = [];
  let exercises = [];
  const selectedExercises = new Set();

  async function graphql(query, variables = {}) {
    const response = await fetch(config.endpoint, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({query, variables}),
    });
    let payload;
    try {
      payload = await response.json();
    } catch (_error) {
      throw new Error(`A API retornou uma resposta inválida (HTTP ${response.status}).`);
    }
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
    createAxisLine(timeLines, fieldKey, functionKey);
  }

  function createComparisonLine(fieldKey = "WEIGHT", functionKey = "RAW") {
    createAxisLine(comparisonLines, fieldKey, functionKey);
  }

  function createAxisLine(container, fieldKey, functionKey) {
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
      if (container.children.length > 1) row.remove();
    });
    row.append(fieldWrap, functionWrap, remove);
    container.appendChild(row);
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
    return [...selectedExercises];
  }

  function normalizeSearch(value) {
    return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }

  function closeExerciseResults() {
    exerciseResults.hidden = true;
    exerciseSearchInput.setAttribute("aria-expanded", "false");
  }

  function renderSelectedExercises() {
    if (!selectedExercises.size) {
      const all = document.createElement("span");
      all.className = "selected-exercises-empty";
      all.textContent = "Todos os exercícios";
      selectedExercisesContainer.replaceChildren(all);
      return;
    }

    selectedExercisesContainer.replaceChildren(...[...selectedExercises].map((id) => {
      const exercise = exercises.find((item) => String(item.id) === id);
      const chip = document.createElement("span");
      chip.className = "selected-exercise-chip";
      chip.append(document.createTextNode(exercise?.name || id));
      const remove = document.createElement("button");
      remove.type = "button";
      remove.setAttribute("aria-label", `Remover ${exercise?.name || "exercício"} do filtro`);
      remove.textContent = "×";
      remove.addEventListener("click", () => {
        selectedExercises.delete(id);
        renderSelectedExercises();
        renderExerciseResults(exerciseSearchInput.value);
      });
      chip.append(remove);
      return chip;
    }));
  }

  function addExercise(id) {
    selectedExercises.add(String(id));
    exerciseSearchInput.value = "";
    closeExerciseResults();
    renderSelectedExercises();
    exerciseSearchInput.focus();
  }

  function renderExerciseResults(query = "") {
    const normalizedQuery = normalizeSearch(query.trim());
    const matches = exercises
      .filter((item) => !selectedExercises.has(String(item.id)))
      .filter((item) => !normalizedQuery || normalizeSearch(item.name).includes(normalizedQuery))
      .slice(0, 12);

    if (!matches.length) {
      const message = document.createElement("div");
      message.className = "exercise-search-status";
      message.textContent = exercises.length ? "Nenhum exercício disponível." : "Nenhum exercício cadastrado.";
      exerciseResults.replaceChildren(message);
    } else {
      exerciseResults.replaceChildren(...matches.map((exercise) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "exercise-result";
        button.setAttribute("role", "option");
        button.textContent = exercise.name;
        button.addEventListener("click", () => addExercise(exercise.id));
        return button;
      }));
    }
    exerciseResults.hidden = false;
    exerciseSearchInput.setAttribute("aria-expanded", "true");
  }

  function lineInputs(container) {
    return [...container.querySelectorAll(".axis-line")].map((row) => {
      const selects = row.querySelectorAll("select");
      return {field: selects[0].value, function: selects[1].value};
    });
  }

  function renderLegend(container, series) {
    container.replaceChildren(...series.filter((item) => item.points?.length).map((item, index) => {
      const label = document.createElement("span");
      label.textContent = item.label;
      label.style.setProperty("--series-color", charts.palette[index % charts.palette.length]);
      return label;
    }));
  }

  function showChart(containerId, emptyId, legendId, rawData) {
    const container = document.getElementById(containerId);
    const empty = document.getElementById(emptyId);
    const data = charts.normalizeData ? charts.normalizeData(rawData) : rawData;
    const hasPoints = Boolean(data?.series?.some((series) => series.points?.length));

    empty.hidden = hasPoints;
    empty.style.display = hasPoints ? "none" : "grid";
    empty.textContent = hasPoints ? "" : "Nenhum dado encontrado para esta consulta.";

    container.hidden = !hasPoints;
    container.style.display = hasPoints ? "block" : "none";
    renderLegend(document.getElementById(legendId), data?.series || []);

    if (hasPoints) charts.mount(container, data);
    else container.replaceChildren();
  }

  async function runAnalysis() {
    if (!startInput.value || !endInput.value) {
      throw new Error("Informe o período da análise.");
    }

    status.textContent = "Executando consultas GraphQL…";
    status.classList.remove("error");
    const xField = document.getElementById("x-field");
    const xFunction = document.getElementById("x-function");
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
        lines: lineInputs(timeLines),
        groupBy: checkedValues("time-group"),
      },
      comparison: {
        ...common,
        x: {field: xField.value, function: xFunction.value},
        lines: lineInputs(comparisonLines),
        groupBy: checkedValues("comparison-group"),
      },
    });

    if (!data?.timeAnalysis || !data?.comparisonAnalysis) {
      throw new Error("A API não retornou os dados esperados para os gráficos.");
    }

    showChart("productivity-chart", "time-chart-empty", "time-chart-legend", data.timeAnalysis);
    showChart("relation-chart", "comparison-chart-empty", "comparison-chart-legend", data.comparisonAnalysis);
    const comparisonLabels = lineInputs(comparisonLines).map((line) => fields.find((field) => field.key === line.field)?.label);
    document.getElementById("comparison-title").textContent = `${comparisonLabels.join(" + ")} em função de ${data.comparisonAnalysis.x.label}`;
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
      exercises = data.analysisCatalog.exercises;
      renderSelectedExercises();
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
      populateFieldSelect(xField, "SET_POSITION");
      populateFunctions(xField, xFunction, "RAW");
      xField.addEventListener("change", () => populateFunctions(xField, xFunction, "RAW"));
      createComparisonLine("WEIGHT", "RAW");
      createComparisonLine("REST", "RAW");
      form.hidden = false;
      status.textContent = "Campos carregados. Configure ou execute a análise padrão.";
      await runAnalysis();
    } catch (error) {
      status.textContent = `Não foi possível carregar a análise: ${error.message}`;
      status.classList.add("error");
    }
  }

  document.getElementById("add-time-line").addEventListener("click", () => createTimeLine());
  document.getElementById("add-comparison-line").addEventListener("click", () => createComparisonLine());
  exerciseSearchInput.addEventListener("input", () => renderExerciseResults(exerciseSearchInput.value));
  exerciseSearchInput.addEventListener("focus", () => renderExerciseResults(exerciseSearchInput.value));
  exerciseSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeExerciseResults();
    if (event.key === "Enter" && !exerciseResults.hidden) {
      const firstResult = exerciseResults.querySelector("button");
      if (firstResult) {
        event.preventDefault();
        firstResult.click();
      }
    }
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".analysis-exercise-filter")) closeExerciseResults();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await runAnalysis();
    } catch (error) {
      console.error("Erro ao executar análise", error);
      status.textContent = `Erro na consulta: ${error.message}`;
      status.classList.add("error");
    }
  });
  initialize();
})();
