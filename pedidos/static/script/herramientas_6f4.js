/* SterakFood 6F.8 — Configuración directa, sin pestañas ni botones repetidos.
 * Reubica los nodos EXISTENTES: sus eventos, datos, CSRF y guardado se conservan.
 * No crea formularios alternativos ni cambia endpoints.
 */
(function () {
  'use strict';
  function iniciar() {
    const tab = document.getElementById('tab-config');
    if (!tab || tab.dataset.sf68Listo === '1') return;
    const central = document.getElementById('sm-herramientas-central');
    const grid = central && central.querySelector('.sm-herramientas-central__grid');
    const config = document.getElementById('sm-ajustes-sistema');
    const operaciones = tab.querySelector('.sm-herramientas-operaciones');
    const impresoras = document.getElementById('sm-impresoras-panel');
    const ayuda = config && config.querySelector('.config-ayuda-v2');
    const cabecera = central && central.querySelector('.sm-herramientas-central__titulo');
    if (!central || !grid || !config || !operaciones || !impresoras || !ayuda || !cabecera) return;
    const acciones = Array.from(grid.children);
    const grupos = Array.from(config.children).filter(el => el.classList.contains('config-grupo'));
    if (acciones.length !== 9 || grupos.length !== 5 ||
        !acciones[0].matches('[data-salon-tool-open="catalogo"]') ||
        !acciones[1].matches('[data-salon-tool-open="mozos"]') ||
        !acciones[2].matches('[data-salon-tool-open="importar"]')) {
      console.warn('SterakFood 6F8: estructura desconocida. No se altera Configuración.');
      return;
    }
    const titulo = cabecera.querySelector('h2');
    if (titulo) titulo.textContent = 'Configuración';
    const descripcion = cabecera.querySelector('p');
    if (descripcion) descripcion.textContent = 'Los ajustes de tu restaurante, sin pasos de más.';
    const kicker = cabecera.querySelector('.categoria-kicker');
    if (kicker) kicker.textContent = 'STERAKFOOD';

    // Un solo recorrido de lectura. No hay una barra con cinco pestañas que
    // luego obligue a presionar otros botones para acceder a las funciones.
    let contenedor = config.querySelector('.sf65-paneles');
    const navAnterior = config.querySelector('.sf65-nav');
    if (navAnterior) navAnterior.remove();
    if (!contenedor) {
      contenedor = document.createElement('div');
      config.prepend(contenedor);
    }
    contenedor.className = 'sf68-grupos';
    contenedor.replaceChildren();
    const headerSistema = config.querySelector('.config-sistema__header');
    if (headerSistema) headerSistema.hidden = true;
    const estadoGuardado = document.getElementById('config-estado-guardado');
    if (estadoGuardado) {
      let estado = config.querySelector('.sf65-estado');
      if (!estado) { estado = document.createElement('div'); estado.className = 'sf65-estado'; }
      estado.appendChild(estadoGuardado);
      contenedor.before(estado);
    }
    function grupo(id, nombre, descripcion, plegado) {
      const sección = document.createElement(plegado ? 'details' : 'section');
      sección.className = 'sf68-grupo';
      sección.id = id;
      if (plegado) {
        const summary = document.createElement('summary');
        summary.className = 'sf68-encabezado';
        summary.textContent = nombre + ' · ' + descripcion;
        sección.appendChild(summary);
      } else {
        const head = document.createElement('div'); head.className = 'sf68-encabezado';
        const h = document.createElement('h3'); h.textContent = nombre;
        const p = document.createElement('p'); p.textContent = descripcion;
        head.append(h, p);
        sección.appendChild(head);
      }
      contenedor.appendChild(sección);
      return sección;
    }
    function accesos(destino, items) {
      const fila = document.createElement('div'); fila.className = 'sf68-accesos';
      items.filter(Boolean).forEach(el => fila.appendChild(el));
      if (fila.children.length) destino.appendChild(fila);
    }
    const operacion = grupo('sf68-operacion', 'Operación', 'Pedidos, caja, mesas y precios', false);
    accesos(operacion, [acciones[0], acciones[6]]);
    operacion.append(grupos[0], grupos[4]);
    const aviso = document.createElement('details'); aviso.className = 'sf68-ayuda';
    const avisoTexto = document.createElement('summary'); avisoTexto.textContent = 'Pedidos web sin Internet';
    aviso.append(avisoTexto, grupos[1], ayuda); operacion.appendChild(aviso);

    const menu = grupo('sf68-menu', 'Menú y apariencia', 'Productos QR, promociones y marca', false);
    accesos(menu, [acciones[4], acciones[7]]);
    menu.append(grupos[2], grupos[3]);

    const impresion = grupo('sf68-impresoras', 'Impresoras', 'Caja, cocina y barra', false);
    impresion.appendChild(impresoras); // Único acceso a la configuración existente.

    const avanzado = grupo('sf68-avanzado', 'Avanzado', 'Respaldos, importación y fiscal', true);
    const backup = operaciones.querySelector('a[href*="backup"]');
    accesos(avanzado, [acciones[2], acciones[5], backup]);
    if (location.hostname === '127.0.0.1' || location.hostname === 'localhost') {
      const sync = document.createElement('a');
      sync.href = '/desktop/sync-6e/';
      sync.className = 'sf68-link-extra';
      sync.textContent = 'Sincronización offline';
      avanzado.appendChild(sync);
    }
    // El control de cierre de caja se encuentra en Salón: no se duplica aquí.
    grid.hidden = true;
    operaciones.hidden = true;
    tab.dataset.sf68Listo = '1';
    tab.classList.add('sf64-herramientas','sf65-ajustes','sf68-ajustes');
    // Compatibilidad con enlaces anteriores: abrir sección específica sin tabs.
    function abrirHash() {
      const id = location.hash;
      const target = id === '#sm-impresoras-panel' || id === '#sf65-impresion' ? impresion :
                     id === '#sf65-avanzado' ? avanzado : null;
      if (target === avanzado) avanzado.open = true;
      if (target && tab.offsetParent !== null) target.scrollIntoView({block:'nearest'});
    }
    window.addEventListener('hashchange', abrirHash);
    abrirHash();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
}());
