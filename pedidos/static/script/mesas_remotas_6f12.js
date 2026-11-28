/* SterakFood 6F.12A - mostrar mesas espejo de Desktop en Web SIN copiarlas
   al estado localStorage del POS. Bloquear clicks en mesas del espejo. */
(function () {
  'use strict';
  var salon = document.getElementById('salon-pos');
  if (!salon || salon.hasAttribute('data-backup-url')) return; // no corre en Desktop
  var header = salon.querySelector('.salon-pos__header');
  if (!header) return;
  var aviso = document.createElement('div');
  aviso.className = 'sf12-mensaje';
  aviso.setAttribute('role', 'status');
  aviso.textContent = 'Consultando mesas de Desktop…';
  header.appendChild(aviso);
  var remotas = Object.create(null);
  var storageKey = 'sistemasm_salon_cuentas_v2';
  var modalAbierto = false;

  function abiertaEnWeb(numero) {
    try {
      var c = JSON.parse(localStorage.getItem(storageKey) || '{}')[numero];
      return !!(c && Array.isArray(c.items) && c.items.some(function (i) { return Number(i.cantidad) > 0; }));
    } catch (_) { return false; }
  }

  function dinero(n) {
    var a = Number(n);
    if (!Number.isFinite(a)) return String(n);
    return '$' + a.toLocaleString('es-AR', {maximumFractionDigits: 2});
  }

  function detalle(numero) {
    if (modalAbierto || !remotas[numero]) return;
    var datos = remotas[numero];
    var mesa = datos.mesa;
    var lineas = [
      'Equipo: ' + datos.etiqueta,
      'Conexión: ' + (datos.conectada ? 'En línea' : 'Sin conexión / estado anterior'),
      'Última actualización: ' + datos.actualizado,
      'Mozo: ' + (mesa.mozo || 'Sin asignar'),
      ''
    ];
    (mesa.items || []).forEach(function (item) {
      lineas.push(String(item.cantidad) + 'x ' + String(item.nombre) + ' — ' + dinero(Number(item.cantidad) * Number(item.precio)));
    });
    lineas.push('', 'TOTAL DE REFERENCIA: ' + dinero(mesa.total),
      '', 'SOLO CONSULTA: cobrala o modificala desde Desktop.');
    if (abiertaEnWeb(numero)) lineas.unshift('ATENCIÓN: esta mesa también tiene datos locales en Web. No operes ambas versiones a la vez.', '');
    if (window.Swal && window.Swal.fire) {
      modalAbierto = true;
      window.Swal.fire({title: 'Mesa ' + numero + ' · Desktop', text: lineas.join('\n'),
        confirmButtonText: 'Cerrar', width: '480px',
        background: 'var(--card-bg)', color: 'var(--text-color)'}).finally(function () {modalAbierto = false;});
    } else window.alert(lineas.join('\n'));
  }

  function marcar() {
    Array.prototype.forEach.call(salon.querySelectorAll('button[data-mesa]'), function (boton) {
      var numero = String(boton.getAttribute('data-mesa'));
      var info = remotas[numero];
      boton.classList.toggle('sf12-desktop', !!info);
      boton.classList.toggle('sf12-conflicto', !!info && abiertaEnWeb(numero));
      if (info) {
        boton.setAttribute('data-sf12-etiqueta', (info.conectada ? 'DESKTOP' : 'DESKTOP SIN CONEXIÓN') + ' · ' + dinero(info.mesa.total));
        boton.setAttribute('title', 'Mesa ocupada en Desktop: solo consulta; abrir para ver detalle');
      } else if (boton.hasAttribute('data-sf12-etiqueta')) {
        boton.removeAttribute('data-sf12-etiqueta');
        boton.removeAttribute('title');
      }
    });
  }

  function actualizar(data) {
    if (!data || data.status !== 'ok' || !Array.isArray(data.dispositivos)) throw Error('Datos de sincronización inválidos');
    var entradas = Object.create(null), repetidas = 0, stale = 0;
    data.dispositivos.forEach(function (d) {
      if (!d || !d.mesas) return;
      Object.keys(d.mesas).forEach(function (numero) {
        var mesa = d.mesas[numero];
        if (!mesa || !Array.isArray(mesa.items) || mesa.items.length === 0) return;
        if (entradas[numero]) {repetidas++; return;}
        entradas[numero] = {mesa: mesa, etiqueta: d.etiqueta || 'PC', conectado: !!d.conectada,
          conectada: !!d.conectada, actualizado: d.actualizado || '?'};
        if (!d.conectada) stale++;
      });
    });
    remotas = entradas;
    marcar();
    var cantidad = Object.keys(entradas).length;
    var conflictosWeb = Object.keys(entradas).filter(abiertaEnWeb).length;
    aviso.textContent = cantidad ? 'Desktop: ' + cantidad + ' mesa(s) · solo consulta' +
      (stale ? ' · ' + stale + ' sin conexión' : '') +
      (conflictosWeb || repetidas ? ' · ATENCIÓN: ' + (conflictosWeb + repetidas) + ' conflicto(s)' : '')
      : 'Desktop: sin mesas abiertas sincronizadas';
    aviso.classList.toggle('sf12-alerta', !!(conflictosWeb || repetidas || stale));
  }

  function consultar() {
    if (document.hidden) return;
    fetch('/salon/api/mesas-desktop-6f12/', {credentials:'same-origin', cache:'no-store'})
      .then(function (res) {return res.json().catch(function(){return {};}).then(function(d) {
        if (!res.ok) throw Error(d.error || 'HTTP ' + res.status);
        return d;
      });})
      .then(actualizar)
      .catch(function(error) {aviso.textContent = 'Desktop: sincronización no disponible (' + error.message + ')';
        aviso.classList.add('sf12-alerta');});
  }

  salon.addEventListener('click', function (e) {
    var boton = e.target.closest && e.target.closest('button[data-mesa]');
    if (!boton) return;
    var numero = String(boton.getAttribute('data-mesa'));
    if (!remotas[numero]) return;
    e.preventDefault(); e.stopImmediatePropagation();
    detalle(numero);
  }, true);

  var rapida = document.getElementById('input-mesa-rapida');
  if (rapida) rapida.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter') return;
    var numero = String(Number(rapida.value));
    if (!remotas[numero]) return;
    e.preventDefault(); e.stopImmediatePropagation();
    detalle(numero);
  }, true);
  var observer;
  if (window.MutationObserver) {
    var grid = document.getElementById('grilla-mesas');
    if (grid) {
      observer = new MutationObserver(function() { marcar(); });
      observer.observe(grid, {childList:true, subtree:true});
    }
  }
  consultar();
  setInterval(consultar, 15000);
})();
