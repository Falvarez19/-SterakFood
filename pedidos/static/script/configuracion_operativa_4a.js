/* Ajustes operativos por restaurante: mesas, mozos e impresoras.
   Utiliza rutas y validaciones existentes. NO accede a ventas ni tickets. */
(function () {
  'use strict';
  const raiz = document.getElementById('sf-operacion');
  if (!raiz) return;
  const csrf = document.querySelector('#sf-op-csrf input[name="csrfmiddlewaretoken"]')?.value || '';
  const cabeceras = {'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest'};
  const mensaje = (id, texto, error) => {
    const el = document.getElementById(id);
    if (el) { el.textContent = texto || ''; el.dataset.error = error ? '1' : '0'; }
  };
  const leer = async (res) => {
    // Un error en servidor nunca debe producir que desaparezcan los datos locales.
    const info = await res.json().catch(() => ({}));
    if (!res.ok || info.status !== 'ok') throw new Error(info.mensaje || 'No se pudo completar la operación.');
    return info;
  };

  document.getElementById('op-mesas-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    try {
      const numero = Number(form.elements.numero_mesas_visibles.value);
      if (!Number.isInteger(numero) || numero < 1 || numero > 100) throw new Error('Elegí entre 1 y 100 mesas.');
      await leer(await fetch(raiz.dataset.mesasUrl, {method: 'POST', credentials: 'same-origin', headers: {...cabeceras, 'Content-Type': 'application/json'}, body: JSON.stringify({numero_mesas_visibles: numero})}));
      mensaje('op-mesas-estado', 'Guardado. Volvé a Salón para ver la nueva grilla.', false);
    } catch(e) { mensaje('op-mesas-estado', e.message, true); }
    finally {btn.disabled = false;}
  });

  const lista = document.getElementById('op-mozos-lista');
  const actualizarTotal = () => {
    document.getElementById('op-mozos-total').textContent = lista.querySelectorAll('li[data-mozo-id]').length + ' registrados';
  };
  document.getElementById('op-mozos-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const nombre = form.elements.nombre.value.trim();
    if (nombre.length < 2) return mensaje('op-mozos-estado', 'Escribí el nombre completo.', true);
    const btn = form.querySelector('button[type="submit"]');btn.disabled = true;
    try {
      const fd = new FormData(); fd.set('nombre', nombre);
      const r = await leer(await fetch(raiz.dataset.mozosAgregar, {method:'POST', credentials:'same-origin', headers:cabeceras, body:fd}));
      const item = document.createElement('li'); item.dataset.mozoId = String(r.mozo.id);
      const texto = document.createElement('span'); const id = document.createElement('b');id.textContent = r.mozo.id + '. ';texto.append(id,document.createTextNode(r.mozo.nombre));
      const borrar = document.createElement('button');borrar.type='button';borrar.className='sf-op__btn sf-op__btn--discreto';borrar.dataset.mozoEliminar=r.mozo.id;borrar.textContent='Quitar';
      item.append(texto,borrar);lista.append(item);form.reset();actualizarTotal();
      mensaje('op-mozos-estado', 'Mozo agregado. Aparecerá en Salón al volver a abrirlo.',false);
      form.elements.nombre.focus();
    } catch(e) {mensaje('op-mozos-estado',e.message,true);}
    finally {btn.disabled=false;}
  });
  lista.addEventListener('click', async (event) => {
    const btn=event.target.closest('button[data-mozo-eliminar]');if(!btn)return;
    const id=btn.dataset.mozoEliminar;
    if(!window.confirm('¿Quitar este mozo de la lista?'))return;
    btn.disabled=true;
    try {
      const url=raiz.dataset.mozosEliminarPatron.replace('999999',encodeURIComponent(id));
      await leer(await fetch(url,{method:'POST',credentials:'same-origin',headers:cabeceras}));
      btn.closest('li').remove();actualizarTotal();mensaje('op-mozos-estado','Mozo quitado.',false);
    }catch(e){btn.disabled=false;mensaje('op-mozos-estado',e.message,true);}
  });

  const impresoras = document.getElementById('op-impresoras-form');
  async function cargarImpresoras(){
    try {
      const info = await leer(await fetch(raiz.dataset.impresorasGet,{credentials:'same-origin'}));
      const c=info.configuracion;
      for(const campo of ['caja_modo','caja_windows','caja_ip','cocina_modo','cocina_windows','ip_cocina','barra_modo','barra_windows','ip_barra','ancho_ticket']){
        if(impresoras.elements[campo]) impresoras.elements[campo].value = c[campo] ?? '';
      }
      if(window.SterakPrinter6F3)window.SterakPrinter6F3.refresh(impresoras);
      document.getElementById('op-impresoras-conexion').textContent = c.vinculada?'PC vinculada':'Sin vincular';
    }catch(e){mensaje('op-impresoras-estado',e.message,true);document.getElementById('op-impresoras-conexion').textContent='Sin datos';}
  }
  impresoras.addEventListener('submit',async(event)=>{
    event.preventDefault(); const btn=impresoras.querySelector('button[type="submit"]');btn.disabled=true;
    try{
      const c={};for(const k of ['caja_modo','caja_windows','caja_ip','cocina_modo','cocina_windows','ip_cocina','barra_modo','barra_windows','ip_barra','ancho_ticket'])c[k]=impresoras.elements[k].value.trim();
      const info=await leer(await fetch(raiz.dataset.impresorasPost,{method:'POST',credentials:'same-origin',headers:{...cabeceras,'Content-Type':'application/json'},body:JSON.stringify(c)}));
      mensaje('op-impresoras-estado',info.mensaje||'Guardado.',false);
    }catch(e){mensaje('op-impresoras-estado',e.message,true);}finally{btn.disabled=false;}
  });
  document.getElementById('op-descargar-vinculo').addEventListener('click',async(event)=>{
    const btn=event.currentTarget;
    if(!window.confirm('¿Generar una nueva vinculación? La anterior dejará de funcionar.'))return;
    btn.disabled=true;
    try{
      const info=await leer(await fetch(raiz.dataset.impresorasVincular,{method:'POST',credentials:'same-origin',headers:cabeceras}));
      const texto=JSON.stringify(info.archivo,null,2);
      const blob=new Blob([texto],{type:'application/json'});
      const url=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=url;a.download=info.nombre_archivo||'VINCULAR_IMPRESORA_STERAKFOOD.json';document.body.append(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
      mensaje('op-impresoras-estado','Vinculación descargada. Guardá el archivo fuera del repositorio.',false);
      document.getElementById('op-impresoras-conexion').textContent='Nueva vinculación creada';
    }catch(e){mensaje('op-impresoras-estado',e.message,true);}finally{btn.disabled=false;}
  });
  cargarImpresoras();
})();
