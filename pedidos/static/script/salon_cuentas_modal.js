/* SterakFood · Cuentas corrientes dentro de Salón POS, sin iframe ni pestaña externa. */
(function () {
  'use strict';
  const abrir = document.getElementById('salon-abrir-cuentas');
  const modal = document.getElementById('salon-cuentas-dialog');
  const contenido = document.getElementById('sc-dialog-content');
  if (!abrir || !modal || !contenido) return;
  const cerrarBtn = modal.querySelector('.sc-dialog__close');
  let focoPrevio = null;
  let peticion = null;
  let secuencia = 0;

  function cerrar() {
    if (modal.hidden) return;
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (peticion) { peticion.abort(); peticion = null; }
    secuencia++;
    if (focoPrevio && focoPrevio.isConnected) focoPrevio.focus();
  }

  function estado(mensaje, error) {
    contenido.replaceChildren();
    const aviso = document.createElement('div');
    aviso.className = 'sc-dialog__status' + (error ? ' is-error' : '');
    aviso.setAttribute('role', error ? 'alert' : 'status');
    aviso.textContent = mensaje;
    contenido.appendChild(aviso);
    if (error) {
      const intentar = document.createElement('button');
      intentar.type = 'button';
      intentar.className = 'sc-dialog__retry';
      intentar.textContent = 'Reintentar';
      intentar.addEventListener('click', cargar);
      contenido.appendChild(intentar);
    }
  }

  async function cargar() {
    if (peticion) peticion.abort();
    const actual = ++secuencia;
    peticion = new AbortController();
    const controlador = peticion;
    estado('Cargando cuentas corrientes…', false);
    try {
      const respuesta = await fetch(contenido.dataset.src, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        signal: controlador.signal,
        cache: 'no-store'
      });
      if (respuesta.redirected || respuesta.status === 401 || respuesta.status === 403) {
        throw new Error('Tu sesión venció. Volvé a iniciar sesión desde el panel.');
      }
      if (!respuesta.ok) throw new Error('No se pudieron cargar las cuentas (HTTP ' + respuesta.status + ').');
      const documento = new DOMParser().parseFromString(await respuesta.text(), 'text/html');
      const panel = documento.getElementById('tab-cuentas');
      if (!panel) throw new Error('No se recibió la sección de Cuentas. Revisá tu sesión.');
      if (actual !== secuencia || modal.hidden) return;
      contenido.replaceChildren(panel);
      panel.style.display = 'block';
      if (typeof window.sterakInitBuscadorCuentas === 'function') window.sterakInitBuscadorCuentas();
      if (typeof window.sterakInitAjaxCuentas === 'function') window.sterakInitAjaxCuentas();
    } catch (error) {
      if (error.name !== 'AbortError' && actual === secuencia && !modal.hidden) {
        estado(error.message || 'No se pudieron cargar las cuentas.', true);
      }
    } finally {
      if (peticion === controlador) peticion = null;
    }
  }

  function mostrar() {
    if (!modal.hidden) return;
    focoPrevio = document.activeElement;
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    cerrarBtn.focus();
    cargar(); // obtener siempre saldos recientes, no cargar cuentas durante el inicio del Salón
  }

  abrir.addEventListener('click', mostrar);
  modal.querySelectorAll('[data-sc-cerrar]').forEach(function (elemento) {
    elemento.addEventListener('click', cerrar);
  });
  document.addEventListener('keydown', function (event) {
    if (modal.hidden) return;
    if (event.key === 'Escape') { event.preventDefault(); cerrar(); return; }
    if (event.key !== 'Tab') return;
    const visibles = Array.from(modal.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])'))
      .filter(function (elemento) { return elemento.getClientRects().length > 0 && elemento.tabIndex !== -1; });
    if (!visibles.length) return;
    if (event.shiftKey && document.activeElement === visibles[0]) { event.preventDefault(); visibles[visibles.length-1].focus(); }
    else if (!event.shiftKey && document.activeElement === visibles[visibles.length-1]) { event.preventDefault(); visibles[0].focus(); }
  });
})();
