/* SterakFood · "Para llevar" desde el MISMO catálogo y las opciones del menú público. */
(function () {
  'use strict';
  const panel = document.getElementById('pl-dialog');
  const abrir = document.getElementById('pl-abrir');
  if (!panel || !abrir) return;
  const $ = (id) => document.getElementById(id);
  const catalogo = $('pl-catalogo'), carrito = $('pl-carrito'), historial = $('pl-pedidos');
  const submit = $('pl-enviar'), aviso = $('pl-aviso'), totalElemento = $('pl-total');
  const configurador = $('pl-configurador'), grupos = $('pl-config-grupos');
  const pedidoCeliaco = $('pl-celiaco-pedido');
  const categorias = $('pl-categorias');
  let categoriaActual = 'Todas';
  const vistaNueva = $('pl-contenido-nuevo'), vistaHistorial = $('pl-vista-historial');
  function cambiarVista(vista) {
    const historia = vista === 'historial';
    vistaNueva.hidden = historia;
    vistaHistorial.hidden = !historia;
    $('pl-tab-nuevo').classList.toggle('is-active', !historia);
    $('pl-tab-historial').classList.toggle('is-active', historia);
    $('pl-tab-nuevo').setAttribute('aria-pressed', String(!historia));
    $('pl-tab-historial').setAttribute('aria-pressed', String(historia));
    if (!historia) $('pl-buscar').focus();
  }
  const csrf = document.querySelector('#salon-csrf-form input[name=csrfmiddlewaretoken]')?.value || '';
  const NOMBRES = [
    ['variante', 'Variante'], ['guarnicion', 'Guarnición'],
    ['punto', 'Punto de cocción'], ['relleno', 'Relleno'],
    ['salsa', 'Salsa'], ['hielo', 'Hielo'], ['adicional', 'Adicionales']
  ];
  let productos = [], elegido = null, busy = false, focoAnterior = null;
  const cart = new Map();
  let solicitud = nuevaSolicitud();
  const money = (v) => new Intl.NumberFormat('es-AR', {style: 'currency', currency: 'ARS'}).format(v || 0);
  const lower = (s) => String(s || '').toLocaleLowerCase('es-AR');
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (cls) node.className = cls;
    return node;
  };
  function nuevaSolicitud() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    if (window.crypto?.getRandomValues) {
      const b = new Uint8Array(16); window.crypto.getRandomValues(b);
      b[6] = (b[6] & 0x0f) | 0x40; b[8] = (b[8] & 0x3f) | 0x80;
      return [...b].map((v,i) => v.toString(16).padStart(2,'0') + ([3,5,7,9].includes(i) ? '-' : '')).join('');
    }
    throw new Error('Abrí el sistema desde HTTPS para crear pedidos con seguridad.');
  }
  function notify(txt, error=false) {
    aviso.textContent = txt;
    aviso.className = 'pl-aviso ' + (error ? 'is-error' : 'is-success');
  }
  function costoExtra(opcion) {
    let total = 0;
    for (const m of String(opcion).matchAll(/\(([+-])(\d+(?:\.\d+)?)\)/g)) {
      total += (m[1] === '+' ? 1 : -1) * Number(m[2]);
    }
    return total;
  }
  function precioFinal(producto, opciones) {
    let n = Number(producto.precio);
    for (const [clave] of NOMBRES) {
      const valores = clave === 'adicional' ? (opciones[clave] || []) : [opciones[clave] || ''];
      valores.forEach(v => n += costoExtra(v));
    }
    return n;
  }
  function tieneOpciones(p) {
    return NOMBRES.some(([clave]) => (p.opciones?.[clave] || []).length);
  }
  function renderCategorias() {
    const lista = ['Todas', ...new Set(productos.map(p => p.categoria || 'Menú'))];
    if (!lista.includes(categoriaActual)) categoriaActual = 'Todas';
    categorias.replaceChildren();
    lista.forEach(cat => {
      const boton = el('button', cat, 'pl-categoria' + (cat===categoriaActual ? ' is-active' : ''));
      boton.type='button'; boton.setAttribute('aria-pressed', String(cat===categoriaActual));
      boton.onclick=()=>{categoriaActual=cat;renderCategorias();renderCatalogo();};
      categorias.append(boton);
    });
  }
  function renderCatalogo() {
    const q = lower($('pl-buscar').value.trim());
    catalogo.replaceChildren();
    const lista = productos.filter(p => (categoriaActual==='Todas' || (p.categoria||'Menú')===categoriaActual)
      && (!q || [p.nombre,p.codigo,p.categoria].some(x => lower(x).includes(q))));
    if (!lista.length) {
      catalogo.append(el('p', q ? 'No encontramos ese producto. Probá otro nombre.' : 'No hay productos en esta categoría.', 'pl-empty'));
      return;
    }
    for (const p of lista.slice(0,200)) {
      const btn = el('button',undefined,'pl-producto'); btn.type = 'button';
      if (p.imagen) {
        const foto = el('img'); foto.src = p.imagen; foto.alt = ''; foto.loading = 'lazy';
        foto.className = 'pl-miniatura'; btn.append(foto);
      } else {
        btn.append(el('span','🍽️','pl-miniatura pl-miniatura-vacia'));
      }
      const info = el('span',undefined,'pl-producto-info');
      info.append(el('strong',p.nombre),el('small',`${p.categoria || 'Menú'} · ${tieneOpciones(p) ? 'Elegir variante' : 'Agregar directo'}`));
      btn.append(info);
      const accion=el('span',undefined,'pl-producto-accion');
      accion.append(el('span',money(Number(p.precio)),'pl-precio-producto'),el('span',tieneOpciones(p)?'Elegir ›':'+ Agregar','pl-boton-sumar'));
      btn.append(accion);
      btn.onclick = () => {
        if (tieneOpciones(p)) mostrarConfigurador(p);
        else agregarItem(p,Object.fromEntries(NOMBRES.map(([clave])=>[clave, clave==='adicional'?[]:''])),false);
      };
      catalogo.append(btn);
    }
  }
  function cerrarConfigurador() {
    configurador.hidden = true; elegido = null;
  }
  function opcionesElegidas() {
    const seleccion = {};
    let faltante = null;
    for (const [clave,label] of NOMBRES) {
      const disponibles = elegido.opciones?.[clave] || [];
      if (clave === 'adicional') {
        seleccion[clave] = [...grupos.querySelectorAll('input[data-tipo="adicional"]:checked')].map(e=>e.value);
      } else {
        const marcado = [...grupos.querySelectorAll('input[data-tipo="' + clave + '"]:checked')][0];
        seleccion[clave] = marcado?.value || '';
        if (disponibles.length && !marcado && !faltante) faltante = label;
      }
    }
    return {seleccion, faltante};
  }
  function actualizarPrecioConfiguracion() {
    if (!elegido) return;
    $('pl-config-precio').textContent = money(precioFinal(elegido,opcionesElegidas().seleccion));
  }
  function mostrarConfigurador(producto) {
    elegido = producto;
    $('pl-aviso-celiaco').checked = false;
    configurador.hidden = false;
    $('pl-config-titulo').textContent = 'Elegí cómo querés ' + producto.nombre;
    grupos.replaceChildren();
    for (const [clave, label] of NOMBRES) {
      const opciones = producto.opciones?.[clave] || [];
      if (!opciones.length) continue;
      const grupo = el('fieldset',undefined,'pl-opciones-grupo');
      grupo.append(el('legend',label + (clave==='adicional' ? ' (opcionales)' : ' *')));
      for (const opcion of opciones) {
        const fila = el('label',undefined,'pl-opcion');
        const control = el('input'); control.type = clave==='adicional' ? 'checkbox' : 'radio';
        control.name = 'pl-option-' + clave; control.dataset.tipo = clave; control.value = opcion;
        control.onchange = actualizarPrecioConfiguracion;
        fila.append(control,el('span',opcion));grupo.append(fila);
      }
      grupos.append(grupo);
    }
    actualizarPrecioConfiguracion();
    $('pl-config-cancelar').focus();
  }
  function agregarItem(producto, opciones, avisoCeliaco=false) {
    // Una misma milanesa puede salir normal y otra con alerta de celiaquía.
    const clave = JSON.stringify([producto.id, NOMBRES.map(([c])=>opciones[c] || (c==='adicional'?[]:'')), avisoCeliaco]);
    const item = cart.get(clave) || {producto, opciones, avisoCeliaco, cantidad:0};
    if (item.cantidad >= 99) return notify('Máximo 99 unidades por combinación.',true);
    item.cantidad += 1; cart.set(clave,item);
    cerrarConfigurador();renderCart();notify('✓ Producto agregado al pedido.');
  }
  function detalles(item) {
    return NOMBRES.flatMap(([clave]) => clave==='adicional' ? (item.opciones[clave]||[]) : (item.opciones[clave] ? [item.opciones[clave]] : []));
  }
  // La casilla del pedido completo tiene prioridad; la selección individual se conserva.
  function tieneAlertaCeliaco(item) {
    return !!(pedidoCeliaco.checked || item.avisoCeliaco);
  }
  function marcarCeliaco(clave,item) {
    cart.delete(clave);
    item.avisoCeliaco = !item.avisoCeliaco;
    const nuevaClave=JSON.stringify([item.producto.id, NOMBRES.map(([c])=>item.opciones[c] || (c==='adicional'?[]:'')),item.avisoCeliaco]);
    const existente=cart.get(nuevaClave);
    if(existente) existente.cantidad=Math.min(99,existente.cantidad+item.cantidad);
    else cart.set(nuevaClave,item);
    renderCart();
  }
  function renderCart() {
    carrito.replaceChildren();let total=0, unidades=0;
    for (const [clave,item] of cart) {
      const unitario=precioFinal(item.producto,item.opciones),subtotal=unitario*item.cantidad;
      total += subtotal;unidades += item.cantidad;
      const fila=el('div',undefined,'pl-item');
      const info=el('div',undefined,'pl-item-info');info.append(el('strong',item.producto.nombre));
      if (detalles(item).length) info.append(el('small',detalles(item).join(' · '),'pl-item-opciones'));
      const alertaBtn=el('button',item.avisoCeliaco?'⚠️ Celíaco: sí':'⚠️ Marcar celíaco','pl-alergia-item');
      alertaBtn.type='button';alertaBtn.setAttribute('aria-pressed',String(!!item.avisoCeliaco));
      alertaBtn.title='Avisar a cocina solamente para este plato';
      alertaBtn.onclick=()=>marcarCeliaco(clave,item);
      info.append(alertaBtn);
      if (tieneAlertaCeliaco(item)) info.append(el('strong','⚠️ Revisar preparación sin gluten','pl-celiaco-chip'));
      info.append(el('small',`${money(unitario)} c/u · ${money(subtotal)}`));
      const ctr=el('div',undefined,'pl-controles');
      const menos=el('button','−'),cantidad=el('span',item.cantidad),mas=el('button','+'),quitar=el('button','✕');
      [menos,mas,quitar].forEach(b=>b.type='button');
      menos.onclick=()=>{if(item.cantidad===1)cart.delete(clave);else item.cantidad--;renderCart();};
      mas.onclick=()=>{if(item.cantidad<99)item.cantidad++;renderCart();};
      quitar.onclick=()=>{cart.delete(clave);renderCart();};
      ctr.append(menos,cantidad,mas);fila.append(info,ctr,quitar);carrito.append(fila);
    }
    if (!cart.size) carrito.append(el('p','Todavía no hay productos. Elegí uno del menú de la izquierda.','pl-empty-cart'));
    $('pl-contador').textContent=unidades+' '+(unidades===1?'unidad':'unidades');
    totalElemento.textContent=money(total);submit.disabled=busy||cart.size===0;
  }
  async function api(url,payload) {
    const response=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify(payload)});
    const data=await response.json();
    if (!response.ok || data.status!=='ok') throw new Error(data.mensaje||'No se pudo completar la operación.');
    return data;
  }
  async function loadHistory() {
    try {
      const response=await fetch(panel.dataset.listUrl,{credentials:'same-origin',cache:'no-store'});
      const data=await response.json();
      if (!response.ok || data.status!=='ok') throw new Error(data.mensaje||'No se pudo consultar pedidos.');
      productos=data.catalogo||[];
      renderCategorias();renderCatalogo();
      historial.replaceChildren();
      if (!data.pedidos.length) {historial.append(el('p','Todavía no hay pedidos.'));return;}
      data.pedidos.forEach(p=>{
        const card=el('article',undefined,'pl-pedido');
        card.append(el('h4',`#${p.id} · ${p.cliente}`),el('small',`${p.hora} · ${p.estado} · ${p.impreso?'Comanda impresa':'En cola de cocina'}`));
        if (p.aviso_celiaco) card.append(el('strong','⚠️ Contiene plato con aviso de celiaquía','pl-celiaco-chip'));
        if (p.notas) card.append(el('small',`Indicaciones: ${p.notas}`));
        card.append(el('div',money(Number(p.total))+(p.cobrado?` · ${p.pago}`:' · PENDIENTE'),'pl-pedido-total'));
        const actions=el('div',undefined,'pl-pedido-actions');
        if (!p.cobrado && p.estado!=='cancelado') {
          const select=el('select');
          [['efectivo','Efectivo'],['debito','Débito'],['mercadopago','Mercado Pago']].forEach(([value,name])=>{const opt=el('option',name);opt.value=value;select.append(opt);});
          const btn=el('button','Registrar cobro');btn.type='button';
          btn.onclick=async()=>{if(!confirm(`¿Registrar el cobro del pedido #${p.id} por ${select.options[select.selectedIndex].text}?`))return;
            btn.disabled=true;try{await api(panel.dataset.chargeTemplate.replace('999999',p.id),{pago:select.value});notify('Cobro registrado sin facturación automática.');await loadHistory();}
            catch(e){notify(e.message,true);btn.disabled=false;}};
          actions.append(select,btn);
        }
        if(p.estado==='preparacion'){
          const btn=el('button','✓ Listo');btn.type='button';
          btn.onclick=async()=>{btn.disabled=true;try{await api(panel.dataset.statusTemplate.replace('999999',p.id),{estado:'listo'});await loadHistory();}catch(e){notify(e.message,true);btn.disabled=false;}};
          actions.append(btn);
        }
        if(p.estado==='listo'&&p.cobrado&&p.impreso){
          const btn=el('button','Entregado');btn.type='button';
          btn.onclick=async()=>{btn.disabled=true;try{await api(panel.dataset.statusTemplate.replace('999999',p.id),{estado:'entregado'});await loadHistory();}catch(e){notify(e.message,true);btn.disabled=false;}};
          actions.append(btn);
        }
        card.append(actions);historial.append(card);
      });
    } catch(e) {historial.replaceChildren(el('p',e.message));catalogo.replaceChildren(el('p','No pudimos cargar el menú. Revisá la conexión.'));}
  }
  function open(){focoAnterior=document.activeElement;panel.hidden=false;panel.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';categoriaActual='Todas';$('pl-buscar').value='';cambiarVista('nuevo');catalogo.replaceChildren(el('p','Cargando menú…'));renderCart();loadHistory();}
  $('pl-tab-nuevo').addEventListener('click',()=>cambiarVista('nuevo'));
  $('pl-tab-historial').addEventListener('click',()=>{cambiarVista('historial');loadHistory();});
  function close(){panel.hidden=true;panel.setAttribute('aria-hidden','true');document.body.style.overflow='';cerrarConfigurador();focoAnterior?.focus?.();}
  abrir.addEventListener('click',open);
  panel.querySelectorAll('[data-pl-close]').forEach(b=>b.addEventListener('click',close));
  document.addEventListener('keydown',e=>{if(!panel.hidden&&e.key==='Escape'){if(!configurador.hidden)cerrarConfigurador();else close();}});
  pedidoCeliaco.addEventListener('change', renderCart);
  $('pl-buscar').addEventListener('input',renderCatalogo);
  $('pl-actualizar').addEventListener('click',loadHistory);
  $('pl-config-cancelar').addEventListener('click',cerrarConfigurador);
  $('pl-config-agregar').addEventListener('click',()=>{
    if(!elegido)return;
    const {seleccion,faltante}=opcionesElegidas();
    if(faltante)return notify('Elegí: '+faltante+' para '+elegido.nombre+'.',true);
    if(precioFinal(elegido,seleccion)<=0)return notify('El precio del producto no es válido.',true);
    agregarItem(elegido,seleccion,$('pl-aviso-celiaco').checked);
  });
  submit.addEventListener('click',async()=>{
    if(busy||!cart.size)return;
    busy=true;submit.disabled=true;notify('Guardando pedido y preparando comanda…');
    const data={solicitud_id:solicitud,cliente:$('pl-cliente').value,telefono:$('pl-telefono').value,
      notas:$('pl-notas').value,pago:$('pl-pago').value,
      items:[...cart.values()].map(i=>({producto_id:i.producto.id,cantidad:i.cantidad,
        opciones:i.opciones,aviso_celiaco:tieneAlertaCeliaco(i)}))};
    try {
      const result=await api(panel.dataset.createUrl,data);
      notify(`Pedido #${result.pedido_id} guardado. ${result.duplicado?'Sin duplicar.':'Enviado a la cola de cocina.'}`);
      cart.clear();$('pl-cliente').value='';$('pl-telefono').value='';$('pl-notas').value='';$('pl-pago').value='pendiente';pedidoCeliaco.checked=false;
      solicitud=nuevaSolicitud();renderCart();await loadHistory();cambiarVista('historial');
    } catch(e){notify(e.message+' Podés reintentar sin duplicar el pedido.',true);}
    finally{busy=false;renderCart();}
  });
  // Después de editar un producto en el panel, refrescamos nombres, opciones y precios desde DB.
  window.addEventListener('salon-catalogo-actualizado',()=>{if(!panel.hidden)loadHistory();});
})();
