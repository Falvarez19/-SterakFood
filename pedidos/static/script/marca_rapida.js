(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const name = get('sf-nombre');
  const primary = get('sf-principal');
  const secondary = get('sf-secundario');
  const accent = get('sf-acento');
  const preview = get('sf-preview');
  const title = get('sf-preview-nombre');
  if (!name || !primary || !secondary || !accent || !preview || !title) return;

  function refresh() {
    preview.style.setProperty('--sf-principal', primary.value);
    preview.style.setProperty('--sf-secundario', secondary.value);
    preview.style.setProperty('--sf-acento', accent.value);
    title.textContent = name.value.trim() || 'Mi restaurante';
  }
  [name, primary, secondary, accent].forEach(input => input.addEventListener('input', refresh));
  document.querySelectorAll('[data-sf-palette]').forEach(button => {
    button.addEventListener('click', () => {
      const values = (button.getAttribute('data-sf-palette') || '').split(',');
      if (values.length !== 3) return;
      [primary.value, secondary.value, accent.value] = values;
      refresh();
    });
  });
  const fileInput = get('sf-logo-archivo');
  const image = get('sf-preview-logo');
  let temporaryUrl;
  fileInput?.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (!file || !image) return;
    if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
    temporaryUrl = URL.createObjectURL(file);
    image.src = temporaryUrl;
  });
  window.addEventListener('beforeunload', () => {
    if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
  });
  refresh();
})();
