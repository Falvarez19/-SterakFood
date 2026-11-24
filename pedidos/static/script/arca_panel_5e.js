/* SterakFood 5E - Presentacion compacta del panel ARCA.
 * Mejora progresiva sin modificar los formularios, sus destinos o permisos.
 * Sin AJAX fiscal: el backend sigue siendo la unica fuente de verdad.
 */
(function () {
  'use strict';
  function start() {
    var root = document.querySelector('main.sf-arca--5e');
    if (!root || root.dataset.panel5eInicializado === '1') return;
    var layout = root.querySelector('.sf-arca__layout');
    var datos = layout && layout.querySelector(':scope > section.sf-arca__section');
    var estado = layout && layout.querySelector(':scope > aside.sf-arca__section');
    var compat = root.querySelector('.sf-arca__section[aria-labelledby="sf-arca-5c-titulo"]');
    var pruebas = root.querySelector('.sf-arca__section[aria-labelledby="sf-arca-5d-titulo"]');
    var certificados = root.querySelector('.sf-arca__selfservice');
    var diagnostico = estado && estado.querySelector('.sf-arca__diag');
    if (!layout || !datos || !estado || !compat || !pruebas || !certificados || !diagnostico) return;

    var tabs = [
      { id: 'resumen', label: 'Resumen' },
      { id: 'datos', label: 'Datos fiscales' },
      { id: 'certificados', label: 'Certificados' },
      { id: 'diagnostico', label: 'Diagnóstico' },
      { id: 'pruebas', label: 'Pruebas' }
    ];
    var tabBar = document.createElement('nav');
    tabBar.className = 'sf-arca5e__tabs';
    tabBar.setAttribute('role', 'tablist');
    tabBar.setAttribute('aria-label', 'Secciones de configuración fiscal');
    var container = document.createElement('div');
    container.className = 'sf-arca5e__contenedor';
    var panels = {};
    var buttons = {};
    var storeKey = 'sterak-arca-5e-tab';

    tabs.forEach(function (tab) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'sf-arca5e__tab';
      btn.textContent = tab.label;
      btn.setAttribute('role', 'tab');
      btn.setAttribute('id', 'sf-arca5e-tab-' + tab.id);
      btn.setAttribute('aria-controls', 'sf-arca5e-panel-' + tab.id);
      btn.setAttribute('aria-selected', 'false');
      btn.tabIndex = -1;
      tabBar.appendChild(btn);
      buttons[tab.id] = btn;
      var panel = document.createElement('div');
      panel.className = 'sf-arca5e__panel';
      panel.id = 'sf-arca5e-panel-' + tab.id;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', btn.id);
      panel.hidden = true;
      container.appendChild(panel);
      panels[tab.id] = panel;
      btn.addEventListener('click', function () { activate(tab.id, true); });
      btn.addEventListener('keydown', function (ev) {
        var current = tabs.findIndex(function (x) { return x.id === tab.id; });
        var next = current;
        if (ev.key === 'ArrowRight') next = (current + 1) % tabs.length;
        else if (ev.key === 'ArrowLeft') next = (current + tabs.length - 1) % tabs.length;
        else if (ev.key === 'Home') next = 0;
        else if (ev.key === 'End') next = tabs.length - 1;
        else return;
        ev.preventDefault();
        activate(tabs[next].id, true);
        buttons[tabs[next].id].focus();
      });
    });

    // Mover nodos originales preserva los valores de formularios, CSRF y enlaces.
    estado.querySelector('.sf-arca__diag').remove();
    panels.resumen.appendChild(estado);
    panels.resumen.appendChild(compat);
    panels.datos.appendChild(datos);
    panels.certificados.appendChild(certificados);
    var diagnosticoTarjeta = document.createElement('section');
    diagnosticoTarjeta.className = 'sf-arca__section sf-arca5e__diag-card';
    diagnosticoTarjeta.appendChild(diagnostico);
    panels.diagnostico.appendChild(diagnosticoTarjeta);
    panels.pruebas.appendChild(pruebas);

    // Avisar que la simulacion es independiente de la condicion fiscal del emisor.
    if (root.dataset.condicionIva !== 'monotributo') {
      var aviso = document.createElement('p');
      aviso.className = 'sf-arca5e__aviso-pruebas';
      aviso.textContent = 'La simulación de Factura C es una herramienta de prueba. No corresponde al régimen fiscal actualmente seleccionado y nunca habilita emitir.';
      panels.pruebas.insertBefore(aviso, pruebas);
    }
    // En el resumen, atajos verdaderos a las otras secciones.
    var shortcut = document.createElement('div');
    shortcut.className = 'sf-arca5e__atajos';
    [
      ['datos', 'Editar datos fiscales'],
      ['certificados', 'Cargar certificado'],
      ['diagnostico', 'Comprobar ARCA']
    ].forEach(function (item) {
      var a = document.createElement('button');
      a.type = 'button';
      a.textContent = item[1];
      a.addEventListener('click', function () { activate(item[0], true); buttons[item[0]].focus(); });
      shortcut.appendChild(a);
    });
    panels.resumen.insertBefore(shortcut, estado);

    // Restaurar la misma pestana tras los POST tradicionales de Django.
    tabs.forEach(function (tab) {
      panels[tab.id].querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
          try { window.sessionStorage.setItem(storeKey, tab.id); } catch (_ignored) {}
        });
      });
    });

    function activate(id, save) {
      if (!panels[id]) id = 'resumen';
      tabs.forEach(function (tab) {
        var selected = tab.id === id;
        panels[tab.id].hidden = !selected;
        buttons[tab.id].setAttribute('aria-selected', String(selected));
        buttons[tab.id].tabIndex = selected ? 0 : -1;
      });
      if (save) {
        try { window.sessionStorage.setItem(storeKey, id); } catch (_ignored) {}
      }
    }
    layout.replaceWith(tabBar, container);
    root.dataset.panel5eInicializado = '1';
    var last = 'resumen';
    try { last = window.sessionStorage.getItem(storeKey) || last; } catch (_ignored) {}
    activate(last, false);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
