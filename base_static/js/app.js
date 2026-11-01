(function () {
  function renderIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }
  window.renderIcons = renderIcons;

  function isTyping(target) {
    if (!target) return false;
    var tag = target.tagName;
    return (
      tag === 'INPUT' ||
      tag === 'TEXTAREA' ||
      tag === 'SELECT' ||
      target.isContentEditable
    );
  }

  function initTheme() {
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var isDark = document.documentElement.classList.toggle('dark');
        try {
          localStorage.setItem('theme', isDark ? 'dark' : 'light');
        } catch (e) {}
      });
    });
  }

  function initAccountMenu() {
    var btn = document.getElementById('profileDropdownBtn');
    var menu = document.getElementById('profileDropdown');
    if (!btn || !menu) return;

    function close() {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
    }

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var willOpen = menu.classList.contains('hidden');
      menu.classList.toggle('hidden', !willOpen);
      btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });

    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !menu.contains(e.target)) close();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !menu.classList.contains('hidden')) {
        close();
        btn.focus();
      }
    });
  }

  function initSearch() {
    var inputs = document.querySelectorAll('[data-search]');
    if (!inputs.length) return;

    var STORAGE_KEY = 'al-search-focus';
    var timer = null;

    inputs.forEach(function (input) {
      var form = input.closest('form');
      if (!form) return;

      try {
        if (sessionStorage.getItem(STORAGE_KEY) === '1' && input.value) {
          input.focus();
          input.setSelectionRange(input.value.length, input.value.length);
        }
        sessionStorage.removeItem(STORAGE_KEY);
      } catch (e) {}

      input.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          document.querySelectorAll('[data-list]').forEach(function (el) {
            el.classList.add('al-skeleton');
          });
          try {
            sessionStorage.setItem(STORAGE_KEY, '1');
          } catch (e) {}
          form.requestSubmit();
        }, 250);
      });
    });
  }

  function initShortcuts() {
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        var search = document.querySelector('[data-search]');
        if (search) {
          e.preventDefault();
          search.focus();
          search.select();
        }
        return;
      }

      if (
        e.key.toLowerCase() === 'n' &&
        !e.metaKey &&
        !e.ctrlKey &&
        !e.altKey
      ) {
        if (isTyping(e.target)) return;
        if (document.querySelector('dialog[open]')) return;
        var open = document.getElementById('openCreateDialog');
        if (open) {
          e.preventDefault();
          open.click();
        }
      }
    });
  }

  function init() {
    renderIcons();
    initTheme();
    initAccountMenu();
    initSearch();
    initShortcuts();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
