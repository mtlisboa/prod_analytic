(() => {
  const modal = document.querySelector("#training-create-modal");
  if (!modal) return;

  const body = modal.querySelector(".training-create-modal-body");

  function openModal(event) {
    event?.preventDefault();
    modal.hidden = false;
    document.body.classList.add("modal-open");
    modal.querySelector("#exercise-search")?.focus();
  }

  function closeModal() {
    const setModal = modal.querySelector("#set-modal");
    if (setModal?.open) setModal.close();
    modal.hidden = true;
    document.body.classList.remove("modal-open");
  }

  function initializeModalContent() {
    window.FORGE_INIT_EXERCISE_SEARCH?.(body);
    window.FORGE_INIT_TRAINING_CONTROLS?.(body);
    const form = body.querySelector("[data-training-modal-form]");
    if (!form) return;
    form.addEventListener("submit", submitTraining);
    body.querySelectorAll("[data-training-modal-close]").forEach(button => button.addEventListener("click", closeModal));
  }

  async function submitTraining(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type='submit']");
    submit.disabled = true;
    submit.textContent = "Salvando…";

    try {
      const response = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success) window.location.reload();
        return;
      }
      if (response.status === 422) {
        body.innerHTML = await response.text();
        initializeModalContent();
        return;
      }
      throw new Error("training request failed");
    } catch (_) {
      submit.disabled = false;
      submit.textContent = "Registrar treino";
      window.alert("Não foi possível registrar o treino. Tente novamente.");
    }
  }

  document.querySelectorAll("[data-training-modal-open]").forEach(link => link.addEventListener("click", openModal));
  modal.addEventListener("click", event => { if (event.target === modal) closeModal(); });
  document.addEventListener("keydown", event => { if (event.key === "Escape" && !modal.hidden && !modal.querySelector("#set-modal")?.open) closeModal(); });
  initializeModalContent();
})();
