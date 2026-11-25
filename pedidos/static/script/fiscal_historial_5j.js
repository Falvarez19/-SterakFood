(function(){'use strict';
  document.querySelectorAll('form.sf5j-recuperar').forEach(form=>form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!window.confirm('¿Consultar el comprobante en ARCA SIN reenviar ni emitir?'))return;
    const boton=form.querySelector('button'); boton.disabled=true;
    try {
      const csrf=form.querySelector('[name=csrfmiddlewaretoken]').value;
      const r=await fetch(form.action,{method:'POST',headers:{'X-CSRFToken':csrf},credentials:'same-origin'});
      const d=await r.json();
      alert(d.mensaje||d.estado||'Consulta completada.');
      if(r.ok)window.location.reload();
    }catch(_){alert('No se pudo consultar ARCA. No se reenvió el comprobante.');}
    finally {boton.disabled=false;}
  }));
})();
