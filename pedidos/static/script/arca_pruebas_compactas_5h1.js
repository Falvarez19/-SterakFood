/* SterakFood 5H.1: solo presentacion. No cambia action, method, tokens CSRF ni comportamiento fiscal. */
(function () {
  'use strict';
  function start() {
    var root = document.querySelector('main.sf-arca--5e');
    if (!root || root.dataset.pruebas5h1 === '1') return;
    var section = root.querySelector('.sf-arca__section[aria-labelledby="sf-arca-5d-titulo"]');
    if (!section) return;
    var simTitle = section.querySelector(':scope > #sf-arca-5d-titulo');
    var intro = section.querySelector(':scope > p.sf-arca__hint');
    var simForm = section.querySelector(':scope > form');
    var simHelp = section.querySelector(':scope > #sf-arca-5d-ayuda');
    var simWarn = section.querySelector(':scope > p.sf-arca__warning');
    var preflight = section.querySelector(':scope > .sf-arca__entorno:not(.sf5h-box)');
    var cae = section.querySelector(':scope > .sf5h-box');
    if (!simTitle || !intro || !simForm || !simHelp || !simWarn || !preflight || !cae) return;
    if (!preflight.querySelector('form') || !cae.querySelector('a[href]')) return;

    function el(tag, className, text) {
      var node = document.createElement(tag);
      if (className) node.className = className;
      if (text) node.textContent = text;
      return node;
    }
    function details(card, nodes, title) {
      var disclosure = el('details', 'sf5h1-disclosure');
      var summary = el('summary', '', title || 'Ver detalles');
      disclosure.appendChild(summary);
      var content = el('div', 'sf5h1-disclosure__body');
      nodes.forEach(function (node) { if (node) content.appendChild(node); });
      disclosure.appendChild(content);
      card.appendChild(disclosure);
    }
    function status(card, text) {
      card.insertBefore(el('p', 'sf5h1-status', text), card.firstChild.nextSibling);
    }

    var heading = el('div', 'sf5h1-heading');
    heading.appendChild(simTitle);
    simTitle.textContent = 'Pruebas de Factura C';
    heading.appendChild(el('span', 'sf5h1-heading__badge', 'Sin emisión comercial'));

    var grid = el('div', 'sf5h1-grid');
    var sim = el('section', 'sf5h1-card sf5h1-card--sim');
    sim.setAttribute('aria-label', 'Simulación sin emitir');
    sim.appendChild(el('h3', '', 'Simulación de importes'));
    sim.appendChild(el('p', 'sf5h1-status', 'Ficticia · no solicita CAE'));
    simForm.classList.add('sf5h1-simular-form');
    sim.appendChild(simForm);
    details(sim, [intro, simHelp, simWarn], 'Ver límites de la simulación');

    preflight.classList.add('sf5h1-card', 'sf5h1-card--consulta');
    var preIntro = preflight.querySelector(':scope > p.sf-arca__hint');
    var preExtra = preflight.querySelectorAll(':scope > p.sf-arca__hint');
    var preTitle = preflight.querySelector(':scope > h3');
    if (preTitle) preTitle.textContent = 'Consultar autorización';
    if (preIntro) {
      preIntro.insertAdjacentElement('afterend', el('p', 'sf5h1-status', 'Solo lectura · sin CAE'));
    }
    details(preflight, Array.prototype.slice.call(preExtra), 'Requisitos para consultar');

    cae.classList.add('sf5h1-card', 'sf5h1-card--cae');
    var caeTitle = cae.querySelector(':scope > h3');
    if (caeTitle) caeTitle.textContent = 'CAE de homologación';
    var caeHint = cae.querySelector(':scope > p.sf-arca__hint');
    var caeForm = cae.querySelector(':scope > form');
    var caeMsg = cae.querySelector(':scope > p.sf5h-hint');
    if (caeTitle) caeTitle.insertAdjacentElement('afterend', el('p', 'sf5h1-status sf5h1-status--cuidado', 'Prueba con CAE · consume numeración de homologación'));
    if (caeForm) caeForm.classList.add('sf5h1-cae-form');
    // Nunca ocultar los consentimientos explícitos ni la advertencia de reenvío ante incertidumbre.
    if (caeHint) details(cae, [caeHint], 'Condiciones del CAE de prueba');
    if (caeMsg) caeMsg.classList.add('sf5h1-incierto');

    grid.appendChild(sim);
    grid.appendChild(preflight);
    grid.appendChild(cae);
    section.appendChild(heading);
    section.appendChild(grid);
    section.classList.add('sf5h1-pruebas');
    root.dataset.pruebas5h1 = '1';
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
