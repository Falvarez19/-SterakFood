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
// MÓDULO 9: POS DE SALÓN
// ==========================================================================

(function () {
    'use strict';

    var salonRoot = document.getElementById('salon-pos');

    if (!salonRoot) {
        return;
    }


    // =========================================================
    // PRODUCTOS DESDE DJANGO
    // =========================================================

    var productosData = document.getElementById('salon-productos-data');
    var productosSalon = [];

    if (productosData) {

        try {

            productosSalon = JSON.parse(
                productosData.textContent || '[]'
            );

        } catch (error) {

            console.error(
                'No se pudieron leer los productos del salón:',
                error
            );

            productosSalon = [];

        }

    }


    // =========================================================
    // ESTADO
    // =========================================================

    var STORAGE_KEY = 'sterakfood_salon_cuentas_v1';

    var mesaActual = null;

    var cuentasMesas = cargarCuentasSalon();

    var indiceSugerencia = -1;

    var resultadosSugerencias = [];


    // =========================================================
    // ELEMENTOS
    // =========================================================

    var botonesMesa = Array.prototype.slice.call(
        document.querySelectorAll('.salon-pos__mesa')
    );

    var tituloMesa =
        document.getElementById('titulo-mesa');

    var estadoMesa =
        document.getElementById('estado-mesa');

    var mensajeSeleccionar =
        document.getElementById('mensaje-seleccionar-mesa');

    var areaComanda =
        document.getElementById('area-comanda');

    var inputCant =
        document.getElementById('input-cant');

    var buscador =
        document.getElementById('buscador');

    var sugerenciasBox =
        document.getElementById('lista-sugerencias');

    var listaComanda =
        document.getElementById('lista-comanda');

    var totalCuenta =
        document.getElementById('total-cuenta');

    var totalSeleccionado =
        document.getElementById('total-seleccionado');

    var cantidadLineas =
        document.getElementById('cantidad-lineas');

    var btnCobrarParcial =
        document.getElementById('btn-cobrar-parcial');

    var btnImprimirMesa =
        document.getElementById('btn-imprimir-mesa');

    var btnCobrarMesa =
        document.getElementById('btn-cobrar-mesa');


    // =========================================================
    // INICIO
    // =========================================================

    normalizarProductosSalon();

    actualizarEstadosMesas();

    registrarEventosSalon();


    // =========================================================
    // NORMALIZAR PRODUCTOS
    // =========================================================

    function normalizarProductosSalon() {

        productosSalon = productosSalon.map(
            function (producto) {

                return {

                    codigo: String(
                        producto.codigo || ''
                    ),

                    nombre: String(
                        producto.nombre || ''
                    ),

                    precio: Number(
                        producto.precio || 0
                    )

                };

            }
        );

    }


    // =========================================================
    // EVENTOS
    // =========================================================

    function registrarEventosSalon() {

        botonesMesa.forEach(
            function (boton) {

                boton.addEventListener(
                    'click',
                    function () {

                        seleccionarMesa(
                            Number(
                                boton.getAttribute('data-mesa')
                            )
                        );

                    }
                );

            }
        );


        // ENTER EN CANT -> BUSCADOR

        inputCant.addEventListener(
            'keydown',
            function (event) {

                if (event.key === 'Enter') {

                    event.preventDefault();

                    buscador.focus();

                    buscador.select();

                }

            }
        );


        buscador.addEventListener(
            'input',
            function () {

                actualizarSugerencias();

            }
        );


        buscador.addEventListener(
            'keydown',
            function (event) {

                manejarTecladoBuscador(event);

            }
        );


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


        btnCobrarParcial.addEventListener(
            'click',
            cobrarSeleccionParcial
        );


        btnImprimirMesa.addEventListener(
            'click',
            imprimirTicketMesa
        );


        btnCobrarMesa.addEventListener(
            'click',
            cobrarMesaCompletaSalon
        );

    }


    // =========================================================
    // CUENTA ACTUAL
    // =========================================================

    function obtenerCuentaActual() {

        if (!mesaActual) {
            return null;
        }


        if (!cuentasMesas[mesaActual]) {

            cuentasMesas[mesaActual] = {

                items: [],

                total: 0

            };

        }


        return cuentasMesas[mesaActual];

    }


    // =========================================================
    // SELECCIONAR MESA
    // =========================================================

    function seleccionarMesa(numeroMesa) {

        mesaActual = numeroMesa;

        obtenerCuentaActual();


        tituloMesa.textContent =
            'Mesa ' + numeroMesa;


        estadoMesa.textContent =
            'MESA ' + numeroMesa;


        estadoMesa.classList.add(
            'is-activa'
        );


        mensajeSeleccionar.hidden = true;

        areaComanda.hidden = false;


        inputCant.value = '1';

        buscador.value = '';


        cerrarSugerencias();

        actualizarEstadosMesas();

        renderizarComandaSalon();


        window.setTimeout(
            function () {

                inputCant.focus();

                inputCant.select();

            },
            50
        );

    }


    // =========================================================
    // ESTADOS DE MESAS
    // =========================================================

    function actualizarEstadosMesas() {

        botonesMesa.forEach(
            function (boton) {

                var numero = Number(
                    boton.getAttribute('data-mesa')
                );


                var cuenta =
                    cuentasMesas[numero];


                var estaOcupada =
                    Boolean(
                        cuenta &&
                        cuenta.items &&
                        cuenta.items.length > 0
                    );


                boton.classList.toggle(
                    'mesa-ocupada',
                    estaOcupada
                );


                boton.classList.toggle(
                    'mesa-seleccionada',
                    numero === mesaActual
                );

            }
        );

    }


    // =========================================================
    // BUSCADOR
    // =========================================================

    function actualizarSugerencias() {

        var texto =
            buscador.value
                .trim()
                .toLowerCase();


        indiceSugerencia = -1;

        resultadosSugerencias = [];


        limpiarNodo(
            sugerenciasBox
        );


        if (!texto) {

            cerrarSugerencias();

            return;

        }


        resultadosSugerencias =
            productosSalon.filter(
                function (producto) {

                    return (
                        producto.codigo
                            .toLowerCase()
                            .indexOf(texto) !== -1
                        ||
                        producto.nombre
                            .toLowerCase()
                            .indexOf(texto) !== -1
                    );

                }
            ).slice(
                0,
                15
            );


        if (
            resultadosSugerencias.length === 0
        ) {

            cerrarSugerencias();

            return;

        }


        resultadosSugerencias.forEach(
            function (producto, index) {

                var li =
                    document.createElement('li');


                li.setAttribute(
                    'role',
                    'option'
                );


                li.setAttribute(
                    'data-index',
                    String(index)
                );


                var codigo =
                    document.createElement('span');


                codigo.className =
                    'sugerencia-codigo';


                codigo.textContent =
                    producto.codigo + ' · ';


                var nombre =
                    document.createElement('span');


                nombre.textContent =
                    producto.nombre;


                var precio =
                    document.createElement('span');


                precio.className =
                    'sugerencia-precio';


                precio.textContent =
                    formatMonto(
                        producto.precio
                    );


                li.appendChild(
                    codigo
                );


                li.appendChild(
                    nombre
                );


                li.appendChild(
                    precio
                );


                li.addEventListener(
                    'mousedown',
                    function (event) {

                        event.preventDefault();

                        confirmarAgregadoSalon(
                            producto
                        );

                    }
                );


                sugerenciasBox.appendChild(
                    li
                );

            }
        );


        sugerenciasBox.classList.add(
            'is-open'
        );

    }


    // =========================================================
    // TECLADO DEL BUSCADOR
    // =========================================================

    function manejarTecladoBuscador(event) {

        var items =
            sugerenciasBox.querySelectorAll(
                'li'
            );


        if (
            event.key === 'ArrowDown'
        ) {

            event.preventDefault();


            if (
                items.length === 0
            ) {

                return;

            }


            indiceSugerencia++;


            if (
                indiceSugerencia >=
                items.length
            ) {

                indiceSugerencia = 0;

            }


            resaltarSugerencia(
                items
            );


            return;

        }


        if (
            event.key === 'ArrowUp'
        ) {

            event.preventDefault();


            if (
                items.length === 0
            ) {

                return;

            }


            indiceSugerencia--;


            if (
                indiceSugerencia < 0
            ) {

                indiceSugerencia =
                    items.length - 1;

            }


            resaltarSugerencia(
                items
            );


            return;

        }


        if (
            event.key === 'Escape'
        ) {

            cerrarSugerencias();

            return;

        }


        if (
            event.key === 'Enter'
        ) {

            event.preventDefault();


            if (
                indiceSugerencia >= 0 &&
                resultadosSugerencias[
                    indiceSugerencia
                ]
            ) {

                confirmarAgregadoSalon(
                    resultadosSugerencias[
                        indiceSugerencia
                    ]
                );

                return;

            }


            var texto =
                buscador.value
                    .trim()
                    .toLowerCase();


            var exacto =
                productosSalon.find(
                    function (producto) {

                        return (
                            producto.codigo
                                .toLowerCase() === texto
                            ||
                            producto.nombre
                                .toLowerCase() === texto
                        );

                    }
                );


            if (exacto) {

                confirmarAgregadoSalon(
                    exacto
                );

                return;

            }


            if (
                resultadosSugerencias.length === 1
            ) {

                confirmarAgregadoSalon(
                    resultadosSugerencias[0]
                );

            }

        }

    }


    function resaltarSugerencia(items) {

        Array.prototype.forEach.call(
            items,
            function (item, index) {

                item.classList.toggle(
                    'activo',
                    index === indiceSugerencia
                );

            }
        );


        if (
            items[indiceSugerencia]
        ) {

            items[
                indiceSugerencia
            ].scrollIntoView({

                block: 'nearest'

            });

        }

    }


    function cerrarSugerencias() {

        sugerenciasBox.classList.remove(
            'is-open'
        );


        limpiarNodo(
            sugerenciasBox
        );


        indiceSugerencia = -1;

        resultadosSugerencias = [];

    }


    // =========================================================
    // AGREGAR PRODUCTO
    // =========================================================

    function confirmarAgregadoSalon(producto) {

        if (!mesaActual) {
            return;
        }


        var cantidad =
            parseInt(
                inputCant.value,
                10
            );


        if (
            isNaN(cantidad) ||
            cantidad < 1
        ) {

            cantidad = 1;

        }


        agregarProductoAComanda(
            producto,
            cantidad
        );


        inputCant.value = '1';

        buscador.value = '';


        cerrarSugerencias();


        inputCant.focus();

        inputCant.select();

    }


    function agregarProductoAComanda(
        producto,
        cantidad
    ) {

        var cuenta =
            obtenerCuentaActual();


        var existente =
            cuenta.items.find(
                function (item) {

                    return (
                        item.codigo ===
                        producto.codigo
                    );

                }
            );


        if (existente) {

            existente.cantidad +=
                cantidad;

        } else {

            cuenta.items.push({

                codigo:
                    producto.codigo,

                nombre:
                    producto.nombre,

                precio:
                    Number(
                        producto.precio
                    ),

                cantidad:
                    cantidad,

                seleccionado:
                    false,

                cant_pagar:
                    cantidad

            });

        }


        recalcularCuenta(
            cuenta
        );


        guardarCuentasSalon();

        actualizarEstadosMesas();

        renderizarComandaSalon();

    }


    // =========================================================
    // CAMBIAR CANTIDAD + / -
    // =========================================================

    function cambiarCantidadSalon(
        index,
        delta
    ) {

        var cuenta =
            obtenerCuentaActual();


        if (
            !cuenta ||
            !cuenta.items[index]
        ) {

            return;

        }


        var item =
            cuenta.items[index];


        item.cantidad += delta;


        if (
            item.cantidad <= 0
        ) {

            cuenta.items.splice(
                index,
                1
            );

        } else {

            if (
                !item.cant_pagar ||
                item.cant_pagar < 1
            ) {

                item.cant_pagar = 1;

            }


            if (
                item.cant_pagar >
                item.cantidad
            ) {

                item.cant_pagar =
                    item.cantidad;

            }

        }


        recalcularCuenta(
            cuenta
        );


        guardarCuentasSalon();

        actualizarEstadosMesas();

        renderizarComandaSalon();

    }


    // =========================================================
    // SELECCIÓN PAGO PARCIAL
    // =========================================================

    function toggleSeleccionSalon(
        index,
        checked
    ) {

        var cuenta =
            obtenerCuentaActual();


        if (
            !cuenta ||
            !cuenta.items[index]
        ) {

            return;

        }


        var item =
            cuenta.items[index];


        item.seleccionado =
            checked;


        if (checked) {

            item.cant_pagar =
                item.cantidad;

        }


        guardarCuentasSalon();

        renderizarComandaSalon();

    }


    function actualizarCantPagarSalon(
        index,
        valor,
        input
    ) {

        var cuenta =
            obtenerCuentaActual();


        if (
            !cuenta ||
            !cuenta.items[index]
        ) {

            return;

        }


        var item =
            cuenta.items[index];


        var cantidad =
            parseInt(
                valor,
                10
            );


        if (
            isNaN(cantidad) ||
            cantidad < 1
        ) {

            cantidad = 1;

        }


        if (
            cantidad >
            item.cantidad
        ) {

            cantidad =
                item.cantidad;

        }


        item.cant_pagar =
            cantidad;


        input.value =
            String(cantidad);


        guardarCuentasSalon();

        actualizarTotalSeleccionado();

    }


    // =========================================================
    // RECALCULAR TOTAL
    // =========================================================

    function recalcularCuenta(cuenta) {

        cuenta.total =
            cuenta.items.reduce(
                function (
                    acumulado,
                    item
                ) {

                    return (
                        acumulado +
                        Number(
                            item.precio
                        ) *
                        Number(
                            item.cantidad
                        )
                    );

                },
                0
            );

    }


    // =========================================================
    // RENDER COMANDA
    // =========================================================

    function renderizarComandaSalon() {

        var cuenta =
            obtenerCuentaActual();


        if (!cuenta) {
            return;
        }


        limpiarNodo(
            listaComanda
        );


        if (
            cuenta.items.length === 0
        ) {

            var vacio =
                document.createElement(
                    'li'
                );


            vacio.className =
                'salon-pos__lista-vacia';


            vacio.textContent =
                'Todavía no hay productos cargados en esta mesa.';


            listaComanda.appendChild(
                vacio
            );

        } else {

            cuenta.items.forEach(
                function (
                    item,
                    index
                ) {

                    listaComanda.appendChild(
                        crearItemComanda(
                            item,
                            index
                        )
                    );

                }
            );

        }


        totalCuenta.textContent =
            formatMonto(
                cuenta.total
            );


        cantidadLineas.textContent =
            cuenta.items.length === 1
                ? '1 ítem'
                : cuenta.items.length +
                  ' ítems';


        actualizarTotalSeleccionado();

        actualizarBotonesAccion();

    }


    // =========================================================
    // CREAR FILA DE PRODUCTO
    // =========================================================

    function crearItemComanda(
        item,
        index
    ) {

        var li =
            document.createElement(
                'li'
            );


        li.className =
            'salon-pos__item-comanda';


        if (
            item.seleccionado
        ) {

            li.classList.add(
                'is-seleccionado'
            );

        }


        // IZQUIERDA

        var izquierda =
            document.createElement(
                'div'
            );


        izquierda.className =
            'salon-pos__item-left';


        // CHECKBOX

        var check =
            document.createElement(
                'input'
            );


        check.type =
            'checkbox';


        check.className =
            'salon-pos__check';


        check.checked =
            Boolean(
                item.seleccionado
            );


        check.setAttribute(
            'aria-label',
            'Seleccionar ' +
            item.nombre +
            ' para pago parcial'
        );


        check.addEventListener(
            'change',
            function () {

                toggleSeleccionSalon(
                    index,
                    check.checked
                );

            }
        );


        // INFO

        var info =
            document.createElement(
                'div'
            );


        info.className =
            'salon-pos__item-info';


        var nombre =
            document.createElement(
                'div'
            );


        nombre.className =
            'salon-pos__item-name';


        nombre.textContent =
            item.nombre;


        var precioUnitario =
            document.createElement(
                'div'
            );


        precioUnitario.className =
            'salon-pos__item-price';


        precioUnitario.textContent =
            formatMonto(
                item.precio
            ) +
            ' c/u · Código ' +
            item.codigo;


        info.appendChild(
            nombre
        );


        info.appendChild(
            precioUnitario
        );


        // ¿CUÁNTAS PAGA?

        if (
            item.seleccionado &&
            item.cantidad > 1
        ) {

            var parcial =
                document.createElement(
                    'div'
                );


            parcial.className =
                'salon-pos__parcial-cantidad';


            var label =
                document.createElement(
                    'label'
                );


            label.textContent =
                '¿Cuántas paga?';


            var inputParcial =
                document.createElement(
                    'input'
                );


            inputParcial.type =
                'number';


            inputParcial.className =
                'salon-pos__input-parcial';


            inputParcial.min =
                '1';


            inputParcial.max =
                String(
                    item.cantidad
                );


            inputParcial.step =
                '1';


            inputParcial.value =
                String(
                    item.cant_pagar ||
                    item.cantidad
                );


            inputParcial.setAttribute(
                'aria-label',
                'Cantidad que paga de ' +
                item.nombre
            );


            inputParcial.addEventListener(
                'change',
                function () {

                    actualizarCantPagarSalon(
                        index,
                        inputParcial.value,
                        inputParcial
                    );

                }
            );


            inputParcial.addEventListener(
                'input',
                function () {

                    var cantidadTemporal =
                        parseInt(
                            inputParcial.value,
                            10
                        );


                    if (
                        !isNaN(
                            cantidadTemporal
                        ) &&
                        cantidadTemporal >= 1 &&
                        cantidadTemporal <=
                            item.cantidad
                    ) {

                        item.cant_pagar =
                            cantidadTemporal;


                        actualizarTotalSeleccionado();

                    }

                }
            );


            parcial.appendChild(
                label
            );


            parcial.appendChild(
                inputParcial
            );


            info.appendChild(
                parcial
            );

        }


        izquierda.appendChild(
            check
        );


        izquierda.appendChild(
            info
        );


        // DERECHA

        var derecha =
            document.createElement(
                'div'
            );


        derecha.className =
            'salon-pos__item-right';


        var controlCantidad =
            document.createElement(
                'div'
            );


        controlCantidad.className =
            'salon-pos__cantidad-control';


        // BOTÓN MENOS

        var btnMenos =
            document.createElement(
                'button'
            );


        btnMenos.type =
            'button';


        btnMenos.className =
            'salon-pos__cantidad-btn';


        btnMenos.textContent =
            '−';


        btnMenos.setAttribute(
            'aria-label',
            'Restar una unidad de ' +
            item.nombre
        );


        btnMenos.addEventListener(
            'click',
            function () {

                cambiarCantidadSalon(
                    index,
                    -1
                );

            }
        );


        // CANTIDAD

        var cantidad =
            document.createElement(
                'span'
            );


        cantidad.className =
            'salon-pos__cantidad-numero';


        cantidad.textContent =
            String(
                item.cantidad
            );


        // BOTÓN MÁS

        var btnMas =
            document.createElement(
                'button'
            );


        btnMas.type =
            'button';


        btnMas.className =
            'salon-pos__cantidad-btn';


        btnMas.textContent =
            '+';


        btnMas.setAttribute(
            'aria-label',
            'Sumar una unidad de ' +
            item.nombre
        );


        btnMas.addEventListener(
            'click',
            function () {

                cambiarCantidadSalon(
                    index,
                    1
                );

            }
        );


        controlCantidad.appendChild(
            btnMenos
        );


        controlCantidad.appendChild(
            cantidad
        );


        controlCantidad.appendChild(
            btnMas
        );


        var subtotal =
            document.createElement(
                'div'
            );


        subtotal.className =
            'salon-pos__item-subtotal';


        subtotal.textContent =
            formatMonto(
                Number(
                    item.precio
                ) *
                Number(
                    item.cantidad
                )
            );


        derecha.appendChild(
            controlCantidad
        );


        derecha.appendChild(
            subtotal
        );


        li.appendChild(
            izquierda
        );


        li.appendChild(
            derecha
        );


        return li;

    }


    // =========================================================
    // TOTAL SELECCIONADO
    // =========================================================

    function actualizarTotalSeleccionado() {

        var cuenta =
            obtenerCuentaActual();


        if (!cuenta) {

            totalSeleccionado.textContent =
                formatMonto(0);

            return;

        }


        var subtotal =
            cuenta.items.reduce(
                function (
                    acumulado,
                    item
                ) {

                    if (
                        !item.seleccionado
                    ) {

                        return acumulado;

                    }


                    var cantidadPagar =
                        item.cantidad > 1
                            ? Number(
                                item.cant_pagar ||
                                item.cantidad
                            )
                            : 1;


                    return (
                        acumulado +
                        Number(
                            item.precio
                        ) *
                        cantidadPagar
                    );

                },
                0
            );


        totalSeleccionado.textContent =
            formatMonto(
                subtotal
            );

    }


    // =========================================================
    // BOTONES DE ACCIÓN
    // =========================================================

    function actualizarBotonesAccion() {

        var cuenta =
            obtenerCuentaActual();


        var tieneItems =
            Boolean(
                cuenta &&
                cuenta.items.length > 0
            );


        var tieneSeleccion =
            Boolean(
                cuenta &&
                cuenta.items.some(
                    function (item) {

                        return (
                            item.seleccionado
                        );

                    }
                )
            );


        btnImprimirMesa.disabled =
            !tieneItems;


        btnCobrarMesa.disabled =
            !tieneItems;


        btnCobrarParcial.disabled =
            !tieneSeleccion;

    }


    // =========================================================
    // COBRAR SELECCIÓN PARCIAL
    // =========================================================

    function cobrarSeleccionParcial() {

        var cuenta =
            obtenerCuentaActual();


        if (!cuenta) {
            return;
        }


        var itemsSeleccionados =
            cuenta.items.filter(
                function (item) {

                    return (
                        item.seleccionado
                    );

                }
            );


        if (
            itemsSeleccionados.length === 0
        ) {

            Swal.fire({

                icon:
                    'warning',

                title:
                    'Nada seleccionado',

                text:
                    'Tildá al menos un producto para cobrar una parte de la mesa.',

                background:
                    '#12151b',

                color:
                    '#f5f7fa'

            });


            return;

        }


        var itemsTicket =
            itemsSeleccionados.map(
                function (item) {

                    var cantidadCobrar =
                        item.cantidad > 1
                            ? Number(
                                item.cant_pagar ||
                                item.cantidad
                            )
                            : 1;


                    if (
                        cantidadCobrar < 1
                    ) {

                        cantidadCobrar = 1;

                    }


                    if (
                        cantidadCobrar >
                        item.cantidad
                    ) {

                        cantidadCobrar =
                            item.cantidad;

                    }


                    return {

                        codigo:
                            item.codigo,

                        nombre:
                            item.nombre,

                        precio:
                            Number(
                                item.precio
                            ),

                        cantidad_cobrada:
                            cantidadCobrar

                    };

                }
            );


        var subtotal =
            itemsTicket.reduce(
                function (
                    acumulado,
                    item
                ) {

                    return (
                        acumulado +
                        item.precio *
                        item.cantidad_cobrada
                    );

                },
                0
            );


        Swal.fire({

            title:
                '¿Cobrar selección parcial?',

            text:
                'Monto a cobrar: ' +
                formatMonto(
                    subtotal
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
                'Sí, cobrar e imprimir',

            cancelButtonText:
                'Cancelar',

            background:
                '#12151b',

            color:
                '#f5f7fa'

        }).then(
            function (resultado) {

                if (
                    !resultado.isConfirmed
                ) {

                    return;

                }


                imprimirTicketParcialSalon(
                    itemsTicket,
                    subtotal
                );


                cuenta.items.forEach(
                    function (item) {

                        if (
                            !item.seleccionado
                        ) {

                            return;

                        }


                        var cantidadCobrar =
                            item.cantidad > 1
                                ? Number(
                                    item.cant_pagar ||
                                    item.cantidad
                                )
                                : 1;


                        if (
                            cantidadCobrar < 1
                        ) {

                            cantidadCobrar = 1;

                        }


                        if (
                            cantidadCobrar >
                            item.cantidad
                        ) {

                            cantidadCobrar =
                                item.cantidad;

                        }


                        item.cantidad -=
                            cantidadCobrar;


                        item.seleccionado =
                            false;


                        item.cant_pagar =
                            item.cantidad > 0
                                ? item.cantidad
                                : 0;

                    }
                );


                cuenta.items =
                    cuenta.items.filter(
                        function (item) {

                            return (
                                item.cantidad > 0
                            );

                        }
                    );


                recalcularCuenta(
                    cuenta
                );


                guardarCuentasSalon();

                actualizarEstadosMesas();

                renderizarComandaSalon();


                Swal.fire({

                    icon:
                        'success',

                    title:
                        'Pago parcial cobrado',

                    text:
                        'Quedó pendiente en la mesa solamente lo que no se cobró.',

                    timer:
                        1700,

                    showConfirmButton:
                        false,

                    background:
                        '#12151b',

                    color:
                        '#f5f7fa'

                });

            }
        );

    }


    // =========================================================
    // TICKET PARCIAL
    // =========================================================

    function imprimirTicketParcialSalon(
        items,
        total
    ) {

        abrirTicketImpresion(
            items,
            total,
            'PAGO PARCIAL'
        );

    }


    // =========================================================
    // IMPRIMIR CUENTA COMPLETA
    // =========================================================

    function imprimirTicketMesa() {

        var cuenta =
            obtenerCuentaActual();


        if (
            !cuenta ||
            cuenta.items.length === 0
        ) {

            Swal.fire({

                icon:
                    'info',

                title:
                    'Mesa vacía',

                text:
                    'No hay productos para imprimir.',

                background:
                    '#12151b',

                color:
                    '#f5f7fa'

            });


            return;

        }


        var items =
            cuenta.items.map(
                function (item) {

                    return {

                        codigo:
                            item.codigo,

                        nombre:
                            item.nombre,

                        precio:
                            Number(
                                item.precio
                            ),

                        cantidad_cobrada:
                            Number(
                                item.cantidad
                            )

                    };

                }
            );


        abrirTicketImpresion(
            items,
            cuenta.total,
            'CUENTA DE MESA'
        );

    }


    // =========================================================
    // COBRAR MESA COMPLETA
    // =========================================================

    function cobrarMesaCompletaSalon() {

        var cuenta =
            obtenerCuentaActual();


        if (
            !cuenta ||
            cuenta.items.length === 0
        ) {

            return;

        }


        var numeroMesa =
            mesaActual;


        var total =
            cuenta.total;


        Swal.fire({

            title:
                '¿Cobrar toda la Mesa ' +
                numeroMesa +
                '?',

            text:
                'Total a cobrar: ' +
                formatMonto(
                    total
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
                'Sí, cobrar y liberar mesa',

            cancelButtonText:
                'Cancelar',

            background:
                '#12151b',

            color:
                '#f5f7fa'

        }).then(
            function (resultado) {

                if (
                    !resultado.isConfirmed
                ) {

                    return;

                }


                cuentasMesas[
                    numeroMesa
                ] = {

                    items: [],

                    total: 0

                };


                guardarCuentasSalon();

                actualizarEstadosMesas();

                renderizarComandaSalon();


                Swal.fire({

                    icon:
                        'success',

                    title:
                        'Mesa cobrada',

                    text:
                        'La Mesa ' +
                        numeroMesa +
                        ' quedó liberada.',

                    timer:
                        1600,

                    showConfirmButton:
                        false,

                    background:
                        '#12151b',

                    color:
                        '#f5f7fa'

                });

            }
        );

    }


    // =========================================================
    // IMPRESIÓN
    // =========================================================

    function abrirTicketImpresion(
        items,
        total,
        tipoTicket
    ) {

        var ventana =
            window.open(
                '',
                '_blank',
                'width=420,height=700'
            );


        if (!ventana) {

            Swal.fire({

                icon:
                    'warning',

                title:
                    'Ventana bloqueada',

                text:
                    'Permití las ventanas emergentes del navegador para imprimir el ticket.',

                background:
                    '#12151b',

                color:
                    '#f5f7fa'

            });


            return;

        }


        var filas = '';


        items.forEach(
            function (item) {

                var cantidad =
                    Number(
                        item.cantidad_cobrada ||
                        0
                    );


                var subtotal =
                    Number(
                        item.precio
                    ) *
                    cantidad;


                filas +=
                    '<tr>';


                filas +=
                    '<td>' +
                    escaparHtml(
                        String(
                            cantidad
                        )
                    ) +
                    'x</td>';


                filas +=
                    '<td>' +
                    escaparHtml(
                        item.nombre
                    ) +
                    '</td>';


                filas +=
                    '<td>' +
                    escaparHtml(
                        formatMonto(
                            subtotal
                        )
                    ) +
                    '</td>';


                filas +=
                    '</tr>';

            }
        );


        var html = '';


        html +=
            '<!DOCTYPE html>';


        html +=
            '<html lang="es">';


        html +=
            '<head>';


        html +=
            '<meta charset="UTF-8">';


        html +=
            '<title>Ticket Mesa ' +
            escaparHtml(
                String(
                    mesaActual
                )
            ) +
            '</title>';


        html +=
            '<link rel="stylesheet" href="/static/css/estilos.css">';


        html +=
            '</head>';


        html +=
            '<body>';


        html +=
            '<main class="salon-ticket">';


        html +=
            '<h2 class="salon-ticket__brand">SterakFood</h2>';


        html +=
            '<div class="salon-ticket__meta">Mesa ' +
            escaparHtml(
                String(
                    mesaActual
                )
            ) +
            '</div>';


        html +=
            '<div class="salon-ticket__type">' +
            escaparHtml(
                tipoTicket
            ) +
            '</div>';


        html +=
            '<hr>';


        html +=
            '<table class="salon-ticket__table">' +
            filas +
            '</table>';


        html +=
            '<hr>';


        html +=
            '<div class="salon-ticket__total">';


        html +=
            '<span>TOTAL</span>';


        html +=
            '<span>' +
            escaparHtml(
                formatMonto(
                    total
                )
            ) +
            '</span>';


        html +=
            '</div>';


        html +=
            '<p class="salon-ticket__thanks">Gracias por su compra</p>';


        html +=
            '</main>';


        html +=
            '</body>';


        html +=
            '</html>';


        ventana.document.open();

        ventana.document.write(
            html
        );

        ventana.document.close();

        ventana.focus();


        window.setTimeout(
            function () {

                ventana.print();

            },
            250
        );

    }


    // =========================================================
    // FORMATEAR DINERO
    // =========================================================

    function formatMonto(valor) {

        var numero =
            Number(
                valor || 0
            );


        return (
            '$' +
            numero.toLocaleString(
                'es-AR',
                {

                    minimumFractionDigits:
                        2,

                    maximumFractionDigits:
                        2

                }
            )
        );

    }


    // =========================================================
    // LIMPIAR NODO
    // =========================================================

    function limpiarNodo(nodo) {

        while (
            nodo.firstChild
        ) {

            nodo.removeChild(
                nodo.firstChild
            );

        }

    }


    // =========================================================
    // ESCAPAR HTML
    // =========================================================

    function escaparHtml(texto) {

        return String(
            texto
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


    // =========================================================
    // GUARDAR CUENTAS
    // =========================================================

    function guardarCuentasSalon() {

        try {

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(
                    cuentasMesas
                )
            );

        } catch (error) {

            console.warn(
                'No se pudo guardar el estado local del salón:',
                error
            );

        }

    }


    // =========================================================
    // RECUPERAR CUENTAS
    // =========================================================

    function cargarCuentasSalon() {

        try {

            var guardado =
                localStorage.getItem(
                    STORAGE_KEY
                );


            if (!guardado) {

                return {};

            }


            var cuentas =
                JSON.parse(
                    guardado
                );


            if (
                !cuentas ||
                typeof cuentas !== 'object'
            ) {

                return {};

            }


            Object.keys(
                cuentas
            ).forEach(
                function (mesa) {

                    var cuenta =
                        cuentas[mesa];


                    if (
                        !cuenta ||
                        !Array.isArray(
                            cuenta.items
                        )
                    ) {

                        delete cuentas[
                            mesa
                        ];

                        return;

                    }


                    cuenta.items =
                        cuenta.items
                            .filter(
                                function (item) {

                                    return (
                                        item &&
                                        Number(
                                            item.cantidad
                                        ) > 0
                                    );

                                }
                            )
                            .map(
                                function (item) {

                                    return {

                                        codigo:
                                            String(
                                                item.codigo ||
                                                ''
                                            ),

                                        nombre:
                                            String(
                                                item.nombre ||
                                                ''
                                            ),

                                        precio:
                                            Number(
                                                item.precio ||
                                                0
                                            ),

                                        cantidad:
                                            Number(
                                                item.cantidad ||
                                                0
                                            ),

                                        seleccionado:
                                            false,

                                        cant_pagar:
                                            Number(
                                                item.cantidad ||
                                                0
                                            )

                                    };

                                }
                            );


                    recalcularCuenta(
                        cuenta
                    );

                }
            );


            return cuentas;

        } catch (error) {

            console.warn(
                'No se pudo recuperar el estado local del salón:',
                error
            );


            return {};

        }

    }

})();