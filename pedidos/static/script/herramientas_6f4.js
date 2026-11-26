/* SterakFood 6F.4 — organiza Herramientas sin reemplazar forms, IDs ni eventos.
 * Deliberadamente mueve los nodos existentes (appendChild) en vez de clonar
 * HTML: conserva valores, event listeners, CSRF y las integraciones 6F3.
 */
(function () {
  'use strict';

  function montarHerramientas() {
    var tab = document.getElementById('tab-config');
    if (!tab || tab.dataset.sf64Montado === 'si') return;

    var central = document.getElementById('sm-herramientas-central');
    var grid = central && central.querySelector('.sm-herramientas-central__grid');
    var config = document.getElementById('sm-ajustes-sistema');
    var operaciones = tab.querySelector('.sm-herramientas-operaciones');
    var impresoras = document.getElementById('sm-impresoras-panel');
    var ayuda = config && config.querySelector('.config-ayuda-v2');
    if (!central || !grid || !config || !operaciones || !impresoras || !ayuda) {
      console.warn('SterakFood 6F4: Herramientas no tiene la estructura esperada; no se cambia la pantalla.');
      return;
    }

    var grupos = Array.from(config.children).filter(function (el) {
      return el.classList && el.classList.contains('config-grupo');
    });
    var acciones = Array.from(grid.children);
    // Mapeo de la plantilla que ya existe. No elimina ni inventa operaciones.
    if (grupos.length !== 5 || acciones.length < 9 ||
        !acciones[0].hasAttribute('data-salon-tool-open') ||
        !acciones[1].hasAttribute('data-salon-tool-open') ||
        !acciones[2].hasAttribute('data-salon-tool-open') ||
        !acciones[3].getAttribute('href') ||
        !acciones[4].getAttribute('href')) {
      console.warn('SterakFood 6F4: Se encontró otra versión de Herramientas; se conserva la anterior.');
      return;
    }

    var quick = [acciones[3], acciones[7], acciones[0], acciones[4]];
    var toolMozos = acciones[1];
    var toolImportar = acciones[2];
    var toolFiscal = acciones[5];
    var toolOperacion = acciones[6];
    var toolAjustes = acciones[8];
    var header = central.querySelector('.sm-herramientas-central__titulo');
    var titulo = header && header.querySelector('h2');
    var leyenda = header && header.querySelector('p');
    if (titulo) titulo.textContent = 'Herramientas';
    if (leyenda) leyenda.textContent = 'Elegí qué querés configurar. Todo lo demás queda a un clic.';

    var subtitulo = document.createElement('div');
    subtitulo.className = 'sf64-quick-title';
    subtitulo.textContent = 'Accesos rápidos';
    grid.parentNode.insertBefore(subtitulo, grid);
    grid.classList.add('sf64-quick-grid');
    quick.forEach(function (n) { grid.appendChild(n); });

    var encabezado = config.querySelector('.config-sistema__header');
    if (encabezado) {
      var h = encabezado.querySelector('h2');
      var p = encabezado.querySelector('p');
      if (h) h.textContent = 'Configuración';
      if (p) p.textContent = 'Los cambios de esta pantalla se guardan igual que antes.';
    }

    var stack = document.createElement('div');
    stack.className = 'sf64-secciones';
    stack.setAttribute('aria-label', 'Áreas de configuración');
    if (encabezado && encabezado.nextSibling) {
      config.insertBefore(stack, encabezado.nextSibling);
    } else {
      config.appendChild(stack);
    }

    function seccion(id, titulo, descripcion, abierta) {
      var details = document.createElement('details');
      details.className = 'sf64-seccion';
      details.id = id;
      details.open = Boolean(abierta);
      var summary = document.createElement('summary');
      summary.className = 'sf64-seccion-cabecera';
      var txt = document.createElement('span');
      txt.className = 'sf64-seccion-texto';
      var h = document.createElement('strong');
      h.textContent = titulo;
      var desc = document.createElement('small');
      desc.textContent = descripcion;
      txt.appendChild(h);
      txt.appendChild(desc);
      var flecha = document.createElement('span');
      flecha.className = 'sf64-chevron';
      flecha.setAttribute('aria-hidden', 'true');
      flecha.textContent = '⌄';
      summary.appendChild(txt);
      summary.appendChild(flecha);
      var contenido = document.createElement('div');
      contenido.className = 'sf64-seccion-contenido';
      details.appendChild(summary);
      details.appendChild(contenido);
      stack.appendChild(details);
      return { details: details, contenido: contenido };
    }

    function filaAcciones() {
      var nav = document.createElement('div');
      nav.className = 'sf64-enlaces-secundarios';
      return nav;
    }

    var diaria = seccion('sf64-operacion', 'Operación diaria', 'Pedidos, descuento, salón y personal', true);
    var diarioLinks = filaAcciones();
    diarioLinks.appendChild(toolMozos);
    diarioLinks.appendChild(toolOperacion);
    diaria.contenido.appendChild(diarioLinks);
    diaria.contenido.appendChild(grupos[0]); // Ventas: pedidos online + descuento
    diaria.contenido.appendChild(grupos[4]); // Salón

    var menu = seccion('sf64-menu', 'Menú público y clientes', 'Promociones, bienvenida y opiniones', false);
    menu.contenido.appendChild(grupos[2]); // Menú público
    menu.contenido.appendChild(grupos[3]); // Clientes

    var impresion = seccion('sf64-impresion', 'Impresoras', 'Caja, cocina y barra · USB, red o Wi-Fi', false);
    impresion.contenido.appendChild(impresoras); // incluye modal y eventos 6F3

    var avanzado = seccion('sf64-avanzado', 'Administración avanzada', 'Respaldo, cierre de caja, importación y fiscal', false);
    var avanzadoLinks = filaAcciones();
    avanzadoLinks.appendChild(toolImportar);
    avanzadoLinks.appendChild(toolFiscal);
    avanzadoLinks.appendChild(toolAjustes);
    // Si una versión futura suma accesos, se conservan; nunca se descartan.
    Array.from(grid.children).forEach(function (n) {
      if (quick.indexOf(n) === -1) avanzadoLinks.appendChild(n);
    });
    avanzado.contenido.appendChild(avanzadoLinks);
    avanzado.contenido.appendChild(operaciones); // incluye acciones con confirmación

    var notaPedidos = document.createElement('details');
    notaPedidos.className = 'sf64-info';
    var resumenPedidos = document.createElement('summary');
    resumenPedidos.textContent = 'Información sobre los pedidos online';
    notaPedidos.appendChild(resumenPedidos);
    notaPedidos.appendChild(grupos[1]);
    notaPedidos.appendChild(ayuda);
    avanzado.contenido.appendChild(notaPedidos);

    // Los accesos de arriba abren el bloque correcto, sin dejar secciones enormes.
    var accesoImpresoras = quick[0];
    accesoImpresoras.addEventListener('click', function (ev) {
      ev.preventDefault();
      impresion.details.open = true;
      impresion.details.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    toolAjustes.addEventListener('click', function (ev) {
      ev.preventDefault();
      diaria.details.open = true;
      diaria.details.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    var bloques = [diaria.details, menu.details, impresion.details, avanzado.details];
    bloques.forEach(function (bloque) {
      bloque.addEventListener('toggle', function () {
        if (!bloque.open) return;
        bloques.forEach(function (otro) { if (otro !== bloque) otro.open = false; });
      });
    });
    // Por si el usuario llega con #sm-impresoras-panel o #sm-ajustes-sistema.
    if (window.location.hash === '#sm-impresoras-panel') impresion.details.open = true;
    if (window.location.hash === '#sm-ajustes-sistema') diaria.details.open = true;

    tab.dataset.sf64Montado = 'si';
    tab.classList.add('sf64-herramientas');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', montarHerramientas);
  } else {
    montarHerramientas();
  }
}());
