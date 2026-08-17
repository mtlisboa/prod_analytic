(function () {
  const root = document.documentElement;
  const button = document.querySelector('.theme-toggle');
  const label = button.querySelector('.theme-toggle-label');
  const themeColor = document.querySelector('meta[name="theme-color"]');

  function update(theme) {
    const isDark = theme === 'dark';
    root.dataset.theme = theme;
    button.setAttribute('aria-pressed', String(isDark));
    button.setAttribute('aria-label', isDark ? 'Ativar tema claro' : 'Ativar tema escuro');
    label.textContent = isDark ? 'Tema claro' : 'Tema escuro';
    themeColor.setAttribute('content', isDark ? '#11140f' : '#f4f2eb');
  }

  update(root.dataset.theme || 'light');
  button.addEventListener('click', function () {
    const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('forge-theme', nextTheme);
    update(nextTheme);
  });
}());
