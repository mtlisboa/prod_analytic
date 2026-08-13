(() => {
  const field = document.querySelector("[data-exercise-search-url]");
  if (!field) return;

  const select = field.querySelector("select");
  const input = field.querySelector("#exercise-search");
  const results = field.querySelector("#exercise-results");
  const url = field.dataset.exerciseSearchUrl;
  const selected = select.options[select.selectedIndex];
  let timer;
  let request;

  if (selected?.value) input.value = selected.textContent.trim();

  function closeResults() {
    results.hidden = true;
    input.setAttribute("aria-expanded", "false");
  }

  function showStatus(message) {
    results.replaceChildren();
    const status = document.createElement("div");
    status.className = "exercise-search-status";
    status.textContent = message;
    results.append(status);
    results.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }

  async function search(query) {
    request?.abort();
    request = new AbortController();
    showStatus("Buscando…");
    try {
      const response = await fetch(`${url}?q=${encodeURIComponent(query)}`, {
        headers: { Accept: "application/json" }, signal: request.signal,
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      results.replaceChildren();
      if (!data.results.length) return showStatus("Nenhum exercício encontrado.");
      data.results.forEach(exercise => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "exercise-result";
        button.setAttribute("role", "option");
        const name = document.createElement("span");
        const group = document.createElement("small");
        name.textContent = exercise.name;
        group.textContent = exercise.muscle_group;
        button.append(name, group);
        button.addEventListener("click", () => {
          select.replaceChildren(new Option(exercise.name, exercise.id, true, true));
          input.value = exercise.name;
          input.setCustomValidity("");
          closeResults();
        });
        results.append(button);
      });
    } catch (error) {
      if (error.name !== "AbortError") showStatus("Não foi possível realizar a busca.");
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    select.value = "";
    input.setCustomValidity("Selecione um exercício da lista.");
    const query = input.value.trim();
    if (!query) return closeResults();
    timer = setTimeout(() => search(query), 300);
  });
  input.addEventListener("focus", () => { if (input.value.trim() && !select.value) search(input.value.trim()); });
  document.addEventListener("click", event => { if (!field.contains(event.target)) closeResults(); });
})();
