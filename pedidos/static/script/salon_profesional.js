/* SterakFood | Paso 2A — Filtros y estado del Salón.
   Este módulo SOLO consulta los botones que actualiza script.js.
   No interpreta importes, no guarda cuentas, no imprime ni realiza cobros.
   Se carga después del script.js original: sus listeners de mesa permanecen intactos.
*/
(function () {
  'use strict';

  var salon = document.getElementById('salon-pos');
  var grilla = document.getElementById('grilla-mesas');
  if (!salon || !grilla) return;

  var filtros = Array.prototype.slice.call(salon.querySelectorAll('[data-sf-filtro-mesa]'));
  var total = document.getElementById('sf-salon-total-mesas');
  var ocupadas = document.getElementById('sf-salon-mesas-ocupadas');
  var libres = document.getElementById('sf-salon-mesas-libres');
  var visibles = document.getElementById('sf-salon-mesas-visibles');
  var sinResultados = document.getElementById('sf-salon-sin-resultados');
  var filtroActual = 'todas';
  var redibujoPendiente = false;

  function estaOcupada(mesa) {
    // script.js agrega estas clases cuando la cuenta tiene productos.
    return mesa.classList.contains('is-ocupada') || mesa.classList.contains('mesa-ocupada');
  }

  function actualizarVista() {
    redibujoPendiente = false;
    var mesas = grilla.querySelectorAll('button[data-mesa]');
    var totalOcupadas = 0;
    var totalVisibles = 0;
    Array.prototype.forEach.call(mesas, function (mesa) {
      var ocupada = estaOcupada(mesa);
      if (ocupada) totalOcupadas += 1;
      var mostrar = filtroActual === 'todas' ||
        (filtroActual === 'ocupadas' && ocupada) ||
        (filtroActual === 'libres' && !ocupada);
      // hidden no modifica los eventos ni el contenido de ninguna mesa.
      mesa.hidden = !mostrar;
      if (mostrar) totalVisibles += 1;
    });
    if (total) total.textContent = String(mesas.length);
    if (ocupadas) ocupadas.textContent = String(totalOcupadas);
    if (libres) libres.textContent = String(mesas.length - totalOcupadas);
    if (visibles) visibles.textContent = 'Mostrando ' + totalVisibles + ' de ' + mesas.length + ' mesas';
    if (sinResultados) sinResultados.hidden = totalVisibles !== 0;
  }

  function programarVista() {
    // script.js actualiza varias clases y contenidos en la misma operación.
    // Un solo render evita cálculos redundantes y conserva la velocidad del POS.
    if (redibujoPendiente) return;
    redibujoPendiente = true;
    window.requestAnimationFrame(actualizarVista);
  }

  filtros.forEach(function (boton) {
    boton.addEventListener('click', function () {
      filtroActual = boton.getAttribute('data-sf-filtro-mesa') || 'todas';
      filtros.forEach(function (otro) {
        otro.setAttribute('aria-pressed', otro === boton ? 'true' : 'false');
      });
      programarVista();
    });
  });

  // Detecta actualizaciones provenientes del POS o de nuevos pedidos online.
  // No observa el atributo hidden para evitar bucles con nuestro filtrado.
  if (window.MutationObserver) {
    var observador = new MutationObserver(programarVista);
    observador.observe(grilla, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }
  actualizarVista();
})();
