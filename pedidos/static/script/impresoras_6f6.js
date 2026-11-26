/* SterakFood 6F.6 — Vista de impresión compacta, sin alterar el guardado ni la API.
 * Conserva los elementos con name y data-sf6f3-* para compatibilidad 6F.3.
 */
(function () {
  'use strict';
  const SECTORES = [
    ['caja', 'Caja', 'Ticket para el cliente'],
    ['cocina', 'Cocina', 'Comanda sin precios'],
    ['barra', 'Barra', 'Opcional'],
  ];
  function element(tag, cls, contenido) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (contenido) node.textContent = contenido;
    return node;
  }
  function cambiarEtiqueta(label, text) {
    if (!label) return;
    for (const node of label.childNodes) {
      if (node.nodeType === 3 && node.textContent.trim()) {
        node.textContent = text;
        return;
      }
    }
  }
  function preparar(form) {
    if (!form || form.dataset.sf66Ready === '1') return;
    // No crear un formulario nuevo: reubicamos los controles que ya guarda Django.
    if (!SECTORES.every(([sector]) => form.elements[sector + '_modo'])) return;
    form.dataset.sf66Ready = '1';
    form.classList.add('sf66-ready');
    const tools = form.querySelector('.sf6f3-tools');
    if (tools) {
      tools.classList.add('sf66-tools');
      const button = tools.querySelector('[data-sf6f3-buscar]');
      if (button) button.textContent = 'Detectar impresoras de Windows';
      const output = tools.querySelector('[data-sf6f3-estado]');
      if (output) output.textContent = 'USB, red o Wi-Fi instaladas en esta computadora';
    }
    const general = form.elements.ancho_ticket?.closest('label');
    let ultimaTarjeta = null;
    SECTORES.forEach(([sector, nombre, descripcion]) => {
      const modo = form.elements[sector + '_modo'];
      const modoLabel = modo?.closest('label');
      if (!modoLabel) return;
      const labels = Array.from(form.querySelectorAll('[data-sf6f3-sector="' + sector + '"]'));
      const card = element('section', 'sf66-card');
      card.dataset.sf66Sector = sector;
      const titulo = element('div', 'sf66-card-title');
      titulo.append(element('strong', '', nombre), element('small', '', descripcion));
      const body = element('div', 'sf66-card-body');
      const target = element('div', 'sf66-card-target');
      cambiarEtiqueta(modoLabel, 'Conexión');
      modo.querySelectorAll('option').forEach((opt) => {
        if (opt.value === 'windows') opt.textContent = 'Impresora de Windows';
        if (opt.value === 'tcp') opt.textContent = 'Conectar por IP';
        if (opt.value === 'off') opt.textContent = 'Sin impresora';
      });
      body.append(modoLabel, target);
      labels.forEach((label) => {
        if (label.dataset.sf6f3Mostrar === 'tcp') cambiarEtiqueta(label, 'Dirección IP · puerto 9100');
        else if (label.querySelector('select')) cambiarEtiqueta(label, 'Elegí la impresora');
        else cambiarEtiqueta(label, 'Nombre exacto de Windows');
        target.append(label);
      });
      const manual = labels.find((el) => Boolean(el.querySelector('input[name="' + sector + '_windows"]')));
      if (manual) {
        manual.classList.add('sf66-manual');
        const toggle = element('button', 'sf66-manual-toggle', '¿No aparece? Escribir nombre');
        toggle.type = 'button';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.addEventListener('click', () => {
          const expanded = toggle.getAttribute('aria-expanded') !== 'true';
          toggle.setAttribute('aria-expanded', String(expanded));
          toggle.textContent = expanded ? 'Ocultar nombre manual' : '¿No aparece? Escribir nombre';
          refrescar(form);
          if (expanded) manual.querySelector('input')?.focus();
        });
        target.append(toggle);
      }
      const hint = element('p', 'sf66-off-hint', 'No se enviarán trabajos a este destino.');
      target.append(hint);
      card.append(titulo, body);
      if (ultimaTarjeta) ultimaTarjeta.after(card);
      else if (tools) tools.after(card);
      else form.prepend(card);
      ultimaTarjeta = card;
      modo.addEventListener('change', () => refrescar(form));
    });
    if (general) {
      general.classList.add('sf66-general');
      cambiarEtiqueta(general, 'Ancho del ticket');
    }
    // Formulario web: el agente SM antiguo queda invisible, pero su elemento
    // permanece en DOM porque el JS heredado sigue registrando su listener.
    const modal = form.closest('#sm-impresoras-dialogo');
    if (modal) {
      const subtitle = modal.querySelector('.sm-impresoras__cabecera p');
      if (subtitle) subtitle.textContent = 'Caja, cocina y barra. Elegí cómo se conecta cada impresora.';
    }
    refrescar(form);
  }
  function refrescar(form) {
    if (!form || form.dataset.sf66Ready !== '1') return;
    SECTORES.forEach(([sector]) => {
      const modo = form.elements[sector + '_modo'];
      const card = form.querySelector('[data-sf66-sector="' + sector + '"]');
      if (!modo || !card) return;
      card.dataset.sf66Mode = modo.value;
      const manual = card.querySelector('.sf66-manual');
      const btn = card.querySelector('.sf66-manual-toggle');
      card.querySelectorAll('[data-sf6f3-sector]').forEach((label) => {
        let visible = label.dataset.sf6f3Mostrar === modo.value;
        if (label === manual) visible = visible && btn?.getAttribute('aria-expanded') === 'true';
        label.hidden = !visible;
        label.style.display = visible ? '' : 'none';
        label.querySelectorAll('input,select').forEach((input) => {
          // Solo afecta a los campos visuales. No deshabilitamos inputs,
          // para conservar sus valores al cambiar de método de conexión.
          input.setAttribute('aria-hidden', visible ? 'false' : 'true');
          input.tabIndex = visible ? 0 : -1;
        });
      });
      if (btn) btn.hidden = modo.value !== 'windows';
      const hint = card.querySelector('.sf66-off-hint');
      if (hint) hint.hidden = modo.value !== 'off';
    });
    // El detector de Windows no aporta nada si todos usan IP o están apagados.
    const tools = form.querySelector('.sf66-tools');
    if (tools) tools.hidden = !SECTORES.some(([sector]) => form.elements[sector + '_modo']?.value === 'windows');
  }
  function init() {
    ['sm-impresoras-form', 'sf6f3-desktop-form'].forEach((id) => preparar(document.getElementById(id)));
    // 6F.3 llama refresh() después de cargar valores desde la API web.
    if (window.SterakPrinter6F3 && !window.SterakPrinter6F3.sf66Wrapped) {
      const anterior = window.SterakPrinter6F3.refresh;
      window.SterakPrinter6F3.refresh = function(form) {
        if (typeof anterior === 'function') anterior(form);
        refrescar(form);
      };
      window.SterakPrinter6F3.sf66Wrapped = true;
    }
  }
  window.SterakPrinter6F6 = {refresh:refrescar};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
