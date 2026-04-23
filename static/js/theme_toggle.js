/* static/js/theme_toggle.js */
document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('theme-toggle');
  const themeToggleIcon = themeToggle ? themeToggle.querySelector('i') : null;
  const htmlElement = document.documentElement;

  // Check for saved theme preference or use system preference
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
    htmlElement.classList.add('dark-mode');
    updateIcon(true);
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const isDarkMode = htmlElement.classList.toggle('dark-mode');
      localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
      updateIcon(isDarkMode);
    });
  }

  function updateIcon(isDarkMode) {
    if (themeToggleIcon) {
      if (isDarkMode) {
        themeToggleIcon.classList.replace('fa-moon', 'fa-sun');
      } else {
        themeToggleIcon.classList.replace('fa-sun', 'fa-moon');
      }
    }
  }
});
