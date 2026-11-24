/* SterakFood 5F: pestañas de Mi negocio sin alterar los campos o el POST. */
(() => {
  'use strict';
  const root = document.querySelector('.sf-brand--5f');
  if (!root) return;
  const form = root.querySelector('#sf-marca-form');
  const tabs = [...root.querySelectorAll('.sf-brand__5f-tab[role="tab"]')];
  const sections = [...root.querySelectorAll('.sf-brand__settings > .sf-brand__section[data-sf5f-section]')];
  const preview = root.querySelector('#sf5f-preview');
  const toggle = root.querySelector('.sf-brand__5f-preview-toggle');
  if (!form || tabs.length < 3 || tabs.length !== sections.length || !preview) return;

  function showTab(tab, focusTab = false) {
    const target = tab.dataset.sf5fTarget;
    if (!sections.some(section => section.dataset.sf5fSection === target)) return;
    tabs.forEach(button => {
      const active = button === tab;
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.tabIndex = active ? 0 : -1;
    });
    sections.forEach(section => {
      section.hidden = section.dataset.sf5fSection !== target;
    });
    if (focusTab) tab.focus();
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => showTab(tab));
    tab.addEventListener('keydown', event => {
      const key = event.key;
      let next = i;
      if (key === 'ArrowRight') next = (i + 1) % tabs.length;
      else if (key === 'ArrowLeft') next = (i + tabs.length - 1) % tabs.length;
      else if (key === 'Home') next = 0;
      else if (key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      showTab(tabs[next], true);
    });
  });

  // Si falla la validación nativa, hacer visible el campo requerido antes de que el navegador lo enfoque.
  form.addEventListener('invalid', event => {
    const section = event.target.closest('.sf-brand__section[data-sf5f-section]');
    if (!section) return;
    const match = tabs.find(tab => tab.dataset.sf5fTarget === section.dataset.sf5fSection);
    if (match) showTab(match);
  }, true);

  if (toggle) {
    toggle.addEventListener('click', () => {
      const opened = preview.classList.toggle('sf-brand__5f-preview-open');
      toggle.setAttribute('aria-expanded', String(opened));
    });
  }
  root.classList.add('sf-brand--5f-ready');
  showTab(tabs[0]);
})();
