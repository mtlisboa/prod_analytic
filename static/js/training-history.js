(() => {
  const loader = document.querySelector("#training-history-loader");
  const rows = document.querySelector("#training-history-rows");
  if (!loader || !rows || !loader.dataset.nextPage) return;

  const button = loader.querySelector("button");
  const status = loader.querySelector("[role='status']");
  let loading = false;

  async function loadNextPage() {
    if (loading || !loader.dataset.nextPage) return;
    loading = true;
    button.disabled = true;
    status.textContent = "Carregando…";

    try {
      const url = new URL(loader.dataset.url, window.location.origin);
      url.searchParams.set("page", loader.dataset.nextPage);
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("history request failed");

      const data = await response.json();
      rows.insertAdjacentHTML("beforeend", data.html);
      loader.dataset.nextPage = data.next_page || "";
      loader.hidden = !data.has_next;
      status.textContent = data.has_next ? "" : "Todos os treinos foram carregados.";
    } catch (_) {
      status.textContent = "Não foi possível carregar mais treinos. Tente novamente.";
    } finally {
      loading = false;
      button.disabled = false;
    }
  }

  button.addEventListener("click", loadNextPage);

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) loadNextPage();
    }, { rootMargin: "300px 0px" });
    observer.observe(loader);
  }
})();
