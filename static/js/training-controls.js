(() => {
  const list = document.querySelector("#sets-list");
  const modal = document.querySelector("#set-modal");
  if (!list || !modal) return;
  const total = document.querySelector("#id_sets-TOTAL_FORMS");
  const modalFields = document.querySelector("#modal-fields");
  let activeCard = null;
  let snapshot = null;

  function visibleCards() { return [...list.querySelectorAll("[data-set-form]")].filter(card => !card.classList.contains("removed")); }
  function renumber() { visibleCards().forEach((card, index) => { card.querySelector("[name$='-position']").value = index + 1; card.querySelector(".set-number").textContent = `Série ${index + 1}`; }); }
  function summary(card) {
    const value = suffix => card.querySelector(`[name$='-${suffix}']`)?.value;
    card.querySelector("[data-summary]").textContent = `${value("weight_kg") || 0} kg · ${value("execution_time_seconds") || 0}s execução · ${value("rest_time_seconds") || 0}s descanso`;
  }
  function close(save) {
    if (!save && snapshot) [...modalFields.querySelectorAll("input,select")].forEach((field, i) => { field.value = snapshot[i]; });
    while (modalFields.firstChild) activeCard.querySelector(".set-fields").append(modalFields.firstChild);
    if (save) summary(activeCard);
    modal.close(); activeCard = null;
  }
  function open(card) {
    activeCard = card; const fields = card.querySelector(".set-fields");
    [...fields.children].forEach(node => { if (!node.matches("input[type=hidden], input[type=checkbox]")) modalFields.append(node); });
    snapshot = [...modalFields.querySelectorAll("input,select")].map(field => field.value);
    modal.querySelector("#modal-title").textContent = card.querySelector(".set-number").textContent;
    modal.showModal();
  }
  list.addEventListener("click", event => {
    const card = event.target.closest("[data-set-form]"); if (!card) return;
    if (event.target.closest(".edit-set")) open(card);
    if (event.target.closest(".remove-set")) { if (visibleCards().length === 1) return; const deletion = card.querySelector("[name$='-DELETE']"); deletion.checked = true; card.classList.add("removed"); renumber(); }
  });
  document.querySelector("#add-set").addEventListener("click", () => {
    const index = Number(total.value); const html = document.querySelector("#empty-set-template").innerHTML.replaceAll("__prefix__", index); list.insertAdjacentHTML("beforeend", html); total.value = index + 1;
    const card = list.lastElementChild; const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16); card.querySelector("[name$='-performed_at']").value = now; card.querySelector("[name$='-rest_time_seconds']").value = 60; renumber(); open(card);
  });
  modal.querySelector(".modal-save").onclick = () => { if ([...modalFields.querySelectorAll("input,select")].every(field => field.reportValidity())) close(true); };
  modal.querySelector(".modal-cancel").onclick = () => close(false);
  modal.querySelector(".modal-close").onclick = () => close(false);
  modal.addEventListener("cancel", event => { event.preventDefault(); close(false); });
  visibleCards().forEach(summary); renumber();
})();
