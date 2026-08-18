// ==========================================================================
// MÓDULO 1: GESTIÓN DEL CARRITO DE COMPRAS Y SESIÓN
// ==========================================================================

function agregarAlCarrito(productoId) {
    const parametros = new URLSearchParams(window.location.search);
    const puesto = parametros.get('puesto') || '';

    fetch(`/carrito/agregar/${productoId}/?puesto=${puesto}`)
        .then(respuesta => respuesta.json())
        .then(datos => {
            if(datos.status === 'ok') {
                document.getElementById('badge-contador').innerText = datos.total_items;
                if (document.getElementById('carrito-sidebar').classList.contains('abierto')) {
                    cargarDetalleCarrito();
                }
            }
        });
}

function abrirCarrito() {
    document.getElementById('carrito-sidebar').classList.add('abierto');
    document.getElementById('carrito-overlay').classList.add('activo');
    cargarDetalleCarrito(); 
}

function cerrarCarrito() {
    document.getElementById('carrito-sidebar').classList.remove('abierto');
    document.getElementById('carrito-overlay').classList.remove('activo');
}

function cargarDetalleCarrito() {
    fetch('/carrito/ver/')
        .then(res => res.json())
        .then(datos => {
            const contenedor = document.getElementById('carrito-items');
            contenedor.innerHTML = ''; 
            
            if (datos.items.length === 0) {
                contenedor.innerHTML = '<p style="text-align:center; color:var(--texto-mutado); margin-top:20px;">Tu carrito está vacío.</p>';
                document.getElementById('carrito-precio-total').innerText = '0.00';
            } else {
                datos.items.forEach(item => {
                    contenedor.innerHTML += `
                        <div class="item-carrito">
                            <div class="item-info">
                                <h4>${item.nombre}</h4>
                                <div class="control-cantidad">
                                    <button type="button" class="btn-cantidad" onclick="restarItem('${item.llave}')">-</button>
                                    <span class="cantidad-numero">${item.cantidad}</span>
                                    <button type="button" class="btn-cantidad" onclick="sumarItem('${item.llave}')">+</button>
                                </div>
                            </div>
                            <div class="item-acciones">
                                <span class="item-precio">$${item.subtotal}</span>
                                <button type="button" class="btn-eliminar" onclick="eliminarItem('${item.llave}')">🗑️ Quitar</button>
                            </div>
                        </div>
                    `;
                });
                document.getElementById('carrito-precio-total').innerText = parseFloat(datos.total_general).toFixed(2);
            }
        });
}

function sumarItem(llave) {
    fetch(`/carrito/sumar/${llave}/`).then(res => res.json()).then(datos => {
        if(datos.status === 'ok') { document.getElementById('badge-contador').innerText = datos.total_items; cargarDetalleCarrito(); }
    });
}

function restarItem(llave) {
    fetch(`/carrito/restar/${llave}/`).then(res => res.json()).then(datos => {
        if(datos.status === 'ok') { document.getElementById('badge-contador').innerText = datos.total_items; cargarDetalleCarrito(); }
    });
}

function eliminarItem(llave) {
    fetch(`/carrito/eliminar/${llave}/`).then(res => res.json()).then(datos => {
        if(datos.status === 'ok') { document.getElementById('badge-contador').innerText = datos.total_items; cargarDetalleCarrito(); }
    });
}

function vaciarCarritoTotal() {
    Swal.fire({
        title: '¿Vaciar todo el pedido?',
        text: "Vas a eliminar todos los productos del carrito.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, vaciar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/carrito/limpiar/').then(res => res.json()).then(datos => {
                if(datos.status === 'ok') { 
                    document.getElementById('badge-contador').innerText = '0'; 
                    cargarDetalleCarrito(); 
                }
            });
        }
    });
}

// ==========================================================================
// MÓDULO 2: CHECKOUT Y PREPARACIÓN DEL MODAL DE ENTREGA
// ==========================================================================

function abrirModalEntrega() {
    const total = document.getElementById('carrito-precio-total').innerText;
    if (total === '0.00' || total === '0') { 
        Swal.fire({ icon: 'info', title: 'Carrito Vacío', text: 'Agregá algo rico antes de confirmar tu pedido.', confirmButtonColor: '#1e7b45' });
        return; 
    }

    cerrarCarrito(); 
    document.getElementById('modal-entrega').classList.add('activo');
    document.body.style.overflow = 'hidden'; 

    const parametros = new URLSearchParams(window.location.search);
    const puestoActual = parametros.get('puesto') || ''; 
    const labelMesa = document.getElementById('label-mesa');
    const radioMostrador = document.querySelector('input[name="tipo_entrega"][value="mostrador"]');

    const puestosSinMesa = ['kiosco', 'barra', 'parrilla', 'foodtruck'];
    if (puestosSinMesa.includes(puestoActual)) {
        labelMesa.style.display = 'none';
        radioMostrador.checked = true; 
        toggleFormularioMesa(); 
    } else { 
        labelMesa.style.display = 'block'; 
    }
}

function cerrarModalEntrega() {
    document.getElementById('modal-entrega').classList.remove('activo');
    document.body.style.overflow = 'auto'; 
}

function toggleFormularioMesa() {
    const opcionMesa = document.querySelector('input[name="tipo_entrega"]:checked');
    const formMesa = document.getElementById('form-mesa');
    const formTelefono = document.getElementById('form-telefono');
    
    // Verificamos si el radio de Efectivo está chequeado
    const pagoEfectivo = document.querySelector('input[name="tipo_pago"][value="efectivo"]');
    const esEfectivo = pagoEfectivo ? pagoEfectivo.checked : false;

    if (formTelefono) {
        if (esEfectivo) {
            formTelefono.classList.remove('oculto');
            formTelefono.style.display = 'flex';
        } else {
            formTelefono.classList.add('oculto');
            formTelefono.style.display = 'none';
        }
    }

    if (formMesa) {
        if (opcionMesa && opcionMesa.value === 'mesa') {
            formMesa.classList.remove('oculto');
            formMesa.style.display = 'flex';
        } else {
            formMesa.classList.add('oculto');
            formMesa.style.display = 'none';
        }
    }
}

// ==========================================================================
// MÓDULO 3: PROCESAMIENTO AJAX HACIA DJANGO Y MERCADO PAGO / NAVE / WA
// ==========================================================================

function validarYEnviar(event) {
    if (event) event.preventDefault();

    let nombreCliente = document.getElementById('nombre_cliente').value.trim();
    
    const telefonoInput = document.getElementById('telefono_cliente');
    const telefonoCliente = telefonoInput ? telefonoInput.value.trim() : ""; 
    
    const comentarios = document.getElementById('comentarios_pedido') ? document.getElementById('comentarios_pedido').value.trim() : "";
    const tipoEntregaElement = document.querySelector('input[name="tipo_entrega"]:checked');
    const tipoPagoElement = document.querySelector('input[name="tipo_pago"]:checked');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    if(!tipoEntregaElement || !tipoPagoElement) { 
        Swal.fire({ icon: 'warning', title: 'Faltan datos', text: 'Por favor completá opciones de entrega y pago.', confirmButtonColor: '#1e7b45' }); 
        return; 
    }
    
    const tipoEntrega = tipoEntregaElement.value;
    const tipoPago = tipoPagoElement.value;
    let numeroMesa = "";
    
    if (nombreCliente === "") { 
        Swal.fire({ icon: 'warning', title: 'Falta tu nombre', text: 'Escribí tu nombre y apellido para identificarte.', confirmButtonColor: '#1e7b45' }); 
        return; 
    }

    if (tipoPago === 'efectivo' && telefonoCliente === "") {
        Swal.fire({ icon: 'warning', title: 'Teléfono requerido', text: 'Por favor dejanos tu WhatsApp para coordinar el pago.', confirmButtonColor: '#1e7b45' }); 
        return; 
    }

    if (tipoEntrega === 'mesa') {
        numeroMesa = document.getElementById('numero_mesa').value.trim();
        if (numeroMesa === "") { 
            Swal.fire({ icon: 'warning', title: 'Número de Mesa', text: 'Ingresá el número de mesa donde estás.', confirmButtonColor: '#1e7b45' }); 
            return; 
        }
    }

    let comentariosFinales = comentarios;
    if (tipoEntrega === 'mesa') {
        const checkArmar = document.getElementById('armar_mesa');
        // 🔥 SIN EMOJI PARA QUE LA IMPRESORA NO PONGA "??" 🔥
        if (checkArmar && checkArmar.checked) {
            comentariosFinales = comentariosFinales ? comentariosFinales + " | FALTA ARMAR MESA" : "FALTA ARMAR MESA";
        }
    }
    
    if (comentariosFinales !== "") nombreCliente = `${nombreCliente} (Nota: ${comentariosFinales})`.substring(0, 99); 

    Swal.fire({
        title: 'Procesando...',
        text: '¡Llevando el pedido a toda velocidad!',
        imageUrl: '/static/img/corriendo.gif',
        imageWidth: 120,
        showConfirmButton: false,
        allowOutsideClick: false, 
        allowEscapeKey: false,
        background: 'var(--fondo)',
        color: 'var(--texto)'
    });

    const formData = new FormData();
    formData.append('nombre_cliente', nombreCliente);
    formData.append('telefono_cliente', telefonoCliente);
    formData.append('tipo_entrega', tipoEntrega);
    formData.append('numero_mesa', numeroMesa);
    formData.append('tipo_pago', tipoPago);

    fetch('/procesar/', { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken } })
    .then(res => res.json())
    .then(datos => {
        if (datos.status === 'ok') {
            cerrarModalEntrega();
            
            if (tipoPago === 'mercadopago') {
                if (datos.mp_id) window.location.href = `https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=${datos.mp_id}`;
                else Swal.fire({ icon: 'error', title: 'Error de cobro', text: 'El servidor no generó el link de Mercado Pago.' });
                
            } else if (tipoPago === 'nave') {
                if (datos.nave_url) {
                    window.location.href = datos.nave_url;
                } else {
                    Swal.fire({
                        title: '¡MODO / Nave!',
                        text: 'Estamos terminando de configurar la conexión con Nave. ¡Estará lista muy pronto!',
                        icon: 'info',
                        confirmButtonColor: '#103b70'
                    });
                }
            } else if (tipoPago === 'efectivo') {
                let fraseUbicacion = tipoEntrega === 'mesa' ? `ando en la mesa ${numeroMesa}` : `pedí para retirar en el mostrador`;
                let mensajeWa = `Hola soy ${document.getElementById('nombre_cliente').value.trim()}, ${fraseUbicacion}, mi número de pedido es #${datos.pedido_id} y lo quiero confirmar para acercarme a pagarlo o avísame si me cobras cuando el pedido llegue a la mesa.`;
                
                // ⚠️ ACORDATE DE CAMBIAR ESTE NÚMERO
                let numeroBuffet = "5491178246455"; 
                let linkWa = `https://wa.me/${numeroBuffet}?text=${encodeURIComponent(mensajeWa)}`;

                Swal.fire({
                    title: '¡Pedido Registrado!', 
                    text: 'Toca el botón para enviarnos un WhatsApp y confirmarnos tu pago.', 
                    icon: 'success',
                    confirmButtonText: 'Enviar WhatsApp 💬', 
                    confirmButtonColor: '#25D366', 
                    allowOutsideClick: false
                }).then(() => { 
                    window.open(linkWa, '_blank'); 
                    setTimeout(() => {
                        window.location.href = `/seguimiento/${datos.pedido_id}/`; 
                    }, 500);
                });
            } else {
                window.location.href = `/seguimiento/${datos.pedido_id}/`;
            }
        } else {
            Swal.fire({ icon: 'error', title: 'Oops...', text: "Error: " + datos.mensaje });
        }
    }).catch(error => { 
        Swal.fire({ icon: 'error', title: 'Error de red', text: 'No se pudo conectar con el servidor.' });
    });
}

// ==========================================================================
// MÓDULO 4: CREADOR DINÁMICO DE DISEÑO VISUAL (Acordeón, Radios y Checkboxes)
// ==========================================================================

function actualizarPrecioVisual(productoId) {
    const contenedor = document.querySelector(`.opciones-contenedor[data-id="${productoId}"]`);
    const tarjeta = contenedor.closest('.tarjeta-producto');
    const precioElement = tarjeta.querySelector('.precio');
    
    if (!precioElement.dataset.precioOriginal) {
        const precioBaseTexto = precioElement.innerText.replace('$', '').replace(',', '.');
        precioElement.dataset.precioOriginal = parseFloat(precioBaseTexto);
    }
    
    let precioActual = parseFloat(precioElement.dataset.precioOriginal);
    
    contenedor.querySelectorAll('input:checked').forEach(input => {
        const texto = input.value;
        if (texto.includes('(+')) {
            const extra = parseFloat(texto.split('(+')[1].split(')')[0]);
            if(!isNaN(extra)) precioActual += extra;
        }
        if (texto.includes('(-')) {
            const descuento = parseFloat(texto.split('(-')[1].split(')')[0]);
            if(!isNaN(descuento)) precioActual -= descuento;
        }
    });
    
    precioElement.innerText = '$' + precioActual.toFixed(2);
    
    precioElement.style.transition = 'all 0.3s ease';
    precioElement.style.transform = 'scale(1.15)';
    precioElement.style.color = 'var(--dorado-sanmartin)';
    
    setTimeout(() => {
        precioElement.style.transform = 'scale(1)';
        precioElement.style.color = ''; 
    }, 300);
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.opciones-contenedor').forEach(contenedor => {
        
        const atributos = [
            { nombre: 'Variante', valor: contenedor.dataset.variante, clave: 'variante', tipo: 'radio' },
            { nombre: 'Guarnición', valor: contenedor.dataset.guarnicion, clave: 'guarnicion', tipo: 'radio' },
            { nombre: 'Punto de cocción', valor: contenedor.dataset.punto, clave: 'punto', tipo: 'radio' },
            { nombre: 'Relleno', valor: contenedor.dataset.relleno, clave: 'relleno', tipo: 'radio' },
            { nombre: 'Salsa', valor: contenedor.dataset.salsa, clave: 'salsa', tipo: 'radio' },
            { nombre: 'Hielo', valor: contenedor.dataset.hielo, clave: 'hielo', tipo: 'radio' },
            { nombre: 'Adicional', valor: contenedor.dataset.adicional, clave: 'adicional', tipo: 'checkbox' } 
        ];

        let tieneOpciones = false;

        const wrapper = document.createElement('div');
        wrapper.className = 'opciones-wrapper';
        wrapper.style.display = 'none'; 
        wrapper.style.flexDirection = 'column';
        wrapper.style.gap = '8px';

        const tarjetaProducto = contenedor.closest('.tarjeta-producto');
        const nombreDelPlato = tarjetaProducto ? tarjetaProducto.querySelector('h3').innerText.toLowerCase() : '';
        const esPlatoDeHuevo = nombreDelPlato.includes('omel') || nombreDelPlato.includes('tortilla');

        atributos.forEach(attr => {
            if (attr.valor && attr.valor.trim() !== '') {
                tieneOpciones = true;
                
                const grupo = document.createElement('div');
                grupo.className = `opciones-grupo grupo-${attr.clave}-${contenedor.dataset.id}`;
                grupo.dataset.clave = attr.clave;
                grupo.dataset.requerido = (attr.tipo === 'radio') ? 'true' : 'false';

                const txtOpcional = (attr.tipo === 'checkbox') ? ' (Opcional)' : '';
                grupo.innerHTML = `<div class="opciones-titulo">Elegí ${attr.nombre}${txtOpcional}:</div>`;

                attr.valor.split(',').forEach((opcion) => {
                    const label = document.createElement('label');
                    label.className = 'opcion-item';
                    
                    const input = document.createElement('input');
                    input.type = attr.tipo;
                    input.value = opcion.trim();
                    
                    if (attr.tipo === 'radio') {
                        input.name = `radio-${attr.clave}-${contenedor.dataset.id}`;
                    } else {
                        input.className = `chk-adicional-${contenedor.dataset.id}`;
                    }

                    input.addEventListener('change', () => { 
                        grupo.classList.remove('error'); 
                        actualizarPrecioVisual(contenedor.dataset.id);
                    });

                    const marcador = document.createElement('div');
                    marcador.className = 'opcion-marcador';

                    label.appendChild(input);
                    label.appendChild(marcador);
                    label.appendChild(document.createTextNode(opcion.trim()));
                    
                    grupo.appendChild(label);
                });
                
                if (attr.clave === 'punto' && !esPlatoDeHuevo) {
                    const avisoParrilla = document.createElement('div');
                    avisoParrilla.style.fontSize = '0.8rem';
                    avisoParrilla.style.color = 'var(--dorado-sanmartin)';
                    avisoParrilla.style.fontWeight = 'bold';
                    avisoParrilla.style.marginTop = '4px';
                    avisoParrilla.innerHTML = '⏱️ La carne tiene una espera de 20 a 40 min según cocción.';
                    grupo.appendChild(avisoParrilla);
                }

                wrapper.appendChild(grupo); 
            }
        });

        if (tieneOpciones) {
            const btnToggle = document.createElement('button');
            btnToggle.type = 'button';
            btnToggle.className = 'btn-toggle-opciones';
            btnToggle.innerHTML = `Personalizar <span class="icono-toggle">▼</span>`;
            
            btnToggle.addEventListener('click', () => {
                if (wrapper.style.display === 'none') {
                    wrapper.style.display = 'flex';
                    btnToggle.innerHTML = `Ocultar <span class="icono-toggle">▲</span>`;
                    btnToggle.classList.add('abierto');
                } else {
                    wrapper.style.display = 'none';
                    btnToggle.innerHTML = `Personalizar <span class="icono-toggle">▼</span>`;
                    btnToggle.classList.remove('abierto');
                }
            });

            contenedor.appendChild(btnToggle);
            contenedor.appendChild(wrapper);
        }
    });
});

function agregarConOpciones(productoId) {
    const contenedor = document.querySelector(`.opciones-contenedor[data-id="${productoId}"]`);
    const parametrosActuales = new URLSearchParams(window.location.search);
    const puesto = parametrosActuales.get('puesto') || '';
    
    let fetchParams = new URLSearchParams();
    if (puesto) fetchParams.append('puesto', puesto);
    
    let faltanOpciones = false;
    let teniaPuntoDeCoccion = false;

    const tarjetaProducto = contenedor.closest('.tarjeta-producto');
    const nombreDelPlato = tarjetaProducto ? tarjetaProducto.querySelector('h3').innerText.toLowerCase() : '';
    const esPlatoDeHuevo = nombreDelPlato.includes('omel') || nombreDelPlato.includes('tortilla');

    contenedor.querySelectorAll('.opciones-grupo').forEach(grupo => {
        const clave = grupo.dataset.clave;
        const esRequerido = grupo.dataset.requerido === 'true';

        if (esRequerido) {
            const inputSeleccionado = grupo.querySelector(`input[type="radio"]:checked`);
            if (!inputSeleccionado) {
                grupo.classList.add('error'); 
                faltanOpciones = true;
            } else {
                fetchParams.append(clave, inputSeleccionado.value);
                if (clave === 'punto' && !esPlatoDeHuevo) teniaPuntoDeCoccion = true; 
            }
        } else if (clave === 'adicional') {
            let adicionalesElegidos = [];
            grupo.querySelectorAll('input[type="checkbox"]:checked').forEach(chk => {
                adicionalesElegidos.push(chk.value);
            });
            if (adicionalesElegidos.length > 0) {
                fetchParams.append('adicional', adicionalesElegidos.join(' + '));
            }
        }
    });

    if (faltanOpciones) { 
        const wrapper = contenedor.querySelector('.opciones-wrapper');
        const btnToggle = contenedor.querySelector('.btn-toggle-opciones');
        if (wrapper && wrapper.style.display === 'none') {
            wrapper.style.display = 'flex';
            if (btnToggle) {
                btnToggle.innerHTML = `Ocultar <span class="icono-toggle">▲</span>`;
                btnToggle.classList.add('abierto');
            }
        }
        
        Swal.fire({ 
            icon: 'error', 
            title: 'Falta seleccionar opciones', 
            text: 'Por favor, seleccioná las opciones marcadas en rojo.', 
            confirmButtonColor: '#1e7b45' 
        }); 
        return; 
    }

    const urlFinal = `/carrito/agregar/${productoId}/?${fetchParams.toString()}`;
    const boton = contenedor.nextElementSibling;
    const textoOriginal = boton.innerText;
    
    boton.innerText = "Cargando...";
    boton.disabled = true;
    
    fetch(urlFinal)
        .then(response => response.json())
        .then(data => {
            boton.disabled = false; 
            if (data.status === 'ok') {
                
                if (teniaPuntoDeCoccion) {
                    Swal.fire({
                        icon: 'info',
                        title: '¡Marchando a la Parrilla! 🥩',
                        text: 'Recordá que la carne tiene un tiempo de espera de 20 a 40 minutos según el punto de cocción elegido.',
                        confirmButtonColor: '#dfb23e',
                        timer: 5000
                    });
                }

                boton.innerText = "¡Agregado! ✔";
                boton.style.backgroundColor = "var(--verde-sanmartin)";
                
                contenedor.querySelectorAll('input').forEach(input => input.checked = false);
                actualizarPrecioVisual(productoId);
                
                const wrapper = contenedor.querySelector('.opciones-wrapper');
                const btnToggle = contenedor.querySelector('.btn-toggle-opciones');
                if (wrapper) wrapper.style.display = 'none';
                if (btnToggle) {
                    btnToggle.innerHTML = `Personalizar <span class="icono-toggle">▼</span>`;
                    btnToggle.classList.remove('abierto');
                }

                setTimeout(() => { boton.innerText = textoOriginal; boton.style.backgroundColor = ""; }, 1500);
                
                document.getElementById('badge-contador').innerText = data.total_items;
                if (document.getElementById('carrito-sidebar').classList.contains('abierto')) cargarDetalleCarrito();
            }
        }).catch(error => {
            boton.disabled = false;
            boton.innerText = textoOriginal;
        });
}

// ==========================================================================
// MÓDULO 5: DASHBOARD, PANEL DE CONTROL Y ADMINISTRACIÓN AJAX
// ==========================================================================

function abrirTab(tabId, btnElement) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    const tabSeleccionada = document.getElementById('tab-' + tabId);
    if(tabSeleccionada) tabSeleccionada.style.display = 'block';
    if(btnElement) btnElement.classList.add('active');
    else {
        const btnActivo = document.getElementById('btn-tab-' + tabId);
        if(btnActivo) btnActivo.classList.add('active');
    }
    localStorage.setItem('tabDashboardActiva', tabId);
}

document.addEventListener("DOMContentLoaded", function() {
    if(document.querySelector('.dash-tabs') || document.querySelector('.panel-tabs')) {
        let tabGuardada = localStorage.getItem('tabDashboardActiva') || 'pedidos';
        abrirTab(tabGuardada, document.getElementById('btn-tab-' + tabGuardada));
    }
});

function cambiarEstadoAjax(event, elemento, nuevoEstado, requiereConfirmacion=false) {
    event.preventDefault(); 
    
    if(requiereConfirmacion) {
        Swal.fire({
            title: '¿Seguro que querés cancelar?',
            text: "Esta acción no se puede deshacer.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, cancelar pedido'
        }).then((result) => {
            if (result.isConfirmed) { procesarCambioEstado(elemento, nuevoEstado); }
        });
    } else {
        procesarCambioEstado(elemento, nuevoEstado);
    }
}

function procesarCambioEstado(elemento, nuevoEstado) {
    const url = elemento.getAttribute('href');
    const textoOriginal = elemento.innerHTML;
    elemento.innerHTML = '⏳...';
    elemento.style.pointerEvents = 'none';

    fetch(url, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'ok') {
            const tr = elemento.closest('tr');
            tr.style.transition = "0.3s";
            const etiqueta = tr.querySelector('.badge-estado');
            const contenedorBotones = tr.querySelector('td:last-child div');
            
            if(nuevoEstado === 'cancelado') {
                tr.style.opacity = '0.5';
                if(etiqueta) { etiqueta.innerText = 'Cancelado'; etiqueta.style.background = 'var(--error, #dc3545)'; etiqueta.style.color = 'white'; }
                if(contenedorBotones) contenedorBotones.style.display = 'none'; 
            } else if (nuevoEstado === 'listo') {
                tr.style.borderLeft = '5px solid var(--verde-sanmartin, #28a745)';
                if(etiqueta) { etiqueta.innerText = '¡Listo!'; etiqueta.style.background = 'var(--verde-sanmartin, #28a745)'; etiqueta.style.color = 'white'; }
            } else if (nuevoEstado === 'entregado') {
                tr.style.opacity = '0.5';
                tr.style.borderLeft = '5px solid var(--texto-mutado, #6c757d)';
                if(etiqueta) { etiqueta.innerText = 'Entregado'; etiqueta.style.background = 'var(--texto-mutado, #6c757d)'; etiqueta.style.color = 'white'; }
                if(contenedorBotones) contenedorBotones.style.display = 'none'; 
            } else if (nuevoEstado === 'demorado') {
                if(etiqueta) { etiqueta.innerText = 'Demorado'; etiqueta.style.background = '#fd7e14'; etiqueta.style.color = 'white'; }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = 'auto';
            } else {
                if(etiqueta) { etiqueta.innerText = 'En Preparación'; etiqueta.style.background = 'var(--azul-sanmartin, #007bff)'; etiqueta.style.color = 'white'; }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = 'auto';
            }
        }
    }).catch(error => { 
        elemento.innerHTML = textoOriginal; 
        elemento.style.pointerEvents = 'auto'; 
        Swal.fire({ icon: 'error', title: 'Oops...', text: 'Hubo un error de conexión.' }); 
    });
}

function editarPrecioAjax(event, form) {
    event.preventDefault();
    const btn = form.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = '...';
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(() => { btn.innerText = 'OK'; btn.style.background = 'var(--verde-sanmartin)'; setTimeout(() => { btn.innerText = originalText; btn.style.background = ''; }, 1500); });
}

function cambiarDisponibilidadAjax(event, el) {
    event.preventDefault();
    fetch(el.href, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(res => res.json())
    .then(data => {
        const tr = el.closest('tr');
        tr.style.opacity = data.disponible ? '1' : '0.5';
        el.innerText = data.disponible ? 'Pausar' : 'Activar';
        el.className = data.disponible ? 'btn-panel btn-gris' : 'btn-panel btn-verde';
    });
}

function eliminarProductoAjax(event, el) {
    event.preventDefault();
    Swal.fire({
        title: '¿Borrar producto?',
        text: "Desaparecerá del menú permanentemente.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Borrar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(el.href, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
            .then(() => { const tr = el.closest('tr'); tr.style.transition = "0.3s"; tr.style.opacity = "0"; setTimeout(() => tr.remove(), 300); });
        }
    });
}

function ejecutarAjax(event, el) {
    event.preventDefault();
    fetch(el.href, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(response => response.json()) 
    .then(data => {
        const estaAbierto = data.esta_abierto; 
        el.innerText = estaAbierto ? "Cerrar" : "Abrir";
        el.classList.remove('btn-verde', 'btn-rojo');
        el.classList.add(estaAbierto ? 'btn-rojo' : 'btn-verde');
        const p = el.previousElementSibling;
        p.innerText = estaAbierto ? "🟢 ABIERTO" : "🔴 CERRADO";
        p.style.color = estaAbierto ? "var(--verde-sanmartin)" : "var(--error)";
    });
}

function filtrarPedidos(puestoSlug, btnActivo) {
    document.querySelectorAll('.filtros-mostrador button').forEach(btn => { btn.classList.remove('btn-azul', 'active'); btn.classList.add('btn-gris'); });
    btnActivo.classList.remove('btn-gris');
    btnActivo.classList.add('btn-azul', 'active');
    document.querySelectorAll('.fila-pedido').forEach(fila => { fila.style.display = (puestoSlug === 'todos' || fila.getAttribute('data-puesto') === puestoSlug) ? '' : 'none'; });
}

function actualizarPuestosAjax(event, form) {
    event.preventDefault(); 
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(() => { form.style.backgroundColor = "rgba(40, 167, 69, 0.1)"; setTimeout(() => form.style.backgroundColor = "transparent", 800); })
    .catch(error => Swal.fire({ icon: 'error', title: 'Oops...', text: 'Hubo un error al guardar los mostradores.' }));
}

let deferredPrompt;
let clicsIOS = parseInt(localStorage.getItem('clicsIOS')) || 0;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('btn-instalar-nav').style.display = 'block';
});

document.getElementById('btn-instalar-nav').addEventListener('click', async () => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt = null;
        document.getElementById('btn-instalar-nav').style.display = 'none';
    } 
    else if (isIOS) {
        clicsIOS++;
        localStorage.setItem('clicsIOS', clicsIOS);

        if (clicsIOS >= 1) {
            alert("Para tener el Buffet en tu inicio: Tocá el botón 'Compartir' (el cuadrado con la flecha) y elegí 'Agregar al inicio'.");
        } else {
            console.log("Intento de instalación iOS: " + clicsIOS);
        }
    }
});

window.addEventListener('appinstalled', () => {
    document.getElementById('btn-instalar-nav').style.display = 'none';
});

// ==========================================================================
// MÓDULO 6: CONTROL DE MODO OSCURO / CLARO
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', currentTheme);
    
    if(themeToggle) {
        themeToggle.checked = (currentTheme === 'dark');
        themeToggle.addEventListener('change', () => {
            const newTheme = themeToggle.checked ? 'dark' : 'light';
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
});

// ==========================================================================
// MÓDULO 7: CIERRE DE CAJA Y ESTADÍSTICAS POR MOSTRADOR
// ==========================================================================
function abrirCierreCaja() {
    fetch('/api/resumen-ventas/')
        .then(res => res.json())
        .then(data => {
            if(data.status === 'ok') {
                document.getElementById('gran-total-cierre').innerText = '$' + data.gran_total.toLocaleString('es-AR', {minimumFractionDigits: 2});
                
                let htmlMostradores = '';
                
                if(data.mostradores.length === 0) {
                    htmlMostradores = '<p style="text-align:center; color: var(--texto-mutado);">No hay ventas registradas en este turno.</p>';
                } else {
                    data.mostradores.forEach(m => {
                        // 1. Armar la lista de productos
                        let htmlProductos = '';
                        if(m.productos.length > 0) {
                            m.productos.forEach(p => {
                                htmlProductos += `
                                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px; border-bottom: 1px dashed var(--borde); padding-bottom: 4px; color: var(--text-color);">
                                    <span>${p.nombre}</span> <strong>x${p.cantidad}</strong>
                                </div>`;
                            });
                        } else {
                            htmlProductos = '<span style="color: var(--texto-mutado); font-size: 0.85rem;">Sin productos vendidos.</span>';
                        }

                        // 2. Armar el cajón de este mostrador
                        htmlMostradores += `
                        <details class="panel-accordion" style="margin-bottom: 12px; border: 1px solid var(--borde); background: var(--bg-color); border-radius: 8px;">
                            <summary style="padding: 12px 15px; font-size: 1.05rem; border-left: 4px solid var(--dorado-sanmartin); background: transparent; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center; padding-right: 10px;">
                                    <span style="font-weight: 800;">🏪 ${m.nombre}</span>
                                    <strong style="color: var(--verde-sanmartin);">$${m.total_ventas.toLocaleString('es-AR')}</strong>
                                </div>
                            </summary>
                            <div style="padding: 15px; border-top: 1px solid var(--borde);">
                                
                                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                                    <div style="flex: 1; text-align: center; background: var(--card-bg); padding: 10px; border-radius: 8px; border: 1px solid var(--borde);">
                                        <small style="color: var(--texto-mutado); display: block; font-size: 0.75rem; text-transform: uppercase;">Pedidos</small>
                                        <strong style="color: var(--text-color); font-size: 1.3rem;">${m.cantidad_pedidos}</strong>
                                    </div>
                                    <div style="flex: 1.5; background: var(--card-bg); padding: 10px; border-radius: 8px; border: 1px solid var(--borde); font-size: 0.85rem;">
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>💵 Efectivo:</span> <strong>$${m.efectivo.toLocaleString('es-AR')}</strong></div>
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>📱 MP:</span> <strong>$${m.mercadopago.toLocaleString('es-AR')}</strong></div>
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>🚀 Nave:</span> <strong>$${m.nave.toLocaleString('es-AR')}</strong></div>
                                    </div>
                                </div>
                                
                                <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 0.95rem; color: var(--text-color); border-bottom: 1px solid var(--borde); padding-bottom: 5px;">🍔 Desglose de Productos</h4>
                                ${htmlProductos}
                            </div>
                        </details>
                        `;
                    });
                }
                
                document.getElementById('contenedor-mostradores').innerHTML = htmlMostradores;
                document.getElementById('modalCierre').classList.add('activo');
            }
        })
        .catch(error => console.error("Error al obtener cierre:", error));
}

function cerrarCierreCaja() {
    document.getElementById('modalCierre').classList.remove('activo');
}

function confirmarCierreYLimpiar() {
    Swal.fire({
        title: '¿Seguro que querés cerrar el turno?',
        text: "Esto va a borrar todos los pedidos del panel para arrancar de cero mañana.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: 'var(--error)',
        cancelButtonColor: 'var(--texto-mutado)',
        confirmButtonText: 'Sí, Cerrar Turno',
        cancelButtonText: 'Cancelar',
        background: 'var(--card-bg)',
        color: 'var(--text-color)'
    }).then((result) => {
        if (result.isConfirmed) {
            // Como esto está en un .js externo, usamos la URL directa en vez del tag de Django
            window.location.href = "/dashboard/eliminar-todo/";
        }
    });
}