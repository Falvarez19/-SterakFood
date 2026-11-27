/* SterakFood 6F.11 - impresoras en modal compartido (Render y Desktop).
   Reutiliza la pagina y los endpoints existentes; NO modifica impresion ni ventas.
*/
(function () {
  'use strict';
  const MODAL_ID = 'sterak-printer-modal-6f11';
  let modal, frame, closeBtn, lastFocus, oldOverflow;

  function isPrinterLink(anchor) {
    if (!anchor || !anchor.href) return false;
    let url;
    try { url = new URL(anchor.href, location.href); } catch (_) { return false; }
    if (url.origin !== location.origin) return false;
    return url.pathname.replace(/\/+$/, '/') === '/dashboard/impresoras/' ||
           url.pathname.replace(/\/+$/, '/') === '/desktop/operaciones/impresoras/';
  }

  function ensureModal() {
    if (modal) return;
    modal = document.createElement('div');
    modal.id = MODAL_ID;
    modal.hidden = true;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', MODAL_ID + '-title');
    modal.innerHTML =
      '<div class="sf11-modal-scrim"></div>' +
      '<div class="sf11-modal-window">' +
      ' <header class="sf11-modal-head">' +
      '  <div id="' + MODAL_ID + '-title"><strong>Impresoras</strong><span>Caja · Cocina · Barra</span></div>' +
      '  <button type="button" class="sf11-modal-close" aria-label="Cerrar impresoras">Cerrar ×</button>' +
      ' </header>' +
      ' <iframe class="sf11-modal-frame" title="Configuración de impresoras" loading="eager"></iframe>' +
      '</div>';
    document.body.appendChild(modal);
    frame = modal.querySelector('iframe');
    closeBtn = modal.querySelector('.sf11-modal-close');
    closeBtn.addEventListener('click', closeModal);
    frame.addEventListener('load', function () {
      try {
        frame.contentWindow.addEventListener('keydown', function (event) {
          if (event.key === 'Escape') { event.preventDefault(); closeModal(); }
        });
      } catch (_) { /* no-op */ }
      // Siempre se carga desde el MISMO origen. No accede a ningún servidor ajeno.
      try {
        const doc = frame.contentDocument;
        if (!doc || !doc.head) return;
        if (doc.getElementById('sf11-embedded-style')) return;
        const style = doc.createElement('style');
        style.id = 'sf11-embedded-style';
        style.textContent =
          '.sf9-header{display:none!important}' +
          '.sf9-wrap{max-width:none!important;margin:0!important;padding:10px 14px 20px!important}' +
          '.sf9-main{margin-top:0!important}' +
          'body{min-height:0!important}' +
          '@media(max-width:680px){.sf9-wrap{padding:8px!important}}';
        doc.head.appendChild(style);
      } catch (_) { /* El formulario sigue siendo accesible aunque falle la mejora visual. */ }
    });
  }

  function openModal(href, opener) {
    ensureModal();
    if (!modal.hidden) return;
    lastFocus = opener || document.activeElement;
    oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const url = new URL(href, location.href);
    // El destino es el formulario existente de este mismo servidor.
    url.searchParams.set('modal', '1');
    frame.src = url.toString();
    modal.hidden = false;
    closeBtn.focus();
  }

  function closeModal() {
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = oldOverflow === undefined ? '' : oldOverflow;
    // Liberar la pagina interna; cerrar el modal no manda ninguna solicitud POST.
    frame.removeAttribute('src');
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
  }

  document.addEventListener('click', function (event) {
    const anchor = event.target.closest && event.target.closest('a[href]');
    if (!isPrinterLink(anchor) || event.defaultPrevented) return;
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey ||
        anchor.target === '_blank' || anchor.hasAttribute('download')) return;
    event.preventDefault();
    const details = anchor.closest('details[open]');
    if (details) details.open = false;
    openModal(anchor.href, anchor);
  });
  document.addEventListener('keydown', function (event) {
    if (!modal || modal.hidden) return;
    if (event.key === 'Escape') { event.preventDefault(); closeModal(); }
    // En el contenedor solo existe el boton de cerrar; la navegacion del
    // formulario queda dentro del iframe sin interferir con Salón.
  });
})();
