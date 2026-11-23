/* SterakFood 4F — Diagnóstico fiscal únicamente de lectura. */
(function () {
  'use strict';
  const form = document.querySelector('#sf-arca-diagnostico-form');
  const boton = document.querySelector('#sf-arca-diagnostico-boton');
  const resumen = document.querySelector('#sf-arca-diagnostico-resumen');
  const filas = document.querySelectorAll('[data-arca-paso]');
  if (!form || !boton || !resumen) return;
  const nombres = {ok: 'Correcto', aviso: 'Revisar', pendiente: 'Pendiente', error: 'Error'};
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    boton.disabled = true;
    resumen.textContent = 'Comprobando conexión con ARCA…';
    resumen.dataset.estado = 'pendiente';
    filas.forEach((fila) => {
      fila.querySelector('[data-estado]').textContent = 'Comprobando…';
      fila.querySelector('[data-detalle]').textContent = '';
    });
    try {
      const res = await fetch(form.action, {
        method: 'POST', body: new FormData(form),
        credentials: 'same-origin', cache: 'no-store', headers: {'Accept': 'application/json'}
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'No se pudo completar el diagnóstico.');
      filas.forEach((fila) => {
        const paso = data.pasos[fila.dataset.arcaPaso];
        if (!paso) return;
        fila.querySelector('[data-estado]').textContent = nombres[paso.estado] || 'Sin estado';
        fila.querySelector('[data-estado]').dataset.estado = paso.estado;
        fila.querySelector('[data-detalle]').textContent = paso.detalle;
      });
      resumen.textContent = data.mensaje + ' Entorno: ' + data.entorno + '.';
      resumen.dataset.estado = data.resultado;
    } catch (err) {
      resumen.textContent = err && err.message ? err.message : 'No se pudo completar la consulta.';
      resumen.dataset.estado = 'error';
    } finally {
      boton.disabled = false;
    }
  });
})();
