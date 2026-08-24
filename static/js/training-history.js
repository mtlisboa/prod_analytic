(() => {
  const loader = document.querySelector("#training-history-loader");
  const rows = document.querySelector("#training-history-rows");
  const search = document.querySelector("#training-history-search");
  if (!loader || !rows || !search) return;

  const button = loader.querySelector("button");
  const status = loader.querySelector("[role='status']");
  let loading = false;
  let searchTimer = null;
  let request = null;

  async function loadPage(page, append) {
    if (!page || (loading && append)) return;
    request?.abort();
    const currentRequest = new AbortController();
    request = currentRequest;
    loading = true;
    button.disabled = true;
    status.textContent = "Carregando…";

    try {
      const url = new URL(loader.dataset.url, window.location.origin);
      url.searchParams.set("page", page);
      if (search.value.trim()) url.searchParams.set("q", search.value.trim());
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: currentRequest.signal,
      });
      if (!response.ok) throw new Error("history request failed");

      const data = await response.json();
      if (append) rows.insertAdjacentHTML("beforeend", data.html);
      else rows.innerHTML = data.html;
      loader.dataset.nextPage = data.next_page || "";
      loader.hidden = !data.has_next;
      status.textContent = data.has_next ? "" : "Todos os treinos foram carregados.";
    } catch (error) {
      if (error.name !== "AbortError") status.textContent = "Não foi possível carregar os treinos. Tente novamente.";
    } finally {
      if (request === currentRequest) {
        loading = false;
        button.disabled = false;
      }
    }
  }

  function loadNextPage() {
    return loadPage(loader.dataset.nextPage, true);
  }

  function reloadHistory() {
    return loadPage(1, false);
  }

  button.addEventListener("click", loadNextPage);
  search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(reloadHistory, 300);
  });

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) loadNextPage();
    }, { rootMargin: "300px 0px" });
    observer.observe(loader);
  }
})();
