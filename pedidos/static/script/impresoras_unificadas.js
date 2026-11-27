/* SterakFood 6F.9 R2. Misma experiencia Web y Desktop, sin guardar dos veces. */
(function(){
  'use strict';
  const url='http://127.0.0.1:8765/desktop/operaciones/impresoras/detectadas/';
  document.querySelectorAll('[data-sf9-row]').forEach(function(row){
    const mode=row.querySelector('[data-sf9-method]');
    if(!mode) return;
    function refresh(){
      row.querySelectorAll('[data-sf9-kind]').forEach(el=>{el.hidden=el.dataset.sf9Kind!==mode.value;});
      const test=row.querySelector('.sf9-testbutton');
      if(test) test.disabled=mode.value==='off';
    }
    mode.addEventListener('change',refresh);refresh();
  });
  document.querySelectorAll('.sf9-testbutton').forEach(button=>{
    button.addEventListener('click',e=>{
      if(!window.confirm('¿Enviar UNA prueba NO FISCAL a la impresora ya guardada de este sector?'))e.preventDefault();
    });
  });
  const btn=document.getElementById('sf9-detect');
  if(!btn)return;
  btn.addEventListener('click',async()=>{
    btn.disabled=true;
    const status=document.getElementById('sf9-detect-msg');
    status.textContent='Consultando impresoras instaladas en esta PC...';
    try{
      const local=(location.hostname==='127.0.0.1'||location.hostname==='localhost');
      const resp=await fetch(url,{method:'GET',mode:'cors',credentials:local?'same-origin':'omit',cache:'no-store'});
      const data=await resp.json();
      if(!resp.ok||!data.ok)throw new Error('El agente local no respondió.');
      const list=document.getElementById('sf9-win-printers');
      list.replaceChildren();
      (Array.isArray(data.impresoras)?data.impresoras:[]).forEach(p=>{
        if(!p.nombre)return;
        const opt=document.createElement('option');opt.value=p.nombre;opt.label=p.conexion||'Windows';list.appendChild(opt);
      });
      status.textContent=list.children.length+' impresoras detectadas. Escribí o elegí el nombre en cada fila.';
    }catch(err){
      status.textContent='No se pudo acceder a Desktop desde este navegador. Ingresá el nombre Windows o IP manualmente.';
    }finally{btn.disabled=false;}
  });
}());
