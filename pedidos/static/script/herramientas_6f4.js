/* SterakFood 6F.5 — Configuración compacta: cinco destinos sin duplicados.
 * SOLO presentación del panel existente. No reconstruye formularios ni eventos;
 * reubica los nodos originales para conservar listeners, CSRF y endpoints.
 */
(function () {
  'use strict';
  function iniciar() {
    var tab = document.getElementById('tab-config');
    if (!tab || tab.dataset.sf65Montado === 'si') return;
    var central = document.getElementById('sm-herramientas-central');
    var grid = central && central.querySelector('.sm-herramientas-central__grid');
    var config = document.getElementById('sm-ajustes-sistema');
    var operaciones = tab.querySelector('.sm-herramientas-operaciones');
    var impresoras = document.getElementById('sm-impresoras-panel');
    var ayuda = config && config.querySelector('.config-ayuda-v2');
    var cabecera = central && central.querySelector('.sm-herramientas-central__titulo');
    if (!tab || !central || !grid || !config || !operaciones || !impresoras || !ayuda || !cabecera) {
      console.warn('SterakFood 6F5: estructura diferente. No se reorganizan controles.');
      return;
    }
    var acciones = Array.from(grid.children);
    var grupos = Array.from(config.children).filter(function (el) {
      return el.classList && el.classList.contains('config-grupo');
    });
    if (acciones.length !== 9 || grupos.length !== 5 ||
        !acciones[0].matches('[data-salon-tool-open="catalogo"]') ||
        !acciones[1].matches('[data-salon-tool-open="mozos"]') ||
        !acciones[2].matches('[data-salon-tool-open="importar"]')) {
      console.warn('SterakFood 6F5: acciones inesperadas; se conserva la pantalla anterior.');
      return;
    }

    var h2 = cabecera.querySelector('h2');
    var descripcion = cabecera.querySelector('p');
    var kicker = cabecera.querySelector('.categoria-kicker');
    if (h2) h2.textContent = 'Configuración';
    if (descripcion) descripcion.textContent = 'Elegí qué querés cambiar en tu restaurante.';
    if (kicker) kicker.textContent = 'STERAKFOOD';
    var headerSistema = config.querySelector('.config-sistema__header');
    if (headerSistema) headerSistema.hidden = true;
    var estadoGuardado = document.getElementById('config-estado-guardado');

    var selector = document.createElement('nav');
    selector.className = 'sf65-nav';
    selector.setAttribute('aria-label', 'Apartados de configuración');
    selector.setAttribute('role', 'tablist');
    var paneles = document.createElement('div');
    paneles.className = 'sf65-paneles';
    var separador = document.createElement('div');
    separador.className = 'sf65-estado';
    separador.setAttribute('aria-live', 'polite');
    if (estadoGuardado) separador.appendChild(estadoGuardado);
    config.insertBefore(selector, config.firstChild);
    selector.insertAdjacentElement('afterend', separador);
    separador.insertAdjacentElement('afterend', paneles);

    var secciones = [];
    function seccion(id, titulo, resumen) {
      var boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'sf65-nav-boton';
      boton.setAttribute('role', 'tab');
      boton.setAttribute('aria-controls', id);
      boton.id = id + '-tab';
      boton.textContent = titulo;
      selector.appendChild(boton);
      var panel = document.createElement('section');
      panel.className = 'sf65-panel';
      panel.id = id;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', boton.id);
      panel.setAttribute('tabindex', '0');
      panel.hidden = true;
      var heading = document.createElement('div');
      heading.className = 'sf65-panel-titulo';
      var tituloEl = document.createElement('h3');
      tituloEl.textContent = titulo;
      var p = document.createElement('p');
      p.textContent = resumen;
      heading.appendChild(tituloEl);
      heading.appendChild(p);
      panel.appendChild(heading);
      paneles.appendChild(panel);
      var obj = {id: id, boton: boton, panel: panel};
      secciones.push(obj);
      boton.addEventListener('click', function () { activar(obj); });
      return panel;
    }
    function activar(obj) {
      secciones.forEach(function (item) {
        var selected = item === obj;
        item.panel.hidden = !selected;
        item.boton.setAttribute('aria-selected', String(selected));
        item.boton.tabIndex = selected ? 0 : -1;
        item.boton.classList.toggle('is-active', selected);
      });
      // No se cambia el hash: el dashboard lo utiliza para sus pestañas globales.
    }
    selector.addEventListener('keydown', function (event) {
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
      var index = secciones.findIndex(function (item) { return item.boton === document.activeElement; });
      if (index === -1) return;
      event.preventDefault();
      var offset = event.key === 'ArrowRight' ? 1 : -1;
      var siguiente = secciones[(index + offset + secciones.length) % secciones.length];
      activar(siguiente);
      siguiente.boton.focus();
    });
    function añadirAccesos(destino, lista) {
      var fila = document.createElement('div');
      fila.className = 'sf65-accesos';
      lista.forEach(function (item) { fila.appendChild(item); });
      if (fila.children.length) destino.appendChild(fila);
    }
    function nota(destino, texto) {
      var p = document.createElement('p');
      p.className = 'sf65-nota';
      p.textContent = texto;
      destino.appendChild(p);
    }

    // Operación: precios y administración del salón. La gestión de mozos tiene
    // una sola entrada visible (Mesas y mozos), no dos atajos simultáneos.
    var diaria = seccion('sf65-diaria', 'Operación diaria', 'Pedidos, descuentos, productos del salón y personal.');
    añadirAccesos(diaria, [acciones[0], acciones[6]]);
    diaria.appendChild(grupos[0]); // Pedidos online / descuento
    diaria.appendChild(grupos[4]); // Módulo salón
    var detalles = document.createElement('details');
    detalles.className = 'sf65-aclaracion';
    var resumen = document.createElement('summary');
    resumen.textContent = 'Qué pasa si se corta Internet';
    detalles.appendChild(resumen);
    detalles.appendChild(grupos[1]); // Pedidos sin cierre automático
    detalles.appendChild(ayuda); // Ayudas existentes
    diaria.appendChild(detalles);

    // Un único destino de impresión: se conserva completo el panel 6F3.
    var impresion = seccion('sf65-impresion', 'Impresoras', 'Elegí caja, cocina y barra. Detectá USB, red o Wi-Fi desde Desktop.');
    impresion.appendChild(impresoras);

    // La identidad visual YA tiene su página con validaciones y formularios:
    // no se crea una segunda copia de los campos de nombre, logos y colores.
    var negocio = seccion('sf65-negocio', 'Mi negocio', 'Nombre, logos, colores y apariencia del restaurante.');
    añadirAccesos(negocio, [acciones[7]]);
    nota(negocio, 'Abrí Mi negocio para editar la identidad visual y guardar los cambios allí.');

    var menu = seccion('sf65-menu', 'Menú web', 'Menú QR, promociones, imágenes y comentarios.');
    añadirAccesos(menu, [acciones[4]]);
    menu.appendChild(grupos[2]); // Promociones / popup de bienvenida
    menu.appendChild(grupos[3]); // Comentarios / Google Reviews

    var avanzado = seccion('sf65-avanzado', 'Avanzado', 'Respaldo, importación, fiscal y diagnóstico.');
    nota(avanzado, 'Opciones administrativas. La caja se cierra desde Salón; no se duplica aquí.');
    añadirAccesos(avanzado, [acciones[2], acciones[5]]);
    var backup = operaciones.querySelector('a[href*="backup"]');
    if (backup) añadirAccesos(avanzado, [backup]);
    // En Desktop, 6E permanece desactivado por seguridad hasta configurar Render.
    if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {
      var linkSync = document.createElement('a');
      linkSync.href = '/desktop/sync-6e/';
      linkSync.className = 'sf65-link-extra';
      linkSync.textContent = 'Ver sincronización offline (6E)';
      avanzado.appendChild(linkSync);
    }

    // El formulario manual para pausar pedidos y el botón histórico de cierre
    // quedan en su DOM original, ocultos, sin borrar endpoints o listeners.
    // Las mismas acciones están en Operación diaria y en Salón respectivamente.
    grid.hidden = true;
    operaciones.hidden = true;
    if (headerSistema) headerSistema.hidden = true;
    tab.dataset.sf65Montado = 'si';
    tab.classList.add('sf64-herramientas', 'sf65-ajustes');

    // Destinos directos existentes (no rompe #tab-menu ni la navegación general).
    function seleccionPorHash() {
      var hash = window.location.hash;
      var objetivo = hash === '#sm-impresoras-panel' || hash === '#sf65-impresion' ? impresion :
        hash === '#sf65-negocio' ? negocio :
        hash === '#sf65-menu' ? menu :
        hash === '#sf65-avanzado' ? avanzado : diaria;
      var entry = secciones.find(function (item) { return item.panel === objetivo; });
      if (entry) activar(entry);
    }
    window.addEventListener('hashchange', seleccionPorHash);
    seleccionPorHash();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
}());
