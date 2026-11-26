/* SterakFood 6F3. Detecta colas de Windows SOLO en el equipo que abre el navegador.
 * La web de Render no puede consultar el hardware del servidor.
 * Sin agente local, se pueden escribir nombres Windows o IP manualmente.
 */
(function () {
  'use strict';
  const MODOS = ['caja', 'cocina', 'barra'];
  const URL = 'http://127.0.0.1:8765/desktop/operaciones/impresoras/detectadas/';
  function actualizar(form) {
    MODOS.forEach((sector) => {
      const modo = form.elements[sector + '_modo'];
      if (!modo) return;
      form.querySelectorAll('[data-sf6f3-sector="' + sector + '"]').forEach((el) => {
        el.hidden = el.dataset.sf6f3Mostrar !== modo.value;
      });
    });
  }
  function detectadas(form, impresoras) {
    MODOS.forEach((sector) => {
      const select = form.querySelector('[data-sf6f3-select="' + sector + '"]');
      if (!select) return;
      const input = form.elements[sector + '_windows'];
      const actual = input ? input.value : '';
      select.replaceChildren();
      const vacio = new Option(impresoras.length ? 'Seleccionar impresora instalada…' : 'No se encontraron impresoras', '');
      select.add(vacio);
      let encontrado = false;
      impresoras.forEach((p) => {
        const nombre = String(p.nombre || '').slice(0, 120);
        if (!nombre) return;
        const texto = nombre + ' · ' + (p.conexion || 'Windows');
        const opcion = new Option(texto, nombre);
        select.add(opcion);
        if (nombre === actual) encontrado = true;
      });
      if (actual && !encontrado) select.add(new Option(actual + ' (configurada)', actual));
      if (actual) select.value = actual;
      select.onchange = () => { if (input && select.value) input.value = select.value; };
    });
  }
  window.SterakPrinter6F3 = {refresh: actualizar};
  function init() {
    document.querySelectorAll('#sm-impresoras-form, #op-impresoras-form, #sf6f3-desktop-form').forEach((form) => {
      MODOS.forEach((s) => form.elements[s + '_modo']?.addEventListener('change', () => actualizar(form)));
      actualizar(form);
      const btn = form.querySelector('[data-sf6f3-buscar]');
      const aviso = form.querySelector('[data-sf6f3-estado]');
      if (!btn) return;
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        if (aviso) aviso.textContent = 'Buscando impresoras instaladas en esta PC…';
        try {
          const resp = await fetch(URL, {method: 'GET', mode: 'cors', credentials: (location.hostname === '127.0.0.1' || location.hostname === 'localhost') ? 'same-origin' : 'omit', cache: 'no-store'});
          const info = await resp.json();
          if (!resp.ok || !info.ok) throw new Error(info.mensaje || 'No se pudo consultar Windows.');
          detectadas(form, Array.isArray(info.impresoras) ? info.impresoras : []);
          if (aviso) aviso.textContent = (info.impresoras || []).length + ' impresoras instaladas encontradas. ' + (info.advertencia || '');
        } catch (err) {
          if (aviso) aviso.textContent = 'No se pudo conectar con SterakFood Desktop en esta PC. Abrilo o ingresá el nombre / IP manualmente.';
        } finally { btn.disabled = false; }
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
