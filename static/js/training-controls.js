(() => {
  const list = document.querySelector("#sets-list");
  const modal = document.querySelector("#set-modal");
  const trainingForm = document.querySelector("#training-form");
  if (!list || !modal) return;
  const total = document.querySelector("#id_sets-TOTAL_FORMS");
  const modalFields = document.querySelector("#modal-fields");
  const timerStates = new WeakMap();
  let activeCard = null;
  let snapshot = null;

  function visibleCards() { return [...list.querySelectorAll("[data-set-form]")].filter(card => !card.classList.contains("removed")); }
  function renumber() { visibleCards().forEach((card, index) => { card.querySelector("[name$='-position']").value = index + 1; card.querySelector(".set-number").textContent = `Série ${index + 1}`; }); }
  function summary(card) {
    const value = suffix => card.querySelector(`[name$='-${suffix}']`)?.value;
    const partial = Number(value("partial_reps") || 0);
    const repsText = `${value("reps") || 0} reps${partial ? ` (${partial} parciais)` : ""}`;
    card.querySelector("[data-summary]").textContent = `${value("weight_kg") || 0} kg · ${repsText} · ${value("execution_time_seconds") || 0}s execução · ${value("rest_time_seconds") || 0}s descanso`;
  }

  function timerState(card) {
    if (!timerStates.has(card)) timerStates.set(card, { elapsedMs: 0, startedAt: null, interval: null });
    return timerStates.get(card);
  }

  function formatTimer(milliseconds) {
    const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
    const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
    const seconds = String(totalSeconds % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function renderTimer(card) {
    if (card !== activeCard) return;
    const state = timerState(card);
    const elapsed = state.startedAt ? state.elapsedMs + (Date.now() - state.startedAt) : state.elapsedMs;
    const display = modalFields.querySelector("[data-rest-timer-display]");
    if (display) display.textContent = formatTimer(elapsed);
  }

  function setRestSeconds(input, elapsedMs) {
    input.value = Math.max(0, Math.round(elapsedMs / 1000));
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function startTimer(card) {
    const state = timerState(card);
    if (state.startedAt) return;
    if (state.elapsedMs === 0) {
      const input = modalFields.querySelector("[name$='-rest_time_seconds']");
      if (input) input.value = 0;
    }
    state.startedAt = Date.now();
    state.interval = window.setInterval(() => renderTimer(card), 250);
    renderTimer(card);
  }

  function pauseTimer(card) {
    const state = timerState(card);
    if (state.startedAt) {
      state.elapsedMs += Date.now() - state.startedAt;
      state.startedAt = null;
    }
    if (state.interval) window.clearInterval(state.interval);
    state.interval = null;
    const input = modalFields.querySelector("[name$='-rest_time_seconds']");
    if (input) setRestSeconds(input, state.elapsedMs);
    renderTimer(card);
  }

  function resetTimer(card) {
    const state = timerState(card);
    if (state.interval) window.clearInterval(state.interval);
    state.elapsedMs = 0;
    state.startedAt = null;
    state.interval = null;
    const input = modalFields.querySelector("[name$='-rest_time_seconds']");
    if (input) input.value = 0;
    renderTimer(card);
  }

  function validateReps() {
    const reps = modalFields.querySelector("[name$='-reps']");
    const partial = modalFields.querySelector("[name$='-partial_reps']");
    if (!reps || !partial) return true;
    const invalid = Number(partial.value || 0) > Number(reps.value || 0);
    partial.setCustomValidity(invalid ? "As repetições parciais não podem ser maiores que o total de repetições." : "");
    return !invalid;
  }

  function close(save) {
    if (activeCard) pauseTimer(activeCard);
    if (!save && snapshot) [...modalFields.querySelectorAll("input,select")].forEach((field, i) => { field.value = snapshot[i]; });
    while (modalFields.firstChild) activeCard.querySelector(".set-fields").append(modalFields.firstChild);
    if (save) summary(activeCard);
    timerStates.delete(activeCard);
    modal.close();
    activeCard = null;
  }

  function open(card) {
    activeCard = card;
    const fields = card.querySelector(".set-fields");
    [...fields.children].forEach(node => { if (!node.matches("input[type=hidden], input[type=checkbox]")) modalFields.append(node); });
    snapshot = [...modalFields.querySelectorAll("input,select")].map(field => field.value);
    modal.querySelector("#modal-title").textContent = card.querySelector(".set-number").textContent;
    renderTimer(card);
    modal.showModal();
  }

  list.addEventListener("click", event => {
    const card = event.target.closest("[data-set-form]");
    if (!card) return;
    if (event.target.closest(".edit-set")) open(card);
    if (event.target.closest(".remove-set")) {
      if (visibleCards().length === 1) return;
      const deletion = card.querySelector("[name$='-DELETE']");
      deletion.checked = true;
      card.classList.add("removed");
      renumber();
    }
  });

  modal.addEventListener("click", event => {
    if (!activeCard) return;
    if (event.target.closest("[data-rest-timer-start]")) startTimer(activeCard);
    if (event.target.closest("[data-rest-timer-pause]")) pauseTimer(activeCard);
    if (event.target.closest("[data-rest-timer-reset]")) resetTimer(activeCard);
  });

  modalFields.addEventListener("input", event => {
    if (event.target.matches("[name$='-reps'], [name$='-partial_reps']")) validateReps();
  });

  document.querySelector("#add-set").addEventListener("click", () => {
    const index = Number(total.value);
    const html = document.querySelector("#empty-set-template").innerHTML.replaceAll("__prefix__", index);
    list.insertAdjacentHTML("beforeend", html);
    total.value = index + 1;
    const card = list.lastElementChild;
    const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    card.querySelector("[name$='-performed_at']").value = now;
    card.querySelector("[name$='-rest_time_seconds']").value = 60;
    card.querySelector("[name$='-reps']").value = 0;
    card.querySelector("[name$='-partial_reps']").value = 0;
    renumber();
    open(card);
  });

  modal.querySelector(".modal-save").onclick = () => {
    validateReps();
    if ([...modalFields.querySelectorAll("input,select")].every(field => field.reportValidity())) close(true);
  };
  modal.querySelector(".modal-cancel").onclick = () => close(false);
  modal.querySelector(".modal-close").onclick = () => close(false);
  modal.addEventListener("cancel", event => { event.preventDefault(); close(false); });
  trainingForm?.addEventListener("submit", () => { if (activeCard) pauseTimer(activeCard); });

  visibleCards().forEach(summary);
  renumber();
})();
