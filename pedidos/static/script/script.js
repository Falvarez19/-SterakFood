// ==========================================================================
// MÓDULO 0: PANTALLA DE CARGA Y PORCENTAJE
// ==========================================================================
document.addEventListener("DOMContentLoaded", function() {
    const porcentajeEl = document.getElementById('carga-porcentaje');
    if (porcentajeEl) {
        let progreso = 0;
        
        // El porcentaje sube aleatoriamente para simular carga real
        const intervalo = setInterval(() => {
            if (progreso < 90) {
                progreso += Math.floor(Math.random() * 15) + 5;
                if (progreso > 90) progreso = 90;
                porcentajeEl.textContent = progreso + '%';
            }
        }, 80);

        // Cuando la web carga al 100%, termina de subir y oculta la pantalla
        window.addEventListener('load', function() {
            clearInterval(intervalo);
            porcentajeEl.textContent = '100%'; 
            
            setTimeout(() => {
                const preloader = document.getElementById('pantalla-carga');
                if (preloader) {
                    preloader.style.opacity = '0';
                    preloader.style.visibility = 'hidden';
                    document.body.classList.remove('bloquear-scroll');
                    
                    setTimeout(() => preloader.remove(), 600);
                }
            }, 300); 
        });
    }
});

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
        
        document.querySelectorAll('input[name="tipo_entrega"]').forEach(r => r.checked = false);
        document.querySelectorAll('input[name="tipo_pago"]').forEach(r => r.checked = false);
        toggleFormularioMesa();
    }
}

function cerrarModalEntrega() {
    document.getElementById('modal-entrega').classList.remove('activo');
    document.body.style.overflow = 'auto'; 
}

function toggleFormularioMesa() {
    const opcionEntrega = document.querySelector('input[name="tipo_entrega"]:checked');
    const formMesa = document.getElementById('form-mesa');
    const seccionPago = document.getElementById('seccion-pago');
    
    const opcionPago = document.querySelector('input[name="tipo_pago"]:checked');
    const formTelefono = document.getElementById('form-telefono');
    
    if (seccionPago) {
        if (opcionEntrega) {
            seccionPago.classList.remove('oculto');
        } else {
            seccionPago.classList.add('oculto');
        }
    }

    if (formMesa) {
        if (opcionEntrega && opcionEntrega.value === 'mesa') {
            formMesa.classList.remove('oculto');
            formMesa.style.display = 'flex';
        } else {
            formMesa.classList.add('oculto');
            formMesa.style.display = 'none';
        }
    }

    if (formTelefono) {
        if (opcionPago && opcionPago.value === 'efectivo') {
            formTelefono.classList.remove('oculto');
            formTelefono.style.display = 'flex';
        } else {
            formTelefono.classList.add('oculto');
            formTelefono.style.display = 'none';
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
        Swal.fire({ icon: 'warning', title: 'Faltan datos', text: 'Por favor completá opciones de entrega y pago.', confirmButtonColor: '#ff6600' }); 
        return; 
    }
    
    const tipoEntrega = tipoEntregaElement.value;
    const tipoPago = tipoPagoElement.value;
    let numeroMesa = "";
    
    if (nombreCliente === "") { 
        Swal.fire({ icon: 'warning', title: 'Falta tu nombre', text: 'Escribí tu nombre y apellido para identificarte.', confirmButtonColor: '#ff6600' }); 
        return; 
    }

    if (tipoPago === 'efectivo' && telefonoCliente === "") {
        Swal.fire({ icon: 'warning', title: 'Teléfono requerido', text: 'Por favor dejanos tu WhatsApp para coordinar el pago.', confirmButtonColor: '#ff6600' }); 
        return; 
    }

    if (tipoEntrega === 'mesa') {
        numeroMesa = document.getElementById('numero_mesa').value.trim();
        if (numeroMesa === "") { 
            Swal.fire({ icon: 'warning', title: 'Número de Mesa', text: 'Ingresá el número de mesa donde estás.', confirmButtonColor: '#ff6600' }); 
            return; 
        }
    }

    let comentariosFinales = comentarios;
    if (tipoEntrega === 'mesa') {
        const checkArmar = document.getElementById('armar_mesa');
        if (checkArmar && checkArmar.checked) {
            comentariosFinales = comentariosFinales ? comentariosFinales + " | FALTA ARMAR MESA" : "FALTA ARMAR MESA";
        }
    }
    
    if (comentariosFinales !== "") nombreCliente = `${nombreCliente} (Nota: ${comentariosFinales})`.substring(0, 99); 

    // Alerta de carga limpia sin el Wok
    Swal.fire({
        title: 'Procesando...',
        text: '¡Llevando el pedido a toda velocidad!',
        showConfirmButton: false,
        allowOutsideClick: false, 
        allowEscapeKey: false,
        background: 'var(--card-bg)',
        color: 'var(--text-color)',
        didOpen: () => {
            Swal.showLoading();
        },
        customClass: {
            popup: 'alerta-con-marco'
        }
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
                        confirmButtonColor: '#ff6600'
                    });
                }
            } else if (tipoPago === 'efectivo') {
                let fraseUbicacion = tipoEntrega === 'mesa' ? `ando en la mesa ${numeroMesa}` : `pedí para retirar en el mostrador`;
                let mensajeWa = `Hola soy ${document.getElementById('nombre_cliente').value.trim()}, ${fraseUbicacion}, mi número de pedido es #${datos.pedido_id} y lo quiero confirmar para acercarme a pagarlo o avísame si me cobras cuando el pedido llegue a la mesa.`;
                
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
    precioElement.style.color = 'var(--naranja-sterak)';
    
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
                    avisoParrilla.style.color = 'var(--naranja-brillo)';
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
            confirmButtonColor: '#ff6600' 
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
                        confirmButtonColor: '#ff6600',
                        timer: 5000
                    });
                }

                boton.innerText = "¡Agregado! ✔";
                boton.style.backgroundColor = "var(--naranja-sterak)";
                boton.style.color = "#000";
                
                contenedor.querySelectorAll('input').forEach(input => input.checked = false);
                actualizarPrecioVisual(productoId);
                
                const wrapper = contenedor.querySelector('.opciones-wrapper');
                const btnToggle = contenedor.querySelector('.btn-toggle-opciones');
                if (wrapper) wrapper.style.display = 'none';
                if (btnToggle) {
                    btnToggle.innerHTML = `Personalizar <span class="icono-toggle">▼</span>`;
                    btnToggle.classList.remove('abierto');
                }

                setTimeout(() => { 
                    boton.innerText = textoOriginal; 
                    boton.style.backgroundColor = ""; 
                    boton.style.color = ""; 
                }, 1500);
                
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
                if(etiqueta) { etiqueta.innerText = 'Cancelado'; etiqueta.style.background = 'var(--error)'; etiqueta.style.color = 'white'; }
                if(contenedorBotones) contenedorBotones.style.display = 'none'; 
            } else if (nuevoEstado === 'listo') {
                tr.style.borderLeft = '5px solid #10b981';
                if(etiqueta) { etiqueta.innerText = '¡Listo!'; etiqueta.style.background = '#10b981'; etiqueta.style.color = 'white'; }
            } else if (nuevoEstado === 'entregado') {
                tr.style.opacity = '0.5';
                tr.style.borderLeft = '5px solid var(--texto-mutado)';
                if(etiqueta) { etiqueta.innerText = 'Entregado'; etiqueta.style.background = 'var(--texto-mutado)'; etiqueta.style.color = 'white'; }
                if(contenedorBotones) contenedorBotones.style.display = 'none'; 
            } else if (nuevoEstado === 'demorado') {
                if(etiqueta) { etiqueta.innerText = 'Demorado'; etiqueta.style.background = '#fd7e14'; etiqueta.style.color = 'white'; }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = 'auto';
            } else {
                if(etiqueta) { etiqueta.innerText = 'En Preparación'; etiqueta.style.background = 'var(--naranja-sterak)'; etiqueta.style.color = '#000'; }
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
    .then(() => { btn.innerText = 'OK'; btn.style.background = '#10b981'; setTimeout(() => { btn.innerText = originalText; btn.style.background = ''; }, 1500); });
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
        p.style.color = estaAbierto ? "var(--naranja-sterak)" : "var(--error)";
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
    .then(() => { form.style.backgroundColor = "rgba(255, 102, 0, 0.1)"; setTimeout(() => form.style.backgroundColor = "transparent", 800); })
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
// MÓDULO 6: CONTROL DE MODO OSCURO / CLARO Y CAMBIOS DE LOGO
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', currentTheme);
    
    // 1. Seleccionamos las imágenes del logo
    const navLogo = document.querySelector('.nav-logo');
    const heroLogo = document.querySelector('.hero-logo-side img');

    // 2. Función para cambiar la imagen según el tema
    const actualizarLogos = (tema) => {
        const rutaLogo = tema === 'light' ? '/static/img/logo_2.png' : '/static/img/logo.png';
        
        if (navLogo) navLogo.src = rutaLogo;
        if (heroLogo) {
            heroLogo.src = rutaLogo;
            // Suavizamos la sombra en el banner si es de día
            heroLogo.style.filter = tema === 'light' 
                ? 'drop-shadow(0px 4px 8px rgba(0,0,0,0.2))' 
                : 'drop-shadow(0px 4px 8px rgba(0,0,0,0.8))';
        }
    };

    // 3. Aplicamos el logo apenas carga la página
    actualizarLogos(currentTheme);
    
    if(themeToggle) {
        themeToggle.checked = (currentTheme === 'dark');
        themeToggle.addEventListener('change', () => {
            const newTheme = themeToggle.checked ? 'dark' : 'light';
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Cambiamos el logo dinámicamente al tocar el botón
            actualizarLogos(newTheme);
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

                        htmlMostradores += `
                        <details class="panel-accordion" style="margin-bottom: 12px; border: 1px solid var(--borde); background: var(--bg-color); border-radius: 8px;">
                            <summary style="padding: 12px 15px; font-size: 1.05rem; border-left: 4px solid var(--naranja-sterak); background: transparent; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center; padding-right: 10px;">
                                    <span style="font-weight: 800;">🏪 ${m.nombre}</span>
                                    <strong style="color: var(--naranja-sterak);">$${m.total_ventas.toLocaleString('es-AR')}</strong>
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
            window.location.href = "/dashboard/eliminar-todo/";
        }
    });
}
// ==========================================================================
// MÓDULO 8: RECUPERAR ESTADO DEL CARRITO AL RECARGAR LA PÁGINA
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    const badgeContador = document.getElementById('badge-contador');
    
    if (badgeContador) {
        fetch('/carrito/ver/')
            .then(res => res.json())
            .then(datos => {
                let totalItems = 0;
                if (datos.items && datos.items.length > 0) {
                    datos.items.forEach(item => {
                        totalItems += item.cantidad;
                    });
                }
                badgeContador.innerText = totalItems;
            })
            .catch(err => console.log("Error al recuperar el carrito:", err));
    }
});

// ==========================================================================
// MÓDULO 9: POS DE SALÓN - VERSIÓN FINAL + COMANDA FLOTANTE
// ==========================================================================
(function () {

    'use strict';


    var root =
        document.getElementById(
            'salon-pos'
        );


    if (!root) {
        return;
    }


    // ======================================================================
    // PRODUCTOS
    // ======================================================================

    var productosData =
        document.getElementById(
            'salon-productos-data'
        );


    var productos = [];


    try {

        productos =
            JSON.parse(
                productosData
                    ? productosData.textContent
                    : '[]'
            );

    } catch (error) {

        console.error(
            'No se pudieron leer los productos:',
            error
        );

        productos = [];

    }


    productos =
        productos.map(
            function (producto) {

                return {

                    id:
                        Number(
                            producto.id || 0
                        ),

                    codigo:
                        String(
                            producto.codigo
                            ||
                            producto.id
                            ||
                            ''
                        ),

                    nombre:
                        String(
                            producto.nombre
                            ||
                            'Producto'
                        ),

                    precio:
                        Number(
                            producto.precio
                            ||
                            0
                        )

                };

            }
        );


    // ======================================================================
    // STORAGE
    // ======================================================================

    var STORAGE_KEY =
        'sterakfood_salon_cuentas_v3';


    var STORAGE_ANTERIORES = [

        'sterakfood_salon_cuentas_v2',

        'sterakfood_salon_cuentas_v1',

        'shortyfood_pos_salon_v2'

    ];


    var MESA_ACTUAL_KEY =
        'sterakfood_salon_mesa_actual_v1';


    var cuentas =
        cargarCuentas();


    var mesaActual = null;

    var sugerencias = [];

    var sugerenciaActiva = -1;

    var enviando = false;


    // ======================================================================
    // DOM
    // ======================================================================

    var botonesMesa =
        Array.prototype.slice.call(
            document.querySelectorAll(
                '.salon-pos__mesa'
            )
        );


    var tituloMesa =
        document.getElementById(
            'titulo-mesa'
        );


    var estadoMesa =
        document.getElementById(
            'estado-mesa'
        );


    var mensajeSeleccionar =
        document.getElementById(
            'mensaje-seleccionar-mesa'
        );


    var areaComanda =
        document.getElementById(
            'area-comanda'
        );


    var inputCant =
        document.getElementById(
            'input-cant'
        );


    var buscador =
        document.getElementById(
            'buscador'
        );


    var listaSugerencias =
        document.getElementById(
            'lista-sugerencias'
        );


    var listaComanda =
        document.getElementById(
            'lista-comanda'
        );


    var totalCuenta =
        document.getElementById(
            'total-cuenta'
        );


    var cantidadLineas =
        document.getElementById(
            'cantidad-lineas'
        );


    var resumenAccion =
        document.getElementById(
            'resumen-accion'
        );


    var totalSeleccionado =
        document.getElementById(
            'total-seleccionado'
        );


    var btnAccion =
        document.getElementById(
            'btn-accion-principal'
        );


    var btnTicket =
        document.getElementById(
            'btn-imprimir-mesa'
        );


    var modalComanda =
        document.querySelector(
            '.salon-pos__comanda-panel'
        );


    var modalOverlay =
        document.getElementById(
            'salon-modal-overlay'
        );


    var btnCerrarComanda =
        document.getElementById(
            'btn-cerrar-comanda'
        );


    // ======================================================================
    // STORAGE
    // ======================================================================

    function cargarCuentas() {

        var claves =
            [
                STORAGE_KEY
            ].concat(
                STORAGE_ANTERIORES
            );


        for (
            var i = 0;
            i < claves.length;
            i++
        ) {

            try {

                var guardado =
                    localStorage.getItem(
                        claves[i]
                    );


                if (!guardado) {
                    continue;
                }


                var datos =
                    JSON.parse(
                        guardado
                    );


                if (
                    datos
                    &&
                    typeof datos === 'object'
                ) {

                    if (
                        claves[i]
                        !==
                        STORAGE_KEY
                    ) {

                        localStorage.setItem(
                            STORAGE_KEY,
                            JSON.stringify(
                                datos
                            )
                        );

                    }


                    return datos;

                }

            } catch (error) {

                console.warn(
                    'No se pudo recuperar el salón:',
                    error
                );

            }

        }


        return {};

    }


    function guardar() {

        try {

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(
                    cuentas
                )
            );


            if (mesaActual) {

                localStorage.setItem(
                    MESA_ACTUAL_KEY,
                    String(
                        mesaActual
                    )
                );

            }

        } catch (error) {

            console.error(
                'No se pudo guardar el salón:',
                error
            );

        }

    }


    // ======================================================================
    // CUENTA
    // ======================================================================

    function normalizarCuenta(
        numeroMesa
    ) {

        var clave =
            String(
                numeroMesa
            );


        if (
            !cuentas[
                clave
            ]
            ||
            !Array.isArray(
                cuentas[
                    clave
                ].items
            )
        ) {

            cuentas[
                clave
            ] = {

                items: [],

                total: 0

            };

        }


        cuentas[
            clave
        ].items =
            cuentas[
                clave
            ].items.filter(
                function (item) {

                    return (
                        item
                        &&
                        Number(
                            item.cantidad
                            ||
                            0
                        )
                        >
                        0
                    );

                }
            ).map(
                function (item) {

                    var cantidad =
                        Number(
                            item.cantidad
                            ||
                            1
                        );


                    if (
                        cantidad
                        <
                        1
                    ) {

                        cantidad =
                            1;

                    }


                    var cantPagar =
                        Number(
                            item.cant_pagar
                            ||
                            cantidad
                        );


                    if (
                        cantPagar
                        <
                        1
                    ) {

                        cantPagar =
                            1;

                    }


                    if (
                        cantPagar
                        >
                        cantidad
                    ) {

                        cantPagar =
                            cantidad;

                    }


                    return {

                        producto_id:
                            Number(
                                item.producto_id
                                ||
                                item.id
                                ||
                                0
                            ),

                        codigo:
                            String(
                                item.codigo
                                ||
                                ''
                            ),

                        nombre:
                            String(
                                item.nombre
                                ||
                                'Producto'
                            ),

                        precio:
                            Number(
                                item.precio
                                ||
                                0
                            ),

                        cantidad:
                            cantidad,

                        seleccionado:
                            Boolean(
                                item.seleccionado
                            ),

                        cant_pagar:
                            cantPagar

                    };

                }
            );


        recalcular(
            cuentas[
                clave
            ]
        );


        return cuentas[
            clave
        ];

    }


    function cuentaActual() {

        if (!mesaActual) {
            return null;
        }


        return normalizarCuenta(
            mesaActual
        );

    }


    function recalcular(
        cuenta
    ) {

        cuenta.total =
            cuenta.items.reduce(
                function (
                    total,
                    item
                ) {

                    return (
                        total
                        +
                        (
                            Number(
                                item.precio
                                ||
                                0
                            )
                            *
                            Number(
                                item.cantidad
                                ||
                                0
                            )
                        )
                    );

                },
                0
            );

    }


    // ======================================================================
    // FORMATO
    // ======================================================================

    function dinero(
        valor
    ) {

        return (
            '$'
            +
            Number(
                valor
                ||
                0
            ).toLocaleString(
                'es-AR',
                {

                    minimumFractionDigits:
                        0,

                    maximumFractionDigits:
                        2

                }
            )
        );

    }


    function escapar(
        valor
    ) {

        return String(
            valor
            ||
            ''
        )
        .replace(
            /&/g,
            '&amp;'
        )
        .replace(
            /</g,
            '&lt;'
        )
        .replace(
            />/g,
            '&gt;'
        )
        .replace(
            /"/g,
            '&quot;'
        )
        .replace(
            /'/g,
            '&#039;'
        );

    }


    // ======================================================================
    // VENTANA FLOTANTE DE LA COMANDA
    // ======================================================================

    function abrirComanda() {

        if (
            modalComanda
        ) {

            modalComanda.classList.add(
                'is-open'
            );

        }


        if (
            modalOverlay
        ) {

            modalOverlay.classList.add(
                'is-open'
            );

        }


        document.body.style.overflow =
            'hidden';

    }


    function cerrarComanda() {

        if (
            modalComanda
        ) {

            modalComanda.classList.remove(
                'is-open'
            );

        }


        if (
            modalOverlay
        ) {

            modalOverlay.classList.remove(
                'is-open'
            );

        }


        document.body.style.overflow =
            '';

    }


    // ======================================================================
    // MESAS
    // ======================================================================

    function seleccionarMesa(
        numero
    ) {

        guardar();


        mesaActual =
            String(
                numero
            );


        normalizarCuenta(
            mesaActual
        );


        tituloMesa.textContent =
            'Mesa '
            +
            mesaActual;


        estadoMesa.textContent =
            'MESA '
            +
            mesaActual;


        mensajeSeleccionar.hidden =
            true;


        mensajeSeleccionar.classList.add(
            'is-hidden'
        );


        areaComanda.hidden =
            false;


        abrirComanda();


        actualizarMesas();

        render();

        guardar();


        window.setTimeout(
            function () {

                buscador.focus();

            },
            60
        );

    }


    function actualizarMesas() {

        botonesMesa.forEach(
            function (
                boton
            ) {

                var numero =
                    String(
                        boton.getAttribute(
                            'data-mesa'
                        )
                    );


                var cuenta =
                    cuentas[
                        numero
                    ];


                var items = [];


                if (
                    cuenta
                    &&
                    Array.isArray(
                        cuenta.items
                    )
                ) {

                    items =
                        cuenta.items.filter(
                            function (item) {

                                return (
                                    item
                                    &&
                                    Number(
                                        item.cantidad
                                        ||
                                        0
                                    )
                                    >
                                    0
                                );

                            }
                        );

                }


                var ocupada =
                    items.length
                    >
                    0;


                var unidades =
                    0;


                var total =
                    0;


                items.forEach(
                    function (item) {

                        var cantidad =
                            Number(
                                item.cantidad
                                ||
                                0
                            );


                        var precio =
                            Number(
                                item.precio
                                ||
                                0
                            );


                        unidades +=
                            cantidad;


                        total +=
                            precio
                            *
                            cantidad;

                    }
                );


                var seleccionada =
                    numero
                    ===
                    String(
                        mesaActual
                        ||
                        ''
                    );


                boton.classList.toggle(
                    'mesa-ocupada',
                    ocupada
                );


                boton.classList.toggle(
                    'is-ocupada',
                    ocupada
                );


                boton.classList.toggle(
                    'mesa-seleccionada',
                    seleccionada
                );


                boton.classList.toggle(
                    'is-actual',
                    seleccionada
                );


                if (
                    ocupada
                ) {

                    boton.innerHTML =
                        '<span class="salon-pos__mesa-numero">'
                        +
                        escapar(
                            numero
                        )
                        +
                        '</span>'
                        +
                        '<span class="salon-pos__mesa-items">'
                        +
                        unidades
                        +
                        (
                            unidades
                            ===
                            1
                                ? ' unidad'
                                : ' unidades'
                        )
                        +
                        '</span>'
                        +
                        '<strong class="salon-pos__mesa-total">'
                        +
                        dinero(
                            total
                        )
                        +
                        '</strong>';

                } else {

                    boton.innerHTML =
                        '<span class="salon-pos__mesa-numero">'
                        +
                        escapar(
                            numero
                        )
                        +
                        '</span>'
                        +
                        '<span class="salon-pos__mesa-libre">'
                        +
                        'Libre'
                        +
                        '</span>';

                }

            }
        );

    }


    // ======================================================================
    // AGREGAR PRODUCTO
    // ======================================================================

    function agregarProducto(
        producto
    ) {

        var cuenta =
            cuentaActual();


        if (!cuenta) {
            return;
        }


        var cantidad =
            parseInt(
                inputCant.value,
                10
            );


        if (
            !cantidad
            ||
            cantidad
            <
            1
        ) {

            cantidad =
                1;

        }


        var existente =
            cuenta.items.find(
                function (item) {

                    if (
                        producto.id
                        &&
                        item.producto_id
                    ) {

                        return (
                            Number(
                                producto.id
                            )
                            ===
                            Number(
                                item.producto_id
                            )
                        );

                    }


                    return (
                        String(
                            producto.codigo
                        )
                        ===
                        String(
                            item.codigo
                        )
                    );

                }
            );


        if (existente) {

            existente.cantidad +=
                cantidad;


            if (
                existente.seleccionado
            ) {

                existente.cant_pagar =
                    existente.cantidad;

            }

        } else {

            cuenta.items.push({

                producto_id:
                    producto.id,

                codigo:
                    producto.codigo,

                nombre:
                    producto.nombre,

                precio:
                    producto.precio,

                cantidad:
                    cantidad,

                seleccionado:
                    false,

                cant_pagar:
                    cantidad

            });

        }


        recalcular(
            cuenta
        );


        guardar();

        actualizarMesas();

        render();


        inputCant.value =
            1;


        buscador.value =
            '';


        cerrarSugerencias();

        buscador.focus();

    }


    // ======================================================================
    // BUSCADOR
    // ======================================================================

    function buscarProductos(
        texto
    ) {

        texto =
            String(
                texto
                ||
                ''
            )
            .trim()
            .toLowerCase();


        if (!texto) {
            return [];
        }


        var exactos = [];

        var otros = [];


        productos.forEach(
            function (
                producto
            ) {

                var codigo =
                    String(
                        producto.codigo
                    ).toLowerCase();


                var nombre =
                    String(
                        producto.nombre
                    ).toLowerCase();


                if (
                    codigo
                    ===
                    texto
                ) {

                    exactos.unshift(
                        producto
                    );

                    return;

                }


                if (
                    codigo.indexOf(
                        texto
                    )
                    ===
                    0
                ) {

                    exactos.push(
                        producto
                    );

                    return;

                }


                if (
                    codigo.indexOf(
                        texto
                    )
                    !==
                    -1
                    ||
                    nombre.indexOf(
                        texto
                    )
                    !==
                    -1
                ) {

                    otros.push(
                        producto
                    );

                }

            }
        );


        return exactos.concat(
            otros
        ).slice(
            0,
            8
        );

    }


    function cerrarSugerencias() {

        sugerencias = [];

        sugerenciaActiva =
            -1;


        listaSugerencias.innerHTML =
            '';


        listaSugerencias.classList.remove(
            'is-visible'
        );

    }


    function pintarSugerencias() {

        if (
            !sugerencias.length
        ) {

            cerrarSugerencias();

            return;

        }


        var html =
            '';


        sugerencias.forEach(
            function (
                producto,
                index
            ) {

                var clase =
                    index
                    ===
                    sugerenciaActiva
                        ? ' is-activa'
                        : '';


                html +=
                    '<li class="salon-pos__sugerencia'
                    +
                    clase
                    +
                    '" data-index="'
                    +
                    index
                    +
                    '">'
                    +
                        '<div class="salon-pos__sugerencia-main">'
                        +
                            '<strong>'
                            +
                            escapar(
                                producto.nombre
                            )
                            +
                            '</strong>'
                            +
                            '<span>Cód. '
                            +
                            escapar(
                                producto.codigo
                            )
                            +
                            '</span>'
                        +
                        '</div>'
                        +
                        '<b>'
                        +
                        dinero(
                            producto.precio
                        )
                        +
                        '</b>'
                    +
                    '</li>';

            }
        );


        listaSugerencias.innerHTML =
            html;


        listaSugerencias.classList.add(
            'is-visible'
        );

    }


    // ======================================================================
    // SELECCIÓN
    // ======================================================================

    function resumenSeleccion(
        cuenta
    ) {

        var cantidad =
            0;


        var total =
            0;


        cuenta.items.forEach(
            function (item) {

                if (
                    !item.seleccionado
                ) {

                    return;

                }


                var cant =
                    Number(
                        item.cant_pagar
                        ||
                        item.cantidad
                    );


                if (
                    cant
                    <
                    1
                ) {

                    cant =
                        1;

                }


                if (
                    cant
                    >
                    item.cantidad
                ) {

                    cant =
                        item.cantidad;

                }


                cantidad +=
                    cant;


                total +=
                    item.precio
                    *
                    cant;

            }
        );


        return {

            cantidad:
                cantidad,

            total:
                total

        };

    }


    function toggleSeleccion(
        index
    ) {

        var cuenta =
            cuentaActual();


        if (
            !cuenta
            ||
            !cuenta.items[
                index
            ]
        ) {

            return;

        }


        var item =
            cuenta.items[
                index
            ];


        item.seleccionado =
            !item.seleccionado;


        item.cant_pagar =
            item.cantidad;


        guardar();

        render();

    }


    function cambiarPago(
        index,
        diferencia
    ) {

        var cuenta =
            cuentaActual();


        if (
            !cuenta
            ||
            !cuenta.items[
                index
            ]
        ) {

            return;

        }


        var item =
            cuenta.items[
                index
            ];


        var cantidad =
            Number(
                item.cant_pagar
                ||
                item.cantidad
            )
            +
            diferencia;


        if (
            cantidad
            <
            1
        ) {

            cantidad =
                1;

        }


        if (
            cantidad
            >
            item.cantidad
        ) {

            cantidad =
                item.cantidad;

        }


        item.cant_pagar =
            cantidad;


        guardar();

        render();

    }


    // ======================================================================
    // CAMBIAR CANTIDAD EN MESA
    // ======================================================================

    function cambiarCantidad(
        index,
        diferencia
    ) {

        var cuenta =
            cuentaActual();


        if (
            !cuenta
            ||
            !cuenta.items[
                index
            ]
        ) {

            return;

        }


        var item =
            cuenta.items[
                index
            ];


        item.cantidad +=
            diferencia;


        if (
            item.cantidad
            <=
            0
        ) {

            cuenta.items.splice(
                index,
                1
            );

        } else {

            if (
                item.cant_pagar
                >
                item.cantidad
            ) {

                item.cant_pagar =
                    item.cantidad;

            }

        }


        recalcular(
            cuenta
        );


        guardar();

        actualizarMesas();

        render();

    }


    // ======================================================================
    // RENDER
    // ======================================================================

    function render() {

        var cuenta =
            cuentaActual();


        if (!cuenta) {
            return;
        }


        recalcular(
            cuenta
        );


        if (
            !cuenta.items.length
        ) {

            listaComanda.innerHTML =
                '<li class="salon-pos__lista-vacia">'
                +
                    '<strong>Mesa vacía</strong>'
                    +
                    '<span>Buscá un producto arriba y presioná Enter.</span>'
                +
                '</li>';

        } else {

            var html =
                '';


            cuenta.items.forEach(
                function (
                    item,
                    index
                ) {

                    var clase =
                        item.seleccionado
                            ? ' is-seleccionado'
                            : '';


                    html +=
                        '<li class="salon-pos__item-comanda'
                        +
                        clase
                        +
                        '" data-index="'
                        +
                        index
                        +
                        '">';


                    html +=
                        '<div class="salon-pos__item-top">';


                    html +=
                        '<div class="salon-pos__item-info">'
                        +
                            '<div class="salon-pos__item-name">'
                            +
                            escapar(
                                item.nombre
                            )
                            +
                            '</div>'
                            +
                            '<div class="salon-pos__item-price">'
                            +
                            dinero(
                                item.precio
                            )
                            +
                            ' c/u · Código '
                            +
                            escapar(
                                item.codigo
                            )
                            +
                            '</div>'
                        +
                        '</div>';


                    html +=
                        '<div class="salon-pos__item-side" data-no-toggle="1">'
                        +
                            '<span class="salon-pos__en-mesa">'
                            +
                            'EN MESA'
                            +
                            '</span>'
                            +
                            '<div class="salon-pos__cantidad-control">'
                            +
                                '<button type="button" class="salon-pos__cantidad-btn" data-action="restar" data-index="'
                                +
                                index
                                +
                                '">−</button>'
                                +
                                '<strong class="salon-pos__cantidad-numero">'
                                +
                                item.cantidad
                                +
                                '</strong>'
                                +
                                '<button type="button" class="salon-pos__cantidad-btn" data-action="sumar" data-index="'
                                +
                                index
                                +
                                '">+</button>'
                            +
                            '</div>'
                        +
                        '</div>';


                    html +=
                        '</div>';


                    if (
                        item.seleccionado
                    ) {

                        html +=
                            '<div class="salon-pos__cobro-inline" data-no-toggle="1">'
                            +
                                '<span class="salon-pos__cobro-label">'
                                +
                                'COBRAR'
                                +
                                '</span>'
                                +
                                '<button type="button" class="salon-pos__mini-btn" data-action="pagar-menos" data-index="'
                                +
                                index
                                +
                                '">−</button>'
                                +
                                '<strong class="salon-pos__cobro-numero">'
                                +
                                item.cant_pagar
                                +
                                '</strong>'
                                +
                                '<button type="button" class="salon-pos__mini-btn" data-action="pagar-mas" data-index="'
                                +
                                index
                                +
                                '">+</button>'
                                +
                                '<span class="salon-pos__cobro-de">'
                                +
                                'de '
                                +
                                item.cantidad
                                +
                                '</span>'
                            +
                            '</div>';

                    }


                    html +=
                        '</li>';

                }
            );


            listaComanda.innerHTML =
                html;

        }


        var resumen =
            resumenSeleccion(
                cuenta
            );


        cantidadLineas.textContent =
            cuenta.items.length
            ===
            1
                ? '1 producto'
                : cuenta.items.length
                    +
                    ' productos';


        totalCuenta.textContent =
            dinero(
                cuenta.total
            );


        if (
            resumen.cantidad
            >
            0
        ) {

            resumenAccion.textContent =
                resumen.cantidad
                ===
                1
                    ? '1 unidad seleccionada'
                    : resumen.cantidad
                        +
                        ' unidades seleccionadas';


            totalSeleccionado.textContent =
                dinero(
                    resumen.total
                );


            btnAccion.textContent =
                'Cobrar selección · '
                +
                dinero(
                    resumen.total
                );


            btnAccion.classList.add(
                'is-parcial'
            );


            btnAccion.classList.remove(
                'is-completa'
            );

        } else {

            resumenAccion.textContent =
                cuenta.items.length
                    ? (
                        'Mesa '
                        +
                        mesaActual
                        +
                        ' · total restante'
                    )
                    : 'Mesa sin productos';


            totalSeleccionado.textContent =
                cuenta.items.length
                    ? dinero(
                        cuenta.total
                    )
                    : '$0';


            btnAccion.textContent =
                cuenta.items.length
                    ? (
                        'Cobrar mesa · '
                        +
                        dinero(
                            cuenta.total
                        )
                    )
                    : 'Cobrar mesa';


            btnAccion.classList.add(
                'is-completa'
            );


            btnAccion.classList.remove(
                'is-parcial'
            );

        }


        btnAccion.disabled =
            !cuenta.items.length
            ||
            enviando;


        btnTicket.disabled =
            !cuenta.items.length
            ||
            enviando;


        guardar();

        actualizarMesas();

    }


    // ======================================================================
    // CSRF
    // ======================================================================

    function obtenerCsrf() {

        var input =
            document.querySelector(
                '#salon-csrf-form input[name="csrfmiddlewaretoken"]'
            );


        return input
            ? input.value
            : '';

    }


    // ======================================================================
    // ITEMS DEL TICKET
    // ======================================================================

    function obtenerItemsTicket(
        cuenta,
        soloSeleccionados
    ) {

        var items =
            [];


        cuenta.items.forEach(
            function (item) {

                if (
                    soloSeleccionados
                    &&
                    !item.seleccionado
                ) {

                    return;

                }


                var cantidad =
                    soloSeleccionados
                        ? Number(
                            item.cant_pagar
                            ||
                            item.cantidad
                        )
                        : Number(
                            item.cantidad
                        );


                items.push({

                    producto_id:
                        item.producto_id,

                    codigo:
                        item.codigo,

                    nombre:
                        item.nombre,

                    precio:
                        item.precio,

                    cantidad:
                        cantidad

                });

            }
        );


        return items;

    }


    // ======================================================================
    // ENVIAR A DJANGO / TICKETERA
    // ======================================================================

    function enviarTicket(
        items,
        tipo
    ) {

        var url =
            root.getAttribute(
                'data-print-url'
            );


        enviando =
            true;


        render();


        return fetch(
            url,
            {

                method:
                    'POST',

                headers: {

                    'Content-Type':
                        'application/json',

                    'X-CSRFToken':
                        obtenerCsrf()

                },

                body:
                    JSON.stringify({

                        mesa:
                            mesaActual,

                        tipo:
                            tipo,

                        items:
                            items

                    })

            }
        )
        .then(
            function (
                response
            ) {

                return response
                    .json()
                    .catch(
                        function () {

                            return {};

                        }
                    )
                    .then(
                        function (data) {

                            if (
                                !response.ok
                                ||
                                data.status
                                !==
                                'ok'
                            ) {

                                throw new Error(
                                    data.mensaje
                                    ||
                                    'No se pudo enviar el ticket.'
                                );

                            }


                            return data;

                        }
                    );

            }
        )
        .finally(
            function () {

                enviando =
                    false;

                render();

            }
        );

    }


    function mostrarError(
        error
    ) {

        Swal.fire({

            icon:
                'error',

            title:
                'No se pudo completar',

            text:
                error.message
                ||
                'Ocurrió un error.',

            background:
                '#12151b',

            color:
                '#f5f7fa'

        });

    }


    // ======================================================================
    // IMPRIMIR
    // ======================================================================

    function imprimirMesa() {

        var cuenta =
            cuentaActual();


        if (
            !cuenta
            ||
            !cuenta.items.length
            ||
            enviando
        ) {

            return;

        }


        enviarTicket(

            obtenerItemsTicket(
                cuenta,
                false
            ),

            'cuenta_mesa'

        )
        .then(
            function () {

                Swal.fire({

                    icon:
                        'success',

                    title:
                        'Ticket enviado',

                    timer:
                        1200,

                    showConfirmButton:
                        false,

                    background:
                        '#12151b',

                    color:
                        '#f5f7fa'

                });

            }
        )
        .catch(
            mostrarError
        );

    }


    // ======================================================================
    // COBRO PARCIAL
    // ======================================================================

    function cobrarParcial() {

        var cuenta =
            cuentaActual();


        var resumen =
            resumenSeleccion(
                cuenta
            );


        var items =
            obtenerItemsTicket(
                cuenta,
                true
            );


        if (
            !items.length
        ) {

            return;

        }


        Swal.fire({

            title:
                'Cobrar '
                +
                dinero(
                    resumen.total
                )
                +
                '?',

            text:
                'Se descontará solamente la selección de la Mesa '
                +
                mesaActual
                +
                '.',

            icon:
                'question',

            showCancelButton:
                true,

            confirmButtonColor:
                '#f59e0b',

            cancelButtonColor:
                '#59616e',

            confirmButtonText:
                'Sí, cobrar',

            cancelButtonText:
                'Cancelar',

            background:
                '#12151b',

            color:
                '#f5f7fa'

        })
        .then(
            function (
                resultado
            ) {

                if (
                    !resultado.isConfirmed
                ) {

                    return;

                }


                enviarTicket(
                    items,
                    'pago_parcial'
                )
                .then(
                    function () {

                        cuenta.items.forEach(
                            function (item) {

                                if (
                                    !item.seleccionado
                                ) {

                                    return;

                                }


                                var cantidad =
                                    Number(
                                        item.cant_pagar
                                        ||
                                        item.cantidad
                                    );


                                item.cantidad -=
                                    cantidad;


                                item.seleccionado =
                                    false;


                                item.cant_pagar =
                                    item.cantidad
                                    >
                                    0
                                        ? item.cantidad
                                        : 0;

                            }
                        );


                        cuenta.items =
                            cuenta.items.filter(
                                function (item) {

                                    return (
                                        item.cantidad
                                        >
                                        0
                                    );

                                }
                            );


                        recalcular(
                            cuenta
                        );


                        guardar();

                        actualizarMesas();

                        render();


                        Swal.fire({

                            icon:
                                'success',

                            title:
                                'Pago parcial cobrado',

                            timer:
                                1200,

                            showConfirmButton:
                                false,

                            background:
                                '#12151b',

                            color:
                                '#f5f7fa'

                        });

                    }
                )
                .catch(
                    mostrarError
                );

            }
        );

    }


    // ======================================================================
    // COBRAR MESA COMPLETA
    // ======================================================================

    function cobrarMesa() {

        var cuenta =
            cuentaActual();


        if (
            !cuenta
            ||
            !cuenta.items.length
        ) {

            return;

        }


        var numeroMesa =
            mesaActual;


        Swal.fire({

            title:
                'Cobrar Mesa '
                +
                numeroMesa
                +
                '?',

            text:
                'Total: '
                +
                dinero(
                    cuenta.total
                ),

            icon:
                'question',

            showCancelButton:
                true,

            confirmButtonColor:
                '#22c55e',

            cancelButtonColor:
                '#59616e',

            confirmButtonText:
                'Sí, cobrar y liberar',

            cancelButtonText:
                'Cancelar',

            background:
                '#12151b',

            color:
                '#f5f7fa'

        })
        .then(
            function (
                resultado
            ) {

                if (
                    !resultado.isConfirmed
                ) {

                    return;

                }


                enviarTicket(

                    obtenerItemsTicket(
                        cuenta,
                        false
                    ),

                    'mesa_completa'

                )
                .then(
                    function () {

                        cuentas[
                            numeroMesa
                        ] = {

                            items: [],

                            total: 0

                        };


                        guardar();

                        actualizarMesas();

                        render();


                        Swal.fire({

                            icon:
                                'success',

                            title:
                                'Mesa liberada',

                            timer:
                                1200,

                            showConfirmButton:
                                false,

                            background:
                                '#12151b',

                            color:
                                '#f5f7fa'

                        });

                    }
                )
                .catch(
                    mostrarError
                );

            }
        );

    }


    // ======================================================================
    // EVENTOS DE MESAS
    // ======================================================================

    botonesMesa.forEach(
        function (boton) {

            boton.addEventListener(
                'click',
                function () {

                    seleccionarMesa(
                        boton.getAttribute(
                            'data-mesa'
                        )
                    );

                }
            );

        }
    );


    // ======================================================================
    // EVENTOS DEL BUSCADOR
    // ======================================================================

    buscador.addEventListener(
        'input',
        function () {

            sugerencias =
                buscarProductos(
                    buscador.value
                );


            sugerenciaActiva =
                sugerencias.length
                    ? 0
                    : -1;


            pintarSugerencias();

        }
    );


    buscador.addEventListener(
        'keydown',
        function (event) {

            if (
                event.key
                ===
                'ArrowDown'
                &&
                sugerencias.length
            ) {

                event.preventDefault();

                sugerenciaActiva++;


                if (
                    sugerenciaActiva
                    >=
                    sugerencias.length
                ) {

                    sugerenciaActiva =
                        0;

                }


                pintarSugerencias();

                return;

            }


            if (
                event.key
                ===
                'ArrowUp'
                &&
                sugerencias.length
            ) {

                event.preventDefault();

                sugerenciaActiva--;


                if (
                    sugerenciaActiva
                    <
                    0
                ) {

                    sugerenciaActiva =
                        sugerencias.length
                        -
                        1;

                }


                pintarSugerencias();

                return;

            }


            if (
                event.key
                ===
                'Escape'
            ) {

                cerrarSugerencias();

                return;

            }


            if (
                event.key
                ===
                'Enter'
            ) {

                event.preventDefault();


                if (
                    sugerencias.length
                ) {

                    var index =
                        sugerenciaActiva
                        >=
                        0
                            ? sugerenciaActiva
                            : 0;


                    agregarProducto(
                        sugerencias[
                            index
                        ]
                    );

                }

            }

        }
    );


    listaSugerencias.addEventListener(
        'click',
        function (event) {

            var item =
                event.target.closest(
                    '.salon-pos__sugerencia'
                );


            if (!item) {
                return;
            }


            var index =
                Number(
                    item.getAttribute(
                        'data-index'
                    )
                );


            if (
                sugerencias[
                    index
                ]
            ) {

                agregarProducto(
                    sugerencias[
                        index
                    ]
                );

            }

        }
    );


    // ======================================================================
    // EVENTOS DE PRODUCTOS
    // ======================================================================

    listaComanda.addEventListener(
        'click',
        function (event) {

            var boton =
                event.target.closest(
                    '[data-action]'
                );


            if (boton) {

                event.stopPropagation();


                var index =
                    Number(
                        boton.getAttribute(
                            'data-index'
                        )
                    );


                var accion =
                    boton.getAttribute(
                        'data-action'
                    );


                if (
                    accion
                    ===
                    'sumar'
                ) {

                    cambiarCantidad(
                        index,
                        1
                    );

                }


                if (
                    accion
                    ===
                    'restar'
                ) {

                    cambiarCantidad(
                        index,
                        -1
                    );

                }


                if (
                    accion
                    ===
                    'pagar-mas'
                ) {

                    cambiarPago(
                        index,
                        1
                    );

                }


                if (
                    accion
                    ===
                    'pagar-menos'
                ) {

                    cambiarPago(
                        index,
                        -1
                    );

                }


                return;

            }


            if (
                event.target.closest(
                    '[data-no-toggle="1"]'
                )
            ) {

                return;

            }


            var fila =
                event.target.closest(
                    '.salon-pos__item-comanda'
                );


            if (fila) {

                toggleSeleccion(
                    Number(
                        fila.getAttribute(
                            'data-index'
                        )
                    )
                );

            }

        }
    );


    // ======================================================================
    // BOTÓN PRINCIPAL
    // ======================================================================

    btnAccion.addEventListener(
        'click',
        function () {

            var cuenta =
                cuentaActual();


            if (
                !cuenta
                ||
                !cuenta.items.length
            ) {

                return;

            }


            var resumen =
                resumenSeleccion(
                    cuenta
                );


            if (
                resumen.cantidad
                >
                0
            ) {

                cobrarParcial();

            } else {

                cobrarMesa();

            }

        }
    );


    // ======================================================================
    // TICKET
    // ======================================================================

    btnTicket.addEventListener(
        'click',
        imprimirMesa
    );


    // ======================================================================
    // CERRAR SUGERENCIAS
    // ======================================================================

    document.addEventListener(
        'click',
        function (event) {

            if (
                !event.target.closest(
                    '.salon-pos__field--buscador'
                )
            ) {

                cerrarSugerencias();

            }

        }
    );


    // ======================================================================
    // EVENTOS DE LA VENTANA FLOTANTE
    // ======================================================================

    if (
        btnCerrarComanda
    ) {

        btnCerrarComanda.addEventListener(
            'click',
            cerrarComanda
        );

    }


    if (
        modalOverlay
    ) {

        modalOverlay.addEventListener(
            'click',
            cerrarComanda
        );

    }


    document.addEventListener(
        'keydown',
        function (event) {

            if (
                event.key
                ===
                'Escape'
            ) {

                cerrarComanda();

            }

        }
    );


    // ======================================================================
    // GUARDADO AUTOMÁTICO
    // ======================================================================

    window.addEventListener(
        'pagehide',
        function () {

            guardar();

        }
    );


    window.addEventListener(
        'beforeunload',
        function () {

            guardar();

        }
    );


    // ======================================================================
    // INICIO
    // ======================================================================

    actualizarMesas();


    try {

        var ultimaMesa =
            localStorage.getItem(
                MESA_ACTUAL_KEY
            );


        if (
            ultimaMesa
            &&
            document.querySelector(
                '.salon-pos__mesa[data-mesa="'
                +
                ultimaMesa
                +
                '"]'
            )
        ) {

            seleccionarMesa(
                ultimaMesa
            );

        }

    } catch (error) {

        console.warn(
            'No se pudo restaurar la última mesa:',
            error
        );

    }

})();