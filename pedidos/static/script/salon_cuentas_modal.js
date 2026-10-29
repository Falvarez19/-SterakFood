/* Cuenta corriente dentro del POS: ventana flotante, sin navegar ni abrir pestañas. */
(function(){
  'use strict';
  const abrir=document.getElementById('salon-abrir-cuentas');
  const modal=document.getElementById('salon-cuentas-dialog');
  const frame=document.getElementById('sc-dialog-frame');
  if(!abrir||!modal||!frame)return;
  let focoAnterior=null;
  const ventana=modal.querySelector('.sc-dialog__window');
  const closeButton=modal.querySelector('.sc-dialog__close');
  function cerrar(){
    if(modal.hidden)return;
    modal.hidden=true;modal.setAttribute('aria-hidden','true');
    document.body.style.overflow='';
    if(focoAnterior&&focoAnterior.isConnected)focoAnterior.focus();
  }
  function mostrar(){
    focoAnterior=document.activeElement;
    // Recargar las cuentas al abrir para reflejar pagos recientes, nunca al cerrar.
    frame.src=frame.dataset.src+'?v='+Date.now();
    modal.hidden=false;modal.setAttribute('aria-hidden','false');
    document.body.style.overflow='hidden';
    closeButton.focus();
  }
  abrir.addEventListener('click',mostrar);
  modal.querySelectorAll('[data-sc-cerrar]').forEach(b=>b.addEventListener('click',cerrar));
  document.addEventListener('keydown',e=>{
    if(modal.hidden)return;
    if(e.key==='Escape'){e.preventDefault();cerrar();}
    if(e.key==='Tab'&&document.activeElement===closeButton&&e.shiftKey){
      e.preventDefault();ventana.focus();
    }
  });
})();
