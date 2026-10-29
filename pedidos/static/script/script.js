// ==========================================================================
// # MÓDULO 0: PANTALLA DE CARGA MODERNA SAN MARTÍN
// ==========================================================================

document.addEventListener('DOMContentLoaded', function() {
    const porcentajeEl = document.getElementById('carga-porcentaje');
    const preloader = document.getElementById('pantalla-carga');
    if (!preloader) {
        document.body.classList.remove('bloquear-scroll');
        return;
    }
    let progreso = 0;
    let finalizado = false;
    const intervalo = setInterval(() => {
        if (!porcentajeEl || finalizado) return;
        if (progreso < 90) {
            progreso += Math.floor(Math.random() * 12) + 4;
            if (progreso > 90) progreso = 90;
            porcentajeEl.textContent = progreso + '%';
        }
    }, 90);
    window.addEventListener('load', function() {
        if (finalizado) return;
        finalizado = true;
        clearInterval(intervalo);
        if (porcentajeEl) {
            porcentajeEl.textContent = '100%';
        }
        setTimeout(() => {
            preloader.style.opacity = '0';
            preloader.style.visibility = 'hidden';
            document.body.classList.remove('bloquear-scroll');
            setTimeout(() => {
                if (preloader.parentNode) {
                    preloader.remove();
                }
            }, 600);
        }, 250);
    });
});
// ==========================================================================
// # MÓDULO 1: GESTIÓN DEL CARRITO DE COMPRAS Y SESIÓN
// ==========================================================================

document.addEventListener("DOMContentLoaded", function() {
    const badge = document.getElementById('badge-contador');
    if (badge) {
        fetch('/carrito/ver/')
            .then(res => res.json())
            .then(datos => {
                let total = 0;
                if (datos.items && datos.items.length > 0) {
                    datos.items.forEach(item => {
                        total += item.cantidad;
                    });
                }
                badge.innerText = total;
            })
            .catch(err => console.log('Error sincronizando carrito'));
    }
});
function agregarAlCarrito(productoId) {
    const parametros = new URLSearchParams(window.location.search);
    const puesto = parametros.get('puesto') || '';
    const ahora = new Date();
    const hora = ahora.getHours();
    const diaSemana = ahora.getDay();
    if (puesto === 'foodtruck') {
        if (hora < 10 || hora >= 18) {
            Swal.fire({
                icon: 'warning',
                title: 'Foodtruck Cerrado 🌙',
                text: 'El Foodtruck solo toma pedidos de 10:00 a 18:00 hs.',
                confirmButtonColor: '#dfb23e',
                background: 'var(--card-bg)',
                color: 'var(--text-color)'
            });
            return;
        }
    } else {
        if (diaSemana === 1 || diaSemana === 2) {
            if (hora < 8 || hora >= 21) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Buffet Cerrado 🌙',
                    text: 'Hoy tomamos pedidos de 08:00 a 21:00 hs. ¡Pero podés ir mirando el menú para tentarte!',
                    confirmButtonColor: '#dfb23e',
                    background: 'var(--card-bg)',
                    color: 'var(--text-color)'
                });
                return;
            }
        } else if (diaSemana === 3 || diaSemana === 4 || diaSemana === 5) {
            if (hora < 8 || hora >= 23) {
                 Swal.fire({
                     icon: 'warning',
                     title: 'Buffet Cerrado 🌙',
                     text: 'Hoy tomamos pedidos de 08:00 a 23:00 hs. ¡Pero podés ir mirando el menú para tentarte!',
                     confirmButtonColor: '#dfb23e',
                     background: 'var(--card-bg)',
                     color: 'var(--text-color)'
                 });
                 return;
            }
        } else {
            if (hora < 8 || hora >= 19) {
                 Swal.fire({
                     icon: 'warning',
                     title: 'Buffet Cerrado 🌙',
                     text: 'Hoy tomamos pedidos de 08:00 a 19:00 hs. ¡Pero podés ir mirando el menú para tentarte!',
                     confirmButtonColor: '#dfb23e',
                     background: 'var(--card-bg)',
                     color: 'var(--text-color)'
                 });
                 return;
            }
        }
    }
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
        if(datos.status === 'ok') {
            document.getElementById('badge-contador').innerText = datos.total_items;
            cargarDetalleCarrito();
        }
    });
}
function restarItem(llave) {
    fetch(`/carrito/restar/${llave}/`).then(res => res.json()).then(datos => {
        if(datos.status === 'ok') {
            document.getElementById('badge-contador').innerText = datos.total_items;
            cargarDetalleCarrito();
        }
    });
}
function eliminarItem(llave) {
    fetch(`/carrito/eliminar/${llave}/`).then(res => res.json()).then(datos => {
        if(datos.status === 'ok') {
            document.getElementById('badge-contador').innerText = datos.total_items;
            cargarDetalleCarrito();
        }
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
// # MÓDULO 2: CHECKOUT Y PREPARACIÓN DEL MODAL DE ENTREGA
// ==========================================================================

function abrirModalEntrega() {
    const total = document.getElementById('carrito-precio-total').innerText;
    if (total === '0.00' || total === '0') {
        Swal.fire({
            icon: 'info',
            title: 'Carrito Vacío',
            text: 'Agregá algo rico antes de confirmar tu pedido.',
            confirmButtonColor: '#1e7b45'
        });
        return;
    }
    const parametros = new URLSearchParams(window.location.search);
    const puestoActual = parametros.get('puesto') || '';
    const ahora = new Date();
    const hora = ahora.getHours();
    const diaSemana = ahora.getDay();
    if (puestoActual === 'foodtruck') {
        if (hora < 10 || hora >= 18) {
            Swal.fire({
                icon: 'warning',
                title: 'Foodtruck Cerrado 🌙',
                text: 'Solo tomamos pedidos de 10:00 a 18:00 hs.',
                confirmButtonColor: '#dfb23e',
                background: 'var(--card-bg)',
                color: 'var(--text-color)'
            });
            return;
        }
    } else {
        if (diaSemana === 1 || diaSemana === 2) {
            if (hora < 8 || hora >= 21) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Buffet Cerrado 🌙',
                    text: 'Hoy tomamos pedidos hasta las 21:00 hs.',
                    confirmButtonColor: '#dfb23e',
                    background: 'var(--card-bg)',
                    color: 'var(--text-color)'
                });
                return;
            }
        } else if (diaSemana === 3 || diaSemana === 4 || diaSemana === 5) {
            if (hora < 8 || hora >= 23) {
                 Swal.fire({
                     icon: 'warning',
                     title: 'Buffet Cerrado 🌙',
                     text: 'Hoy tomamos pedidos hasta las 23:00 hs.',
                     confirmButtonColor: '#dfb23e',
                     background: 'var(--card-bg)',
                     color: 'var(--text-color)'
                 });
                 return;
            }
        } else {
            if (hora < 8 || hora >= 19) {
                 Swal.fire({
                     icon: 'warning',
                     title: 'Buffet Cerrado 🌙',
                     text: 'Hoy tomamos pedidos hasta las 19:00 hs.',
                     confirmButtonColor: '#dfb23e',
                     background: 'var(--card-bg)',
                     color: 'var(--text-color)'
                 });
                 return;
            }
        }
    }
    cerrarCarrito();
    document.getElementById('modal-entrega').classList.add('activo');
    document.body.style.overflow = 'hidden';
    const labelMesa = document.getElementById('label-mesa');
    const radioMostrador = document.querySelector('input[name="tipo_entrega"][value="mostrador"]');
    const puestosSinMesa = ['kiosco', 'barra', 'parrilla', 'foodtruck'];
    if (puestosSinMesa.includes(puestoActual)) {
        if(labelMesa) labelMesa.style.display = 'none';
        if(radioMostrador) radioMostrador.checked = true;
    } else {
        if(labelMesa) labelMesa.style.display = 'block';
    }
    toggleFormularioMesa();
}
function cerrarModalEntrega() {
    document.getElementById('modal-entrega').classList.remove('activo');
    document.body.style.overflow = 'auto';
}
function toggleFormularioMesa() {
    const opcionMesa = document.querySelector('input[name="tipo_entrega"]:checked');
    const pagoEfectivo = document.querySelector('input[name="tipo_pago"]:checked');
    const formMesa = document.getElementById('form-mesa');
    const formTelefono = document.getElementById('form-telefono');
    if (formTelefono) {
        if (pagoEfectivo && pagoEfectivo.value === 'efectivo') {
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
    const totalTexto = document.getElementById('carrito-precio-total').innerText;
    const totalOriginal = parseFloat(totalTexto) || 0;
    let totalFinal = totalOriginal;
    const avisoDescuento = document.getElementById('modal-descuento-aviso');
    const modalTotalFinal = document.getElementById('modal-total-final');
    const modalTotalOriginal = document.getElementById('modal-total-original');
    const resumenPago = document.getElementById('resumen-pago');
    const descuentoActivo =
        resumenPago &&
        (
            resumenPago.dataset.descuentoActivo === '1' ||
            resumenPago.dataset.descuentoActivo === 'true'
        );

    const descuentoPorcentaje = resumenPago
        ? (parseFloat(resumenPago.dataset.descuentoPorcentaje || '0') || 0)
        : 0;

    if (descuentoActivo && descuentoPorcentaje > 0 && pagoEfectivo && pagoEfectivo.value === 'efectivo') {
        totalFinal = totalOriginal * (1 - (descuentoPorcentaje / 100));
        if(avisoDescuento) avisoDescuento.style.display = 'inline-block';
        if(modalTotalOriginal) {
            modalTotalOriginal.style.display = 'inline';
            modalTotalOriginal.innerText = '$' + totalOriginal.toFixed(2);
        }
    } else {
        if(avisoDescuento) avisoDescuento.style.display = 'none';
        if(modalTotalOriginal) modalTotalOriginal.style.display = 'none';
    }
    if (modalTotalFinal) {
        modalTotalFinal.innerText = '$' + totalFinal.toFixed(2);
    }
}
// ==========================================================================
// # MÓDULO 3: PROCESAMIENTO AJAX HACIA DJANGO Y MERCADO PAGO / NAVE / WA
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
        Swal.fire({
            icon: 'warning',
            title: 'Faltan datos',
            text: 'Por favor completá opciones de entrega y pago.',
            confirmButtonColor: '#1e7b45'
        });
        return;
    }
    const tipoEntrega = tipoEntregaElement.value;
    const tipoPago = tipoPagoElement.value;
    let numeroMesa = "";
    if (nombreCliente === "") {
        Swal.fire({
            icon: 'warning',
            title: 'Falta tu nombre',
            text: 'Escribí tu nombre y apellido para identificarte.',
            confirmButtonColor: '#1e7b45'
        });
        return;
    }
    if (tipoPago === 'efectivo' && telefonoCliente === "") {
        Swal.fire({
            icon: 'warning',
            title: 'Teléfono requerido',
            text: 'Por favor dejanos tu WhatsApp para coordinar el pago.',
            confirmButtonColor: '#1e7b45'
        });
        return;
    }
    if (tipoEntrega === 'mesa') {
        numeroMesa = document.getElementById('numero_mesa').value.trim();
        if (numeroMesa === "") {
            Swal.fire({
                icon: 'warning',
                title: 'Número de Mesa',
                text: 'Ingresá el número de mesa donde estás.',
                confirmButtonColor: '#1e7b45'
            });
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
    if (comentariosFinales !== "") {
        nombreCliente = `${nombreCliente} (Nota: ${comentariosFinales})`.substring(0, 99);
    }
    // 🔥 FIX DEL CARTEL TRANSPARENTE: Se actualizó background a var(--card-bg) 🔥
    Swal.fire({
        title: 'Procesando...',
        text: '¡Llevando el pedido a toda velocidad!',
        imageUrl: '/static/img/corriendo.gif',
        imageWidth: 120,
        showConfirmButton: false,
        allowOutsideClick: false,
        allowEscapeKey: false,
        background: 'var(--card-bg)',
        color: 'var(--text-color)'
    });
    const formData = new FormData();
    formData.append('nombre_cliente', nombreCliente);
    formData.append('telefono_cliente', telefonoCliente);
    formData.append('tipo_entrega', tipoEntrega);
    formData.append('numero_mesa', numeroMesa);
    formData.append('tipo_pago', tipoPago);
    fetch('/procesar/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
    .then(res => res.json())
    .then(datos => {
        if (datos.status === 'ok') {
            cerrarModalEntrega();
            if (tipoPago === 'mercadopago') {
                if (datos.mp_id) {
                    window.location.href = `https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=${datos.mp_id}`;
                } else {
                    Swal.fire({ icon: 'error', title: 'Error de cobro', text: 'El servidor no generó el link de Mercado Pago.', background: 'var(--card-bg)', color: 'var(--text-color)' });
                }
            } else if (tipoPago === 'nave') {
                if (datos.nave_url) {
                    window.location.href = datos.nave_url;
                } else {
                    Swal.fire({ title: '¡MODO / Nave!', text: 'Estamos terminando de configurar la conexión con Nave.', icon: 'info', confirmButtonColor: '#103b70', background: 'var(--card-bg)', color: 'var(--text-color)' });
                }
            } else if (tipoPago === 'efectivo') {
                let fraseUbicacion = tipoEntrega === 'mesa' ? `ando en la mesa ${numeroMesa}` : `pedí para retirar en el mostrador`;
                let mensajeWa = `Hola soy ${document.getElementById('nombre_cliente').value.trim()}, ${fraseUbicacion}, mi número de pedido es #${datos.pedido_id} y lo quiero confirmar para acercarme a pagarlo o avísame si me cobras cuando el pedido llegue a la mesa.`;
                let numeroBuffet = (window.STERAK_CONTACT_WHATSAPP || "").replace(/\D/g, "");
                let linkWa = numeroBuffet ? `https://wa.me/${numeroBuffet}?text=${encodeURIComponent(mensajeWa)}` : null;
                Swal.fire({
                    title: '¡Pedido Registrado!',
                    text: linkWa ? 'Tocá el botón para enviarnos un WhatsApp y confirmar el pedido.' : 'Tu pedido se registró correctamente.',
                    icon: 'success',
                    confirmButtonText: linkWa ? 'Enviar WhatsApp 💬' : 'Ver mi pedido',
                    confirmButtonColor: '#25D366',
                    allowOutsideClick: false,
                    background: 'var(--card-bg)',
                    color: 'var(--text-color)'
                }).then(() => {
                    if (linkWa) window.open(linkWa, '_blank');
                    setTimeout(() => {
                        window.location.href = `/seguimiento/${datos.pedido_id}/`;
                    }, 500);
                });
            } else {
                window.location.href = `/seguimiento/${datos.pedido_id}/`;
            }
        } else {
            Swal.fire({ icon: 'error', title: 'Oops...', text: "Error: " + datos.mensaje, background: 'var(--card-bg)', color: 'var(--text-color)' });
        }
    }).catch(error => {
        Swal.fire({ icon: 'error', title: 'Error de red', text: 'No se pudo conectar con el servidor.', background: 'var(--card-bg)', color: 'var(--text-color)' });
    });
}
// ==========================================================================

// # MÓDULO 4: CREADOR DINÁMICO DE DISEÑO VISUAL
//           OPCIONES SIN CONFLICTO ENTRE PRODUCTOS REPETIDOS
// ==========================================================================

function actualizarPrecioVisual(contenedor) {
    if (!contenedor) {
        return;
    }
    const tarjeta =
        contenedor.closest(
            '.tarjeta-producto'
        );
    if (!tarjeta) {
        return;
    }
    const precioElement =
        tarjeta.querySelector(
            '.precio'
        );
    if (!precioElement) {
        return;
    }
    if (
        !precioElement.dataset.precioOriginal
    ) {
        const precioBaseTexto =
            precioElement.innerText
                .replace('$', '')
                .replace(',', '.');
        precioElement.dataset.precioOriginal =
            parseFloat(
                precioBaseTexto
            );
    }
    let precioActual =
        parseFloat(
            precioElement.dataset.precioOriginal
        );
    contenedor
        .querySelectorAll(
            'input:checked'
        )
        .forEach(
            input => {
                const texto =
                    input.value;
                if (
                    texto.includes(
                        '(+'
                    )
                ) {
                    const extra =
                        parseFloat(
                            texto
                                .split('(+')[1]
                                .split(')')[0]
                        );
                    if (
                        !isNaN(extra)
                    ) {
                        precioActual +=
                            extra;
                    }
                }
                if (
                    texto.includes(
                        '(-'
                    )
                ) {
                    const descuento =
                        parseFloat(
                            texto
                                .split('(-')[1]
                                .split(')')[0]
                        );
                    if (
                        !isNaN(
                            descuento
                        )
                    ) {
                        precioActual -=
                            descuento;
                    }
                }
            }
        );
    precioElement.innerText =
        '$'
        +
        precioActual.toFixed(
            2
        );
    precioElement.style.transition =
        'all 0.3s ease';
    precioElement.style.transform =
        'scale(1.15)';
    precioElement.style.color =
        'var(--naranja-sterak)';
    setTimeout(
        () => {
            precioElement.style.transform =
                'scale(1)';
            precioElement.style.color =
                '';
        },
        300
    );
}
// ==========================================================================
// # Generar Opciones
// ==========================================================================
document.addEventListener(
    'DOMContentLoaded',
    function () {
        document
            .querySelectorAll(
                '.opciones-contenedor'
            )
            .forEach(
                (
                    contenedor,
                    indiceContenedor
                ) => {
                    const atributos = [
                        {
                            nombre:
                                'Variante',
                            valor:
                                contenedor.dataset.variante,
                            clave:
                                'variante',
                            tipo:
                                'radio'
                        },
                        {
                            nombre:
                                'Guarnición',
                            valor:
                                contenedor.dataset.guarnicion,
                            clave:
                                'guarnicion',
                            tipo:
                                'radio'
                        },
                        {
                            nombre:
                                'Punto de cocción',
                            valor:
                                contenedor.dataset.punto,
                            clave:
                                'punto',
                            tipo:
                                'radio'
                        },
                        {
                            nombre:
                                'Relleno',
                            valor:
                                contenedor.dataset.relleno,
                            clave:
                                'relleno',
                            tipo:
                                'radio'
                        },
                        {
                            nombre:
                                'Salsa',
                            valor:
                                contenedor.dataset.salsa,
                            clave:
                                'salsa',
                            tipo:
                                'radio'
                        },
                        {
                            nombre:
                                'Hielo',
                            valor:
                                contenedor.dataset.hielo,
                            clave:
                                'hielo',
                            tipo:
                                'radio'
                        },
                        {
                            nombre:
                                'Adicional',
                            valor:
                                contenedor.dataset.adicional,
                            clave:
                                'adicional',
                            tipo:
                                'checkbox'
                        }
                    ];
                    let tieneOpciones =
                        false;
                    const wrapper =
                        document.createElement(
                            'div'
                        );
                    wrapper.className =
                        'opciones-wrapper';
                    wrapper.style.display =
                        'none';
                    wrapper.style.flexDirection =
                        'column';
                    wrapper.style.gap =
                        '8px';
                    const tarjetaProducto =
                        contenedor.closest(
                            '.tarjeta-producto'
                        );
                    const nombreDelPlato =
                        tarjetaProducto
                            ?
                            tarjetaProducto
                                .querySelector('h3')
                                .innerText
                                .toLowerCase()
                            :
                            '';
                    const esPlatoDeHuevo =
                        nombreDelPlato.includes(
                            'omel'
                        )
                        ||
                        nombreDelPlato.includes(
                            'tortilla'
                        );
                    atributos.forEach(
                        attr => {
                            if (
                                attr.valor
                                &&
                                attr.valor.trim()
                                !==
                                ''
                            ) {
                                tieneOpciones =
                                    true;
                                const grupo =
                                    document.createElement(
                                        'div'
                                    );
                                grupo.className =
                                    'opciones-grupo grupo-'
                                    +
                                    attr.clave
                                    +
                                    '-'
                                    +
                                    contenedor.dataset.id;
                                grupo.dataset.clave =
                                    attr.clave;
                                grupo.dataset.requerido =
                                    (
                                        attr.tipo
                                        ===
                                        'radio'
                                    )
                                        ?
                                        'true'
                                        :
                                        'false';
                                const txtOpcional =
                                    (
                                        attr.tipo
                                        ===
                                        'checkbox'
                                    )
                                        ?
                                        ' (Opcional)'
                                        :
                                        '';
                                grupo.innerHTML =
                                    '<div class="opciones-titulo">'
                                    +
                                    'Elegí '
                                    +
                                    attr.nombre
                                    +
                                    txtOpcional
                                    +
                                    ':'
                                    +
                                    '</div>';
                                attr.valor
                                    .split(',')
                                    .forEach(
                                        opcion => {
                                            const label =
                                                document.createElement(
                                                    'label'
                                                );
                                            label.className =
                                                'opcion-item';
                                            const input =
                                                document.createElement(
                                                    'input'
                                                );
                                            input.type =
                                                attr.tipo;
                                            input.value =
                                                opcion.trim();
                                            // Cada copia del producto
                                            // tiene su propio grupo de radios.
                                            if (
                                                attr.tipo
                                                ===
                                                'radio'
                                            ) {
                                                input.name =
                                                    'radio-'
                                                    +
                                                    attr.clave
                                                    +
                                                    '-'
                                                    +
                                                    contenedor.dataset.id
                                                    +
                                                    '-'
                                                    +
                                                    indiceContenedor;
                                            } else {
                                                input.className =
                                                    'chk-adicional-'
                                                    +
                                                    contenedor.dataset.id;
                                            }
                                            input.addEventListener(
                                                'change',
                                                () => {
                                                    grupo
                                                        .classList
                                                        .remove(
                                                            'error'
                                                        );
                                                    actualizarPrecioVisual(
                                                        contenedor
                                                    );
                                                }
                                            );
                                            const marcador =
                                                document.createElement(
                                                    'div'
                                                );
                                            marcador.className =
                                                'opcion-marcador';
                                            label.appendChild(
                                                input
                                            );
                                            label.appendChild(
                                                marcador
                                            );
                                            label.appendChild(
                                                document.createTextNode(
                                                    opcion.trim()
                                                )
                                            );
                                            grupo.appendChild(
                                                label
                                            );
                                        }
                                    );
                                if (
                                    attr.clave
                                    ===
                                    'punto'
                                    &&
                                    !esPlatoDeHuevo
                                ) {
                                    const avisoParrilla =
                                        document.createElement(
                                            'div'
                                        );
                                    avisoParrilla.style.fontSize =
                                        '0.8rem';
                                    avisoParrilla.style.color =
                                        'var(--naranja-brillo)';
                                    avisoParrilla.style.fontWeight =
                                        'bold';
                                    avisoParrilla.style.marginTop =
                                        '4px';
                                    avisoParrilla.innerHTML =
                                        '⏱️ La carne tiene una espera de 20 a 40 min según cocción.';
                                    grupo.appendChild(
                                        avisoParrilla
                                    );
                                }
                                wrapper.appendChild(
                                    grupo
                                );
                            }
                        }
                    );
                    if (
                        tieneOpciones
                    ) {
                        const btnToggle =
                            document.createElement(
                                'button'
                            );
                        btnToggle.type =
                            'button';
                        btnToggle.className =
                            'btn-toggle-opciones';
                        btnToggle.innerHTML =
                            'Personalizar '
                            +
                            '<span class="icono-toggle">▼</span>';
                        btnToggle.addEventListener(
                            'click',
                            () => {
                                if (
                                    wrapper.style.display
                                    ===
                                    'none'
                                ) {
                                    wrapper.style.display =
                                        'flex';
                                    btnToggle.innerHTML =
                                        'Ocultar '
                                        +
                                        '<span class="icono-toggle">▲</span>';
                                    btnToggle
                                        .classList
                                        .add(
                                            'abierto'
                                        );
                                } else {
                                    wrapper.style.display =
                                        'none';
                                    btnToggle.innerHTML =
                                        'Personalizar '
                                        +
                                        '<span class="icono-toggle">▼</span>';
                                    btnToggle
                                        .classList
                                        .remove(
                                            'abierto'
                                        );
                                }
                            }
                        );
                        contenedor.appendChild(
                            btnToggle
                        );
                        contenedor.appendChild(
                            wrapper
                        );
                    }
                }
            );
    }
);
// ==========================================================================
// # Agregar Producto Con Sus Opciones
// ==========================================================================
function agregarConOpciones(
    productoId,
    boton
) {
    // IMPORTANTE:
    // Ya no buscamos el producto en toda la página.
    // Buscamos dentro de la tarjeta exacta cuyo botón se tocó.
    const tarjeta =
        boton.closest(
            '.tarjeta-producto'
        );
    if (!tarjeta) {
        return;
    }
    const contenedor =
        tarjeta.querySelector(
            '.opciones-contenedor[data-id="'
            +
            productoId
            +
            '"]'
        );
    if (!contenedor) {
        return;
    }
    const parametrosActuales =
        new URLSearchParams(
            window.location.search
        );
    const puesto =
        parametrosActuales.get(
            'puesto'
        )
        ||
        '';
    let fetchParams =
        new URLSearchParams();
    if (puesto) {
        fetchParams.append(
            'puesto',
            puesto
        );
    }
    let faltanOpciones =
        false;
    let teniaPuntoDeCoccion =
        false;
    const tarjetaProducto =
        contenedor.closest(
            '.tarjeta-producto'
        );
    const nombreDelPlato =
        tarjetaProducto
            ?
            tarjetaProducto
                .querySelector('h3')
                .innerText
                .toLowerCase()
            :
            '';
    const esPlatoDeHuevo =
        nombreDelPlato.includes(
            'omel'
        )
        ||
        nombreDelPlato.includes(
            'tortilla'
        );
    contenedor
        .querySelectorAll(
            '.opciones-grupo'
        )
        .forEach(
            grupo => {
                const clave =
                    grupo.dataset.clave;
                const esRequerido =
                    grupo.dataset.requerido
                    ===
                    'true';
                if (
                    esRequerido
                ) {
                    const inputSeleccionado =
                        grupo.querySelector(
                            'input[type="radio"]:checked'
                        );
                    if (
                        !inputSeleccionado
                    ) {
                        grupo
                            .classList
                            .add(
                                'error'
                            );
                        faltanOpciones =
                            true;
                    } else {
                        grupo
                            .classList
                            .remove(
                                'error'
                            );
                        fetchParams.append(
                            clave,
                            inputSeleccionado.value
                        );
                        if (
                            clave
                            ===
                            'punto'
                            &&
                            !esPlatoDeHuevo
                        ) {
                            teniaPuntoDeCoccion =
                                true;
                        }
                    }
                } else if (
                    clave
                    ===
                    'adicional'
                ) {
                    let adicionalesElegidos =
                        [];
                    grupo
                        .querySelectorAll(
                            'input[type="checkbox"]:checked'
                        )
                        .forEach(
                            chk => {
                                adicionalesElegidos
                                    .push(
                                        chk.value
                                    );
                            }
                        );
                    if (
                        adicionalesElegidos.length
                        >
                        0
                    ) {
                        fetchParams.append(
                            'adicional',
                            adicionalesElegidos.join(
                                ' + '
                            )
                        );
                    }
                }
            }
        );
    // ======================================================================
    // # FALTAN OPCIONES
    // ======================================================================
    if (
        faltanOpciones
    ) {
        const wrapper =
            contenedor.querySelector(
                '.opciones-wrapper'
            );
        const btnToggle =
            contenedor.querySelector(
                '.btn-toggle-opciones'
            );
        if (
            wrapper
            &&
            wrapper.style.display
            ===
            'none'
        ) {
            wrapper.style.display =
                'flex';
            if (
                btnToggle
            ) {
                btnToggle.innerHTML =
                    'Ocultar '
                    +
                    '<span class="icono-toggle">▲</span>';
                btnToggle
                    .classList
                    .add(
                        'abierto'
                    );
            }
        }
        Swal.fire(
            {
                icon:
                    'error',
                title:
                    'Falta seleccionar opciones',
                text:
                    'Por favor, seleccioná las opciones marcadas en rojo.',
                confirmButtonColor:
                    '#ff6600'
            }
        );
        return;
    }
    // ======================================================================
    // # AGREGAR AL CARRITO
    // ======================================================================
    const urlFinal =
        '/carrito/agregar/'
        +
        productoId
        +
        '/?'
        +
        fetchParams.toString();
    const textoOriginal =
        boton.innerText;
    boton.innerText =
        'Cargando...';
    boton.disabled =
        true;
    fetch(
        urlFinal
    )
        .then(
            response =>
                response.json()
        )
        .then(
            data => {
                boton.disabled =
                    false;
                if (
                    data.status
                    ===
                    'ok'
                ) {
                    if (
                        teniaPuntoDeCoccion
                    ) {
                        Swal.fire(
                            {
                                icon:
                                    'info',
                                title:
                                    '¡Marchando a la Parrilla! 🥩',
                                text:
                                    'Recordá que la carne tiene un tiempo de espera de 20 a 40 minutos según el punto de cocción elegido.',
                                confirmButtonColor:
                                    '#ff6600',
                                timer:
                                    5000
                            }
                        );
                    }
                    boton.innerText =
                        '¡Agregado! ✔';
                    boton.style.backgroundColor =
                        'var(--naranja-sterak)';
                    boton.style.color =
                        '#000';
                    // Limpiamos únicamente esta tarjeta.
                    contenedor
                        .querySelectorAll(
                            'input'
                        )
                        .forEach(
                            input => {
                                input.checked =
                                    false;
                            }
                        );
                    actualizarPrecioVisual(
                        contenedor
                    );
                    const wrapper =
                        contenedor.querySelector(
                            '.opciones-wrapper'
                        );
                    const btnToggle =
                        contenedor.querySelector(
                            '.btn-toggle-opciones'
                        );
                    if (
                        wrapper
                    ) {
                        wrapper.style.display =
                            'none';
                    }
                    if (
                        btnToggle
                    ) {
                        btnToggle.innerHTML =
                            'Personalizar '
                            +
                            '<span class="icono-toggle">▼</span>';
                        btnToggle
                            .classList
                            .remove(
                                'abierto'
                            );
                    }
                    setTimeout(
                        () => {
                            boton.innerText =
                                textoOriginal;
                            boton.style.backgroundColor =
                                '';
                            boton.style.color =
                                '';
                        },
                        1500
                    );
                    const badge =
                        document.getElementById(
                            'badge-contador'
                        );
                    if (
                        badge
                    ) {
                        badge.innerText =
                            data.total_items;
                    }
                    const carritoSidebar =
                        document.getElementById(
                            'carrito-sidebar'
                        );
                    if (
                        carritoSidebar
                        &&
                        carritoSidebar
                            .classList
                            .contains(
                                'abierto'
                            )
                    ) {
                        cargarDetalleCarrito();
                    }
                } else {
                    boton.innerText =
                        textoOriginal;
                    Swal.fire(
                        {
                            icon:
                                'error',
                            title:
                                'No se pudo agregar',
                            text:
                                data.mensaje
                                ||
                                'Intentá nuevamente.'
                        }
                    );
                }
            }
        )
        .catch(
            error => {
                console.error(
                    'Error agregando producto:',
                    error
                );
                boton.disabled =
                    false;
                boton.innerText =
                    textoOriginal;
                Swal.fire(
                    {
                        icon:
                            'error',
                        title:
                            'Error de conexión',
                        text:
                            'No se pudo agregar el producto al carrito.'
                    }
                );
            }
        );
}
// ==========================================================================
// # MÓDULO 5: DASHBOARD, PANEL DE CONTROL Y ADMINISTRACIÓN AJAX
// ==========================================================================

function abrirTab(tabId, btnElement) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-btn, .panel-tab-btn').forEach(el => el.classList.remove('active', 'is-active'));
    const tabSeleccionada = document.getElementById('tab-' + tabId);
    if(tabSeleccionada) tabSeleccionada.style.display = 'block';
    if(btnElement) {
        btnElement.classList.add('active');
    } else {
        const btnActivo = document.getElementById('btn-tab-' + tabId);
        if(btnActivo) btnActivo.classList.add('active');
    }
    localStorage.setItem('tabDashboardActiva', tabId);
}
document.addEventListener("DOMContentLoaded", function() {
    if(document.querySelector('.dash-tabs') || document.querySelector('.panel-tabs')) {
        let tabURL = new URLSearchParams(window.location.search).get('tab');
        let tabGuardada = tabURL && document.getElementById('tab-' + tabURL) ? tabURL : (localStorage.getItem('tabDashboardActiva') || 'inicio');
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
            confirmButtonText: 'Sí, cancelar pedido',
            background: 'var(--card-bg)',
            color: 'var(--text-color)'
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
                if(etiqueta) {
                    etiqueta.innerText = 'Cancelado';
                    etiqueta.style.background = 'var(--error, #dc3545)';
                    etiqueta.style.color = 'white';
                    etiqueta.className = "badge-estado badge-cancelado";
                }
                if(contenedorBotones) contenedorBotones.style.display = 'none';
            } else if (nuevoEstado === 'listo') {
                tr.style.borderLeft = '5px solid var(--verde-sanmartin, #28a745)';
                if(etiqueta) {
                    etiqueta.innerText = '¡Listo!';
                    etiqueta.style.background = 'var(--verde-sanmartin, #28a745)';
                    etiqueta.style.color = 'white';
                    etiqueta.className = "badge-estado badge-listo";
                }
            } else if (nuevoEstado === 'entregado') {
                tr.style.opacity = '0.5';
                tr.style.borderLeft = '5px solid var(--texto-mutado, #6c757d)';
                if(etiqueta) {
                    etiqueta.innerText = 'Entregado';
                    etiqueta.style.background = 'var(--texto-mutado, #6c757d)';
                    etiqueta.style.color = 'white';
                    etiqueta.className = "badge-estado badge-entregado";
                }
                if(contenedorBotones) contenedorBotones.style.display = 'none';
            } else if (nuevoEstado === 'demorado') {
                if(etiqueta) {
                    etiqueta.innerText = 'Demorado';
                    etiqueta.style.background = '#fd7e14';
                    etiqueta.style.color = 'white';
                }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = 'auto';
            } else {
                if(etiqueta) {
                    etiqueta.innerText = 'En Preparación';
                    etiqueta.style.background = 'var(--azul-sanmartin, #007bff)';
                    etiqueta.style.color = 'white';
                    etiqueta.className = "badge-estado badge-preparacion";
                }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = 'auto';
            }
        }
    }).catch(error => {
        elemento.innerHTML = textoOriginal;
        elemento.style.pointerEvents = 'auto';
        Swal.fire({ icon: 'error', title: 'Oops...', text: 'Hubo un error de conexión.', background: 'var(--card-bg)', color: 'var(--text-color)' });
    });
}
function editarPrecioAjax(event, form) {
    event.preventDefault();

    const boton = form.querySelector('button');
    const input = form.querySelector('input[name="precio"]');
    const textoOriginal = boton ? boton.innerText : 'OK';

    if (boton) {
        boton.disabled = true;
        boton.innerText = '...';
    }

    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('No se pudo actualizar el precio.');
        }
        return response.json().catch(() => ({ status: 'ok' }));
    })
    .then(data => {
        if (data.status && data.status !== 'ok') {
            throw new Error(data.mensaje || 'No se pudo actualizar el precio.');
        }

        if (boton) {
            boton.innerText = '✓';
            boton.style.background = 'var(--verde-sanmartin)';
            boton.style.color = '#fff';
        }

        if (input) {
            input.blur();
        }

        setTimeout(() => {
            if (boton) {
                boton.innerText = textoOriginal;
                boton.style.background = '';
                boton.style.color = '';
                boton.disabled = false;
            }
        }, 900);
    })
    .catch(error => {
        if (boton) {
            boton.innerText = textoOriginal;
            boton.disabled = false;
        }

        Swal.fire({
            icon: 'error',
            title: 'No se pudo cambiar el precio',
            text: error.message,
            background: 'var(--card-bg)',
            color: 'var(--text-color)'
        });
    });
}

function cambiarDisponibilidadAjax(event, el) {
    event.preventDefault();
    fetch(el.href, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(res => res.json())
    .then(data => {
        const fila = el.closest('.fila-producto-menu') || el.closest('tr');
        if (fila) {
            fila.classList.toggle('is-pausado', !data.disponible);
            fila.style.opacity = '';
            const estado = fila.querySelector('.menu-admin-estado');
            if (estado) {
                estado.classList.toggle('is-activo', data.disponible);
                estado.classList.toggle('is-pausado', !data.disponible);
                estado.textContent = data.disponible ? '● ACTIVO' : '● PAUSADO';
            }
        }
        el.innerText = data.disponible ? '⏸ Pausar' : '▶ Activar';
        if (el.classList.contains('menu-admin-btn')) {
            el.classList.toggle('is-pausar', data.disponible);
            el.classList.toggle('is-activar', !data.disponible);
        } else {
            el.className = data.disponible ? 'btn-panel btn-gris' : 'btn-panel btn-verde';
        }
    });
}
function eliminarProductoAjax(event, el) {
    event.preventDefault();
    Swal.fire({
        title: '¿Borrar producto?',
        text: 'Desaparecerá del menú permanentemente.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Borrar',
        cancelButtonText: 'Cancelar',
        background: 'var(--card-bg)',
        color: 'var(--text-color)'
    }).then((result) => {
        if (!result.isConfirmed) return;
        fetch(el.href, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
        .then(() => {
            const fila = el.closest('.fila-producto-menu') || el.closest('tr');
            if (!fila) return;
            fila.style.transition = '0.3s';
            fila.style.opacity = '0';
            setTimeout(() => {
                const categoria = fila.closest('.categoria-menu');
                fila.remove();
                if (categoria && !categoria.querySelector('.fila-producto-menu')) {
                    categoria.remove();
                }
                if (typeof aplicarFiltrosMenuAdmin === 'function') {
                    aplicarFiltrosMenuAdmin();
                }
            }, 300);
        });
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
function actualizarPuestosAjax(event, form) {
    event.preventDefault();
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: {'X-Requested-With': 'XMLHttpRequest'} })
    .then(() => {
        form.style.backgroundColor = "rgba(40, 167, 69, 0.1)";
        setTimeout(() => form.style.backgroundColor = "transparent", 800);
    })
    .catch(error => Swal.fire({ icon: 'error', title: 'Oops...', text: 'Hubo un error al guardar.', background: 'var(--card-bg)', color: 'var(--text-color)' }));
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
        document.getElementById('btn-instalar-nav').style.display = 'inline-flex';
    } else if (isIOS) {
        // Safari/iOS no ofrece beforeinstallprompt.
        alert("Para instalar la aplicación: tocá Compartir y elegí 'Agregar a pantalla de inicio'.");
    } else {
        // En algunos navegadores el evento de instalación no está disponible.
        alert("Si tu navegador permite instalar esta web, abrí su menú (⋮ o ⋯) y elegí 'Instalar app' o 'Agregar a pantalla de inicio'.");
    }
});
window.addEventListener('appinstalled', () => { document.getElementById('btn-instalar-nav').textContent = 'App instalada'; });
// ==========================================================================
// # SELECTOR DE CATEGORÍAS BUSCABLE
// ========================================================================== 

function sincronizarSelectorCategoria(select) {
    if (!select || !select._categoriaPicker) return;

    const opcion = select.options[select.selectedIndex];
    const texto = opcion && opcion.value
        ? opcion.textContent.trim()
        : 'Elegí una categoría';

    select._categoriaPicker.label.textContent = texto;

    select._categoriaPicker.items.forEach(item => {
        item.classList.toggle(
            'is-selected',
            String(item.dataset.value) === String(select.value)
        );
    });
}

function inicializarSelectorCategoria(select) {
    if (!select || select.dataset.categoriaPickerInicializado === '1') return;

    select.dataset.categoriaPickerInicializado = '1';
    select.classList.add('categoria-select-native');

    const picker = document.createElement('div');
    picker.className = 'categoria-picker';

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'categoria-picker__trigger';
    trigger.innerHTML = '<span>Elegí una categoría</span><b>⌄</b>';

    const panel = document.createElement('div');
    panel.className = 'categoria-picker__panel';
    panel.hidden = true;

    const search = document.createElement('input');
    search.type = 'search';
    search.className = 'categoria-picker__search';
    search.placeholder = 'Buscar categoría...';
    search.autocomplete = 'off';

    const list = document.createElement('div');
    list.className = 'categoria-picker__list';

    const items = [];

    Array.from(select.options).forEach(opcion => {
        if (!opcion.value) return;

        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'categoria-picker__item';
        item.dataset.value = opcion.value;
        item.dataset.busqueda = normalizarTextoMenuAdmin(opcion.textContent);
        item.textContent = opcion.textContent.trim();

        item.addEventListener('click', function() {
            select.value = item.dataset.value;
            select.dispatchEvent(new Event('change', {bubbles: true}));
            panel.hidden = true;
            picker.classList.remove('is-open');
        });

        items.push(item);
        list.appendChild(item);
    });

    search.addEventListener('input', function() {
        const texto = normalizarTextoMenuAdmin(search.value);
        items.forEach(item => {
            item.hidden = Boolean(texto) && !item.dataset.busqueda.includes(texto);
        });
    });

    trigger.addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();

        const abrir = panel.hidden;

        document.querySelectorAll('.categoria-picker.is-open').forEach(otro => {
            if (otro !== picker) {
                otro.classList.remove('is-open');
                const otroPanel = otro.querySelector('.categoria-picker__panel');
                if (otroPanel) otroPanel.hidden = true;
            }
        });

        panel.hidden = !abrir;
        picker.classList.toggle('is-open', abrir);

        if (abrir) {
            search.value = '';
            items.forEach(item => item.hidden = false);
            window.setTimeout(() => search.focus(), 30);
        }
    });

    picker.addEventListener('click', event => event.stopPropagation());

    panel.appendChild(search);
    panel.appendChild(list);
    picker.appendChild(trigger);
    picker.appendChild(panel);
    select.insertAdjacentElement('afterend', picker);

    select._categoriaPicker = {
        picker: picker,
        panel: panel,
        label: trigger.querySelector('span'),
        search: search,
        items: items
    };

    select.addEventListener('change', function() {
        sincronizarSelectorCategoria(select);
    });

    sincronizarSelectorCategoria(select);
}

function cerrarSelectoresCategoria() {
    document.querySelectorAll('.categoria-picker.is-open').forEach(picker => {
        picker.classList.remove('is-open');
        const panel = picker.querySelector('.categoria-picker__panel');
        if (panel) panel.hidden = true;
    });
}

document.addEventListener('click', cerrarSelectoresCategoria);

// ==========================================================================
// # MÓDULO 5B: GESTOR VISUAL DEL MENÚ EN EL DASHBOARD
// ==========================================================================
let filtroPuestoMenuAdmin = 'todos';

function normalizarTextoMenuAdmin(valor) {
    return String(valor || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function filtrarMenu(puestoId, btnActivo) {
    filtroPuestoMenuAdmin = String(puestoId || 'todos');
    document.querySelectorAll('.menu-admin-filtro').forEach(btn => {
        btn.classList.remove('is-active');
    });
    if (btnActivo) {
        btnActivo.classList.add('is-active');
    }
    aplicarFiltrosMenuAdmin();
}

function aplicarFiltrosMenuAdmin() {
    const buscador = document.getElementById('buscador-menu-admin');
    const texto = normalizarTextoMenuAdmin(buscador ? buscador.value : '');
    let totalVisibles = 0;

    document.querySelectorAll('.categoria-menu').forEach(categoria => {
        let visiblesCategoria = 0;
        categoria.querySelectorAll('.fila-producto-menu').forEach(fila => {
            const puestos = String(fila.dataset.puestos || '')
                .split(',')
                .map(valor => valor.trim())
                .filter(Boolean);
            const busqueda = normalizarTextoMenuAdmin(fila.dataset.busqueda || fila.innerText);
            const coincidePuesto = filtroPuestoMenuAdmin === 'todos' || puestos.includes(filtroPuestoMenuAdmin);
            const coincideTexto = !texto || busqueda.includes(texto);
            const visible = coincidePuesto && coincideTexto;
            fila.hidden = !visible;
            if (visible) {
                visiblesCategoria++;
                totalVisibles++;
            }
        });
        categoria.hidden = visiblesCategoria === 0;
    });

    const sinResultados = document.getElementById('menu-admin-sin-resultados');
    if (sinResultados) {
        sinResultados.hidden = totalVisibles !== 0;
    }
}

function actualizarAvisoCategoriaSalon() {
    const select = document.getElementById('editor-categoria');
    const aviso = document.getElementById('editor-aviso-salon');
    if (!select || !aviso) return;
    const opcion = select.options[select.selectedIndex];
    const esSalon = opcion && normalizarTextoMenuAdmin(opcion.textContent) === 'salon';
    aviso.hidden = !esSalon;
}

function actualizarPreviewEditorProducto(url) {
    const preview = document.getElementById('editor-imagen-preview');
    if (!preview) return;
    preview.innerHTML = '';
    if (!url) {
        const texto = document.createElement('span');
        texto.textContent = 'Sin imagen';
        preview.appendChild(texto);
        return;
    }
    const imagen = document.createElement('img');
    imagen.src = url;
    imagen.alt = 'Imagen actual del producto';
    preview.appendChild(imagen);
}

function abrirEditorProducto(boton) {
    const modal = document.getElementById('modal-editor-producto');
    const form = document.getElementById('form-editor-producto');
    if (!modal || !form || !boton) return;

    form.action = boton.dataset.url || '';
    form.dataset.modo = 'editar';
    document.getElementById('editor-producto-titulo').textContent = 'Editar producto';
    const botonGuardarEditor = document.getElementById('btn-guardar-editor-producto');
    if (botonGuardarEditor) botonGuardarEditor.textContent = '💾 Guardar cambios';
    document.getElementById('editor-nombre').value = boton.dataset.nombre || '';
    document.getElementById('editor-codigo').value = boton.dataset.codigo || '';
    const editorCategoria = document.getElementById('editor-categoria');
    editorCategoria.value = boton.dataset.categoria || '';
    editorCategoria.dispatchEvent(new Event('change', {bubbles: true}));
    document.getElementById('editor-precio').value = boton.dataset.precio || '';
    document.getElementById('editor-orden').value = boton.dataset.orden || '0';
    document.getElementById('editor-descripcion').value = boton.dataset.descripcion || '';
    document.getElementById('editor-disponible').checked = boton.dataset.disponible === '1';
    document.getElementById('editor-promo').checked = boton.dataset.promo === '1';
    document.getElementById('editor-variantes').value = boton.dataset.variantes || '';
    document.getElementById('editor-guarniciones').value = boton.dataset.guarniciones || '';
    document.getElementById('editor-coccion').value = boton.dataset.coccion || '';
    document.getElementById('editor-rellenos').value = boton.dataset.rellenos || '';
    document.getElementById('editor-salsas').value = boton.dataset.salsas || '';
    document.getElementById('editor-adicionales').value = boton.dataset.adicionales || '';
    document.getElementById('editor-hielo').value = boton.dataset.hielo || '';

    const puntosSeleccionados = String(boton.dataset.puestos || '')
        .split(',')
        .map(valor => valor.trim())
        .filter(Boolean);

    document.querySelectorAll('#editor-puntos-venta input[name="puntos_venta"]').forEach(input => {
        input.checked = puntosSeleccionados.includes(String(input.value));
    });

    const inputImagen = document.getElementById('editor-imagen');
    if (inputImagen) inputImagen.value = '';
    actualizarPreviewEditorProducto(boton.dataset.imagen || '');
    actualizarAvisoCategoriaSalon();

    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('menu-editor-abierto');

    window.setTimeout(() => {
        const nombre = document.getElementById('editor-nombre');
        if (nombre) {
            nombre.focus();
            nombre.select();
        }
    }, 60);
}

function cerrarEditorProducto() {
    const modal = document.getElementById('modal-editor-producto');
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('menu-editor-abierto');
}

// v161: actualizá solo los productos en el panel; la pestaña y la búsqueda permanecen intactas.
async function refrescarListadoMenuSinRecargar() {
    const listado = document.getElementById('menu-admin-categorias');
    if (!listado) return;
    const abiertos = new Set(Array.from(listado.querySelectorAll('details[open] .menu-admin-categoria__titulo'))
        .map(el => el.textContent.trim()));
    const respuesta = await fetch('/dashboard/?tab=menu', {
        credentials: 'same-origin', cache: 'no-store', headers: {'X-Requested-With': 'XMLHttpRequest'}
    });
    if (!respuesta.ok) throw new Error('No se pudo actualizar la lista visual de productos.');
    const documento = new DOMParser().parseFromString(await respuesta.text(), 'text/html');
    const nuevo = documento.getElementById('menu-admin-categorias');
    if (!nuevo) throw new Error('No se pudo recuperar el menú; quizás venció tu sesión.');
    const scroll = {x: window.scrollX, y: window.scrollY};
    listado.replaceChildren(...Array.from(nuevo.children).map(el => document.importNode(el, true)));
    listado.querySelectorAll('details').forEach(details => {
        const titulo = details.querySelector('.menu-admin-categoria__titulo');
        details.open = !!(titulo && abiertos.has(titulo.textContent.trim()));
    });
    // Se vuelven a aplicar filtros y búsqueda, sin tocar inputs ni navegación.
    if (typeof aplicarFiltrosMenuAdmin === 'function') aplicarFiltrosMenuAdmin();
    if (typeof window.filtrarMenu === 'function') {
        const activo = document.querySelector('.menu-admin-filtro.is-active');
        if (activo) window.filtrarMenu(activo.dataset.puesto || 'todos', activo);
    }
    window.scrollTo(scroll.x, scroll.y);
}
function mensajeMenuGuardado(mensaje, icono) {
    if (window.Swal) Swal.fire({toast:true,position:'top-end',icon: icono || 'success',title:mensaje,
        timer:2600,showConfirmButton:false,background:'var(--card-bg)',color:'var(--text-color)'});
}
function abrirNuevoProducto() {
    const form = document.getElementById('form-editor-producto');
    const modal = document.getElementById('modal-editor-producto');
    const boton = document.querySelector('[data-url-nuevo]');
    if (!form || !modal || !boton) return;
    form.reset();
    form.action = boton.dataset.urlNuevo;
    form.dataset.modo = 'nuevo';
    document.getElementById('editor-producto-titulo').textContent = 'Agregar producto';
    const guardar = document.getElementById('btn-guardar-editor-producto');
    if (guardar) guardar.textContent = '💾 Guardar y agregar otro';
    document.querySelectorAll('#editor-puntos-venta input[name="puntos_venta"]').forEach(el => {el.checked = false;});
    const imagen = document.getElementById('editor-imagen');
    if (imagen) imagen.value = '';
    actualizarPreviewEditorProducto('');
    actualizarAvisoCategoriaSalon();
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden','false');
    document.body.classList.add('menu-editor-abierto');
    window.setTimeout(() => document.getElementById('editor-nombre')?.focus(), 60);
}

function guardarEditorProducto(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const boton = document.getElementById('btn-guardar-editor-producto');
    const puntosMarcados = form.querySelectorAll('input[name="puntos_venta"]:checked');

    if (!puntosMarcados.length) {
        Swal.fire({
            icon: 'warning',
            title: 'Elegí un mostrador',
            text: 'El producto tiene que estar asignado al menos a un punto de venta.',
            background: 'var(--card-bg)',
            color: 'var(--text-color)',
            confirmButtonColor: 'var(--dorado-sanmartin)'
        });
        return;
    }

    const textoOriginal = boton ? boton.innerHTML : '';
    if (boton) {
        boton.disabled = true;
        boton.innerHTML = '⏳ Guardando...';
    }

    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(async response => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== 'ok') {
            throw new Error(data.mensaje || 'No se pudo guardar el producto.');
        }
        return data;
    })
    .then(async (datos) => {
        localStorage.setItem('tabDashboardActiva', 'menu');
        let aviso = 'Producto guardado. Seguís en el mismo lugar.';
        try {
            await refrescarListadoMenuSinRecargar();
        } catch(error) {
            // El POST ya fue exitoso: no pedir reenvío ni informar falso fallo de guardado.
            aviso = 'Guardado. No se pudo actualizar la lista; revisala después.';
        }
        if (form.dataset.modo === 'nuevo') {
            form.reset();
            document.getElementById('editor-imagen').value = '';
            actualizarPreviewEditorProducto('');
            actualizarAvisoCategoriaSalon();
            document.getElementById('editor-nombre').focus({preventScroll:true});
        }
        mensajeMenuGuardado(aviso, 'success');
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: 'No se pudo guardar',
            text: error.message || 'Revisá los datos e intentá nuevamente.',
            background: 'var(--card-bg)',
            color: 'var(--text-color)',
            confirmButtonColor: 'var(--dorado-sanmartin)'
        });
    })
    .finally(() => {
        if (boton) {
            boton.disabled = false;
            boton.innerHTML = textoOriginal;
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const buscador = document.getElementById('buscador-menu-admin');
    if (buscador) {
        buscador.addEventListener('input', aplicarFiltrosMenuAdmin);
    }

    const categoria = document.getElementById('editor-categoria');
    if (categoria) {
        categoria.addEventListener('change', actualizarAvisoCategoriaSalon);
    }

    const imagen = document.getElementById('editor-imagen');
    if (imagen) {
        imagen.addEventListener('change', function() {
            const archivo = imagen.files && imagen.files[0];
            if (!archivo) return;
            const lector = new FileReader();
            lector.onload = function() {
                actualizarPreviewEditorProducto(lector.result);
            };
            lector.readAsDataURL(archivo);
        });
    }

    const formEditor = document.getElementById('form-editor-producto');
    if (formEditor) {
        formEditor.addEventListener('submit', guardarEditorProducto);
    }

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modal = document.getElementById('modal-editor-producto');
            if (modal && modal.classList.contains('is-open')) {
                cerrarEditorProducto();
            }
        }
    });

    document.querySelectorAll('#id_categoria, #editor-categoria, select[data-categoria-select]').forEach(
        inicializarSelectorCategoria
    );

    aplicarFiltrosMenuAdmin();
});


// ==========================================================================
// # MÓDULO 6: CONTROL DE MODO OSCURO / CLARO
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
// # MÓDULO 7: CIERRE DE CAJA Y ESTADÍSTICAS POR MOSTRADOR
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
                        } else { htmlProductos = '<span style="color: var(--texto-mutado); font-size: 0.85rem;">Sin productos vendidos.</span>'; }
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
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>💳 Débito:</span> <strong>$${m.debito.toLocaleString('es-AR')}</strong></div>
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
        }).catch(error => console.error("Error al obtener cierre:", error));
}
function cerrarCierreCaja() { document.getElementById('modalCierre').classList.remove('activo'); }
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
    }).then((result) => { if (result.isConfirmed) { window.location.href = "/dashboard/eliminar-todo/"; } });
}
// ==========================================================================
// # MÓDULO 8: LÓGICA DE MESAS (AGRUPACIÓN MÁGICA Y SEGURA)
// ==========================================================================


function renderizarMesas() {
    const grid = document.getElementById('grid-mesas');
    if (!grid) return;

    let mesas = {};

    function parseMonto(valor) {
        let texto = String(valor || '0')
            .replace(/\$/g, '')
            .replace(/\s/g, '')
            .trim();

        if (texto.includes(',') && texto.includes('.')) {
            texto = texto.replace(/\./g, '').replace(',', '.');
        } else if (texto.includes(',')) {
            texto = texto.replace(',', '.');
        }

        const numero = parseFloat(texto);
        return Number.isFinite(numero) ? numero : 0;
    }

    document.querySelectorAll('.fila-pedido').forEach(function (fila) {
        const estado = String(
            fila.dataset.estado ||
            (fila.querySelector('.badge-estado') ? fila.querySelector('.badge-estado').innerText : '')
        ).toLowerCase();

        if (
            estado.includes('cancelado') ||
            estado.includes('entregado')
        ) {
            return;
        }

        const pago = String(
            fila.dataset.pago ||
            (fila.querySelector('td:first-child') ? fila.querySelector('td:first-child').innerText : '')
        ).toLowerCase();

        if (!pago.includes('efectivo')) {
            return;
        }

        let numMesa = String(fila.dataset.mesa || '').trim();

        if (!numMesa) {
            const detalle = fila.querySelector('.order-details-box');
            const textoDetalle = detalle ? detalle.textContent : fila.textContent;
            const matchMesa = textoDetalle.match(/\(Mesa\s+([^)]+)\)/i) || textoDetalle.match(/Mesa\s+([0-9A-Za-z_-]+)/i);
            if (matchMesa) {
                numMesa = String(matchMesa[1] || '').trim();
            }
        }

        if (!numMesa) {
            return;
        }

        const total = parseMonto(
            fila.dataset.total ||
            (fila.querySelector('td:nth-child(3)') ? fila.querySelector('td:nth-child(3)').innerText : '0')
        );

        const idPedido = (fila.id || '').replace('pedido-', '');

        if (!mesas[numMesa]) {
            mesas[numMesa] = {
                total: 0,
                pedidos: []
            };
        }

        mesas[numMesa].total += total;

        if (idPedido) {
            mesas[numMesa].pedidos.push(idPedido);
        }
    });

    grid.innerHTML = '';

    const numerosMesa = Object.keys(mesas).sort(function (a, b) {
        const na = parseInt(a, 10);
        const nb = parseInt(b, 10);

        if (Number.isFinite(na) && Number.isFinite(nb)) {
            return na - nb;
        }

        return String(a).localeCompare(String(b), 'es');
    });

    if (numerosMesa.length === 0) {
        grid.innerHTML = '<div class="mesa-empty">No hay mesas activas con pagos en efectivo por el momento.</div>';
        return;
    }

    numerosMesa.forEach(function (mesa) {
        const data = mesas[mesa];
        const cuentaSalon = obtenerCuentaSalonGuardada(mesa);
        const mozoMesa = cuentaSalon && cuentaSalon.mozo_nombre
            ? cuentaSalon.mozo_nombre
            : 'Sin asignar';

        grid.innerHTML += `
            <div class="mesa-card">
                <div class="mesa-header">
                    <h3 class="mesa-titulo">🍽️ Mesa ${mesa}</h3>
                    <span class="mesa-badge">${data.pedidos.length} Pedido/s</span>
                </div>
                <div class="mesa-mozo">🧑‍🍳 ${mozoMesa}</div>
                <div class="mesa-total">$${data.total.toLocaleString('es-AR', {minimumFractionDigits: 2})}</div>
                <div class="mesa-acciones">
                    <button onclick="dividirCuenta('${mesa}', ${data.total})" class="btn-panel btn-amarillo" style="flex: 1; padding: 12px; font-size: 1rem; border-radius: 8px;">➗ Dividir</button>
                    <button onclick="cobrarMesa('${mesa}', '${data.pedidos.join(',')}')" class="btn-panel btn-verde" style="flex: 1; padding: 12px; font-size: 1rem; border-radius: 8px;">💵 Cobrar</button>
                </div>
            </div>
        `;
    });
}

function dividirCuenta(mesa, total) {
    Swal.fire({
        title: `Mesa ${mesa} - Dividir Cuenta`,
        text: `El total de la mesa es $${total.toLocaleString('es-AR')}`,
        input: 'number',
        inputAttributes: { min: 2, max: 20, step: 1 },
        inputLabel: '¿Entre cuántas personas dividimos?',
        inputValue: 2,
        showCancelButton: true,
        confirmButtonColor: 'var(--azul-sanmartin)',
        confirmButtonText: 'Calcular',
        cancelButtonText: 'Cancelar',
        background: 'var(--card-bg)',
        color: 'var(--text-color)'
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            const personas = parseInt(result.value);
            const porCabeza = (total / personas).toFixed(2);
            Swal.fire({ icon: 'info', title: `Tienen que poner $${parseFloat(porCabeza).toLocaleString('es-AR')} c/u`, text: `(Dividido en ${personas} personas)`, confirmButtonColor: 'var(--verde-sanmartin)', background: 'var(--card-bg)', color: 'var(--text-color)' });
        }
    });
}
function cobrarMesa(mesa, pedidosStr) {
    Swal.fire({
        title: `¿Cobrar Mesa ${mesa}?`,
        text: "Se marcarán como Entregados y Cobrados todos los pedidos acumulados de esta mesa.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: 'var(--verde-sanmartin)',
        cancelButtonColor: 'var(--texto-mutado)',
        confirmButtonText: 'Sí, cobrar la mesa',
        cancelButtonText: 'Cancelar',
        background: 'var(--card-bg)',
        color: 'var(--text-color)'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({title: 'Cobrando mesa...', showConfirmButton: false, background: 'var(--card-bg)', color: 'var(--text-color)'});
            const pedidos = pedidosStr.split(',');
            let fetchPromises = pedidos.map(id => {
                const fila = document.getElementById(`pedido-${id}`);
                if (!fila) return Promise.resolve();
                const aTag = fila.querySelector('td:last-child a');
                if (!aTag) {
                    fila.style.opacity = '0.5';
                    fila.style.display = 'none';
                    return Promise.resolve();
                }
                let baseHref = aTag.getAttribute('href');
                let parts = baseHref.split('/');
                parts[parts.length - 2] = 'entregado';
                const finalUrl = parts.join('/');
                return fetch(finalUrl, { headers: {'X-Requested-With': 'XMLHttpRequest'} })
                    .then(res => res.json())
                    .then(data => {
                        if(data.status === 'ok') {
                            fila.style.opacity = '0.5';
                            fila.style.display = 'none';
                            const badge = fila.querySelector('.badge-estado');
                            if(badge) { badge.innerText = "Entregado"; }
                        }
                    });
            });
            Promise.all(fetchPromises).then(() => {
                Swal.fire({ icon: 'success', title: '¡Mesa Cobrada!', text: `La mesa ${mesa} ya fue liquidada.`, confirmButtonColor: 'var(--verde-sanmartin)', background: 'var(--card-bg)', color: 'var(--text-color)' });
                renderizarMesas();
            });
        }
    });
}

// ==========================================================================
// # MÓDULO 8B: OPINIONES Y SUGERENCIAS DE CLIENTES
// ==========================================================================

function abrirModalOpinion() {
    const modal = document.getElementById('modal-opinion');
    if (!modal) return;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
}

function cerrarModalOpinion() {
    const modal = document.getElementById('modal-opinion');
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
}

function obtenerCsrfDashboard() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('form-opinion');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        event.preventDefault();

        const boton = document.getElementById('btn-enviar-opinion');
        const textoOriginal = boton ? boton.innerHTML : '';
        if (boton) {
            boton.disabled = true;
            boton.innerHTML = 'Enviando...';
        }

        fetch(form.action || '/opinion/enviar/', {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(async function(response) {
            const data = await response.json().catch(function() { return {}; });
            if (!response.ok || data.status !== 'ok') {
                throw new Error(data.mensaje || 'No se pudo enviar el comentario.');
            }
            return data;
        })
        .then(function() {
            form.reset();
            cerrarModalOpinion();
            Swal.fire({
                icon: 'success',
                title: '¡Gracias por contarnos!',
                text: 'Tu comentario fue enviado de forma privada.',
                confirmButtonColor: 'var(--verde-sanmartin)',
                background: 'var(--card-bg)',
                color: 'var(--text-color)'
            });
        })
        .catch(function(error) {
            Swal.fire({
                icon: 'error',
                title: 'No se pudo enviar',
                text: error.message,
                background: 'var(--card-bg)',
                color: 'var(--text-color)'
            });
        })
        .finally(function() {
            if (boton) {
                boton.disabled = false;
                boton.innerHTML = textoOriginal;
            }
        });
    });
});

function marcarOpinionLeida(opinionId, url) {
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': obtenerCsrfDashboard(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.status !== 'ok') return;
        const tarjeta = document.getElementById('opinion-' + opinionId);
        if (!tarjeta) return;
        tarjeta.classList.remove('is-nueva');
        const badge = tarjeta.querySelector('.opinion-nueva-badge');
        if (badge) badge.remove();
        const boton = tarjeta.querySelector('.opinion-btn--leida');
        if (boton) boton.remove();
    });
}

function eliminarOpinion(opinionId, url) {
    Swal.fire({
        title: '¿Eliminar comentario?',
        text: 'No se puede recuperar después.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Eliminar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: 'var(--error)',
        background: 'var(--card-bg)',
        color: 'var(--text-color)'
    }).then(function(resultado) {
        if (!resultado.isConfirmed) return;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': obtenerCsrfDashboard(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.status !== 'ok') return;
            const tarjeta = document.getElementById('opinion-' + opinionId);
            if (tarjeta) {
                tarjeta.style.opacity = '0';
                window.setTimeout(function() { tarjeta.remove(); }, 250);
            }
        });
    });
}

// ==========================================================================
// MÓDULO 9: POS DE SALÓN - TECLADO, COMANDA Y PAGO PARCIAL
// ==========================================================================

(function () {
    "use strict";
    var root = document.getElementById("salon-pos");
    if (!root) {
        return;
    }
    var productosData = document.getElementById("salon-productos-data");
    var productos = [];
    try {
        productos = JSON.parse(productosData ? productosData.textContent : "[]");
    }
    catch (error) {
        console.error("No se pudieron leer los productos del sal\u00F3n:", error);
        productos = [];
    }
    productos = productos.map(function (producto) {
        return {
            id: Number(producto.id || 0),
            codigo: String(producto.codigo || producto.codigo_rapido || producto.id || ""),
            nombre: String(producto.nombre || "Producto"),
            precio: Number(producto.precio || 0),
            es_salon: Boolean(producto.es_salon)
        };
    });

    // SM v111: cambios de precio/código del editor disponibles al instante
    // para consumos NUEVOS. Las líneas ya agregadas mantienen el importe original.
    window.addEventListener('salon-catalogo-actualizado', function (event) {
        var item = event.detail || {};
        var id = Number(item.id);
        if (!id) return;
        productos = productos.filter(function (p) {
            return p.id !== id;
        });
        if (item.disponible) {
            productos.push({
                id: id,
                codigo: String(item.codigo || id),
                nombre: String(item.nombre || 'Producto'),
                precio: Number(item.precio || 0),
                es_salon: item.es_salon !== false
            });
        }
    });

    var mozosData = document.getElementById("salon-mozos-data");
    var mozos = [];
    try {
        mozos = JSON.parse(mozosData ? mozosData.textContent : "[]");
    }
    catch (error) {
        console.error("No se pudieron leer los mozos del sal\u00F3n:", error);
        mozos = [];
    }
    mozos = mozos.map(function (mozo) {
        return {
            id: Number(mozo.id || 0),
            nombre: String(mozo.nombre || "")
        };
    }).filter(function (mozo) {
        return (mozo.id && mozo.nombre);
    });
    var mozosNumerados = mozos.map(function (mozo, indice) {
        return {
            id: mozo.id,
            nombre: mozo.nombre,
            numero: indice + 1,
            etiqueta: (indice + 1) + '. ' + mozo.nombre
        };
    });
    window.addEventListener('sm-mozos-modificados', function(event){
        var detalle=event.detail||{}, mozo=detalle.mozo||{};
        if (detalle.accion==='agregar' && mozo.id) {
            mozos.push({id:Number(mozo.id),nombre:String(mozo.nombre||'')});
        } else if (detalle.accion==='eliminar') {
            mozos=mozos.filter(function(m){return Number(m.id)!==Number(mozo.id);});
        }
        mozos.sort(function(a,b){return a.nombre.localeCompare(b.nombre,'es');});
        mozosNumerados=mozos.map(function(m,i){return {id:m.id,nombre:m.nombre,numero:i+1,etiqueta:(i+1)+'. '+m.nombre};});
        reconstruirSelectorMozos();
    });
    // Clientes activos para el cobro a cuenta corriente.
    var cuentasCorrientesPOS = [];
    try {
        var cuentasData = document.getElementById('salon-cuentas-corrientes-data');
        cuentasCorrientesPOS = JSON.parse(cuentasData ? cuentasData.textContent : '[]');
    } catch (error) {
        console.warn('No se pudieron cargar los clientes de cuenta corriente', error);
    }
    var pedidosWebData = document.getElementById('salon-pedidos-web-data');
    var pedidosWebIniciales = [];
    try { pedidosWebIniciales = JSON.parse(pedidosWebData ? pedidosWebData.textContent : '[]'); }
    catch (error) { console.warn('No se pudo leer pedidos web de mesa',error); }
    // El servidor local guarda otra copia de las mesas para recuperarlas incluso
    // si se borra el almacenamiento del navegador. Una sola terminal de edición.
    var respaldoUrl = root.getAttribute('data-backup-url') || '';
    var respaldoPreparado = !respaldoUrl;
    var respaldoBloqueado = false;
    var respaldoVersion = 0;
    var respaldoPendiente = false;
    var respaldoGuardando = false;
    var respaldoTimer = null;
    var estadoGuardado = document.getElementById('sm-local-save-state');
    if (respaldoUrl) root.style.pointerEvents = 'none';
    function indicarRespaldo(mensaje, fallo) {
        if (estadoGuardado) {
            estadoGuardado.textContent = mensaje;
            estadoGuardado.classList.toggle('is-error', !!fallo);
        }
    }
    function bloquearRespaldo(texto) {
        if (respaldoBloqueado) return;
        respaldoBloqueado = true;
        root.style.pointerEvents = 'none';
        indicarRespaldo('ATENCIÓN: guardado de mesas detenido', true);
        // No se puede seguir cobrando sin un respaldo consistente.
        Swal.fire({icon:'error',title:'Protección de las mesas',
            text:texto + ' No continúes operando desde esta ventana. Recargá y revisá las mesas.',
            confirmButtonText:'Entendido',allowOutsideClick:false,
            background:'var(--card-bg)',color:'var(--text-color)'});
    }
    function enviarRespaldo() {
        if (!respaldoUrl || !respaldoPreparado || respaldoBloqueado ||
            respaldoGuardando || !respaldoPendiente) return;
        if (respaldoTimer) { clearTimeout(respaldoTimer); respaldoTimer=null; }
        respaldoPendiente = false;
        respaldoGuardando = true;
        var copia = JSON.parse(JSON.stringify(cuentas));
        indicarRespaldo('Guardando mesas en esta PC...');
        fetch(respaldoUrl,{method:'POST',credentials:'same-origin',
            headers:{'Content-Type':'application/json','X-CSRFToken':obtenerCsrf()},
            body:JSON.stringify({version:respaldoVersion,cuentas:copia})})
        .then(function(res){
            return res.json().catch(function(){return {};}).then(function(d){
                if (!res.ok || d.status !== 'ok') {
                    throw new Error(d.mensaje || 'No se pudo guardar en esta PC.');
                }
                respaldoVersion = Number(d.version);
                indicarRespaldo('Mesas respaldadas en esta PC · versión '+respaldoVersion);
            });
        }).catch(function(err){ bloquearRespaldo(err.message); })
        .finally(function(){
            respaldoGuardando = false;
            if (respaldoPendiente && !respaldoBloqueado) enviarRespaldo();
        });
    }
    function programarRespaldo() {
        if (!respaldoUrl || !respaldoPreparado || respaldoBloqueado) return;
        respaldoPendiente = true;
        if (respaldoTimer) clearTimeout(respaldoTimer);
        respaldoTimer = setTimeout(enviarRespaldo,250);
    }
    function esperarRespaldoAntesDeCobrar() {
        if (!respaldoUrl) return Promise.resolve();
        if (!respaldoPreparado || respaldoBloqueado)
            return Promise.reject(new Error('El respaldo de mesas no está disponible.'));
        enviarRespaldo();
        return new Promise(function(resolve,reject){
            function comprobar(){
                if (respaldoBloqueado) return reject(new Error('Fallo al guardar las mesas en esta PC.'));
                if (!respaldoGuardando && !respaldoPendiente) return resolve();
                setTimeout(comprobar,70);
            }
            comprobar();
        });
    }
    var storageKey = "sistemasm_salon_cuentas_v2";
    var storageAnteriores = [
        "sistemasm_salon_cuentas_v1",
        "sistemasm_salon_cuentas_v0",
        "sterakfood_salon_cuentas_v5",
        "sterakfood_salon_cuentas_v4",
        "sterakfood_salon_cuentas_v3",
        "sterakfood_salon_cuentas_v2",
        "sterakfood_salon_cuentas_v1",
        "shortyfood_pos_salon_v2"
    ];
    var mesaActualKey = "sistemasm_salon_mesa_actual_v2";
    var cuentas = cargarCuentas();
    var mesaActual = cargarUltimaMesa();
    var sugerencias = [];
    var sugerenciaActiva = -1;
    var enviando = false;
    var modoParcial = false;
    var filaTeclado = 0;
    var botonesMesa = Array.prototype.slice.call(document.querySelectorAll(".salon-pos__mesa"));
    var inputMesaRapida = document.getElementById("input-mesa-rapida");
    var tituloMesa = document.getElementById("titulo-mesa");
    var estadoMesa = document.getElementById("estado-mesa");
    var selectorMozoMesa = document.getElementById("selector-mozo-mesa");
    var mensajeSeleccionar = document.getElementById("mensaje-seleccionar-mesa");
    var areaComanda = document.getElementById("area-comanda");
    var inputCant = document.getElementById("input-cant");
    var buscador = document.getElementById("buscador");
    var listaSugerencias = document.getElementById("lista-sugerencias");
    var listaComanda = document.getElementById("lista-comanda");
    var listaVacia = document.getElementById("salon-lista-vacia");
    var totalCuenta = document.getElementById("total-cuenta");
    var cantidadLineas = document.getElementById("cantidad-lineas");
    var resumenAccion = document.getElementById("resumen-accion");
    var totalSeleccionado = document.getElementById("total-seleccionado");
    var btnParcial = document.getElementById("btn-pago-parcial");
    var btnAccion = document.getElementById("btn-accion-principal");
    var btnTicket = document.getElementById("btn-imprimir-mesa");
    var modalComanda = document.getElementById("salon-comanda-modal");
    var modalOverlay = document.getElementById("salon-modal-overlay");
    var btnCerrarComanda = document.getElementById("btn-cerrar-comanda");
    var btnCerrarComandaInferior = document.getElementById("btn-cerrar-comanda-inferior");
    reconstruirSelectorMozos();
    function cargarCuentas() {
        var claves = [
            storageKey
        ].concat(storageAnteriores);
        for (var i = 0; i < claves.length; i++) {
            try {
                var guardado = localStorage.getItem(claves[i]);
                if (!guardado) {
                    continue;
                }
                var datos = JSON.parse(guardado);
                if (datos && typeof datos === "object") {
                    if (claves[i] !== storageKey) {
                        localStorage.setItem(storageKey, JSON.stringify(datos));
                    }
                    return datos;
                }
            }
            catch (error) {
                console.warn("No se pudo recuperar el sal\u00F3n:", error);
            }
        }
        return {};
    }
    function cargarUltimaMesa() {
        var claves = [
            mesaActualKey,
            "sistemasm_salon_mesa_actual_v1"
        ];
        for (var i = 0; i < claves.length; i++) {
            try {
                var guardada = localStorage.getItem(claves[i]);
                if (guardada) {
                    return String(guardada);
                }
            }
            catch (error) {
                console.warn("No se pudo recuperar la \u00FAltima mesa:", error);
            }
        }
        return null;
    }
    function guardar() {
        // El respaldo al servidor se agenda INDEPENDIENTEMENTE de localStorage.
        programarRespaldo();
        try {
            localStorage.setItem(storageKey, JSON.stringify(cuentas));
            if (mesaActual) {
                localStorage.setItem(mesaActualKey, String(mesaActual));
            }
        }
        catch (error) {
            console.error("No se pudo guardar el sal\u00F3n:", error);
        }
    }
    function borrarMesaActualGuardada() {
        try {
            localStorage.removeItem(mesaActualKey);
            localStorage.removeItem("sistemasm_salon_mesa_actual_v1");
        }
        catch (error) {
            console.warn("No se pudo limpiar la mesa actual:", error);
        }
    }
    function normalizarCuenta(numeroMesa) {
        var clave = String(numeroMesa);
        if (!cuentas[clave] || !Array.isArray(cuentas[clave].items)) {
            cuentas[clave] = {
                items: [],
                total: 0,
                mozo_id: null,
                mozo_nombre: ""
            };
        }
        if (!Object.prototype.hasOwnProperty.call(cuentas[clave], "mozo_id")) {
            cuentas[clave].mozo_id = null;
        }
        if (!Object.prototype.hasOwnProperty.call(cuentas[clave], "mozo_nombre")) {
            cuentas[clave].mozo_nombre = "";
        }
        cuentas[clave].items = cuentas[clave].items.filter(function (item) {
            return (item && Number(item.cantidad || 0) > 0);
        }).map(function (item) {
            var cantidad = Number(item.cantidad || 1);
            var cantPagar = Number(item.cant_pagar || 1);
            if (cantidad < 1) {
                cantidad = 1;
            }
            if (cantPagar < 1) {
                cantPagar = 1;
            }
            if (cantPagar > cantidad) {
                cantPagar = cantidad;
            }
            return {
                producto_id: Number(item.producto_id || item.id || 0),
                codigo: String(item.codigo || ""),
                nombre: String(item.nombre || "Producto"),
                precio: Number(item.precio || 0),
                cantidad: cantidad,
                seleccionado: Boolean(item.seleccionado),
                cant_pagar: cantPagar,
                origen: String(item.origen || ''),
                pedido_id: Number(item.pedido_id || 0),
                detalle_id: Number(item.detalle_id || 0)
            };
        });
        recalcular(cuentas[clave]);
        return cuentas[clave];
    }
    // Pedidos del menú público se fusionan por ID: NO se crean ventas POS duplicadas.
    // Evitar redibujar las 100 mesas y escribir localStorage si el servidor devolvió
    // exactamente las mismas cantidades, productos y precios que en la consulta previa.
    var ultimaFirmaPedidosWebSalon = null;
    function sincronizarPedidosWebSalon(itemsWeb) {
        if (!Array.isArray(itemsWeb)) return;
        var firma = JSON.stringify(itemsWeb.map(function (web) {
            return [Number(web.detalle_id || 0), String(web.mesa || ''),
                Number(web.cantidad || 0), Number(web.precio || 0),
                Number(web.producto_id || 0), String(web.codigo || ''),
                String(web.nombre || '')];
        }).sort(function (a, b) { return a[0] - b[0]; }));
        if (firma === ultimaFirmaPedidosWebSalon) return;
        var pendientes = new Map();
        itemsWeb.forEach(function (web) {
            var id = Number(web.detalle_id || 0);
            var mesa = String(web.mesa || '').trim();
            if (id && mesa) pendientes.set(id, web);
        });
        Object.keys(cuentas).forEach(function (clave) {
            var cuenta = normalizarCuenta(clave);
            cuenta.items = cuenta.items.filter(function (item) {
                return item.origen !== 'web' || pendientes.has(Number(item.detalle_id || 0));
            });
            recalcular(cuenta);
        });
        pendientes.forEach(function (web, detalleId) {
            var mesa = String(web.mesa || '').trim();
            var cuenta = normalizarCuenta(mesa);
            var existente = cuenta.items.find(function (item) {
                return item.origen === 'web' && Number(item.detalle_id) === detalleId;
            });
            var cantidad = Math.max(1, Number(web.cantidad || 1));
            if (existente) {
                existente.cantidad = cantidad;
                existente.cant_pagar = Math.max(1, Math.min(Number(existente.cant_pagar || 1), cantidad));
                existente.precio = Number(web.precio || 0);
                existente.nombre = String(web.nombre || 'Producto');
            } else {
                cuenta.items.push({
                    producto_id: Number(web.producto_id || 0),codigo: String(web.codigo || ''),
                    nombre: String(web.nombre || 'Producto'),precio: Number(web.precio || 0),
                    cantidad: cantidad,seleccionado: false,cant_pagar: 1,
                    origen: 'web',pedido_id: Number(web.pedido_id || 0),detalle_id: detalleId
                });
            }
            recalcular(cuenta);
        });
        ultimaFirmaPedidosWebSalon = firma;
        guardar();
        if (mesaActual) render();
        else actualizarMesas();
    }
    var consultaPedidosWebActiva = false;
    function refrescarPedidosWebSalon() {
        var url = root.getAttribute('data-web-pedidos-url');
        // Una sola consulta a la vez. No llenar Render de peticiones pendientes.
        if (!url || consultaPedidosWebActiva || enviando || modoParcial || document.hidden) return;
        consultaPedidosWebActiva = true;
        var controlador = new AbortController();
        var vencimiento = window.setTimeout(function () { controlador.abort(); }, 12000);
        fetch(url, {credentials:'same-origin',cache:'no-store',signal:controlador.signal})
          .then(function (resp) {
              if (!resp.ok) throw new Error('No se pudo sincronizar salón (HTTP ' + resp.status + ')');
              return resp.json();
          })
          .then(function (resp) { if (resp.status === 'ok') sincronizarPedidosWebSalon(resp.items); })
          .catch(function (error) {
              console.warn('Sincronización de pedidos web:',
                  error.name === 'AbortError' ? 'la consulta excedió 12 segundos' : error.message);
          })
          .finally(function () {
              window.clearTimeout(vencimiento);
              consultaPedidosWebActiva = false;
          });
    }

    function cuentaActual() {
        if (!mesaActual) {
            return null;
        }
        return normalizarCuenta(mesaActual);
    }
    function recalcular(cuenta) {
        cuenta.total = cuenta.items.reduce(function (total, item) {
            return (total + Number(item.precio || 0) * Number(item.cantidad || 0));
        }, 0);
    }
    function limpiarSeleccion(cuenta) {
        if (!cuenta) {
            return;
        }
        cuenta.items.forEach(function (item) {
            item.seleccionado = false;
            item.cant_pagar = 1;
        });
    }
    function dinero(valor) {
        return ("$" + Number(valor || 0).toLocaleString("es-AR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }));
    }
    function escapar(valor) {
        return String(valor || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
    function modalEstaAbierto() {
        return Boolean(modalComanda && modalComanda.classList.contains("is-open"));
    }
    // Nunca devolver el teclado a Mesa rápida mientras la comanda esté abierta.
    function enfocarMesaRapida() {
        window.setTimeout(function () {
            if (!inputMesaRapida || modalEstaAbierto() ||
                (window.Swal && typeof Swal.isVisible === "function" && Swal.isVisible())) return;
            inputMesaRapida.value = "";
            inputMesaRapida.focus({preventScroll: true});
            inputMesaRapida.select();
        }, 70);
    }
    function obtenerMozoPorId(mozoId) {
        var id = Number(mozoId || 0);
        return mozosNumerados.find(function (item) {
            return Number(item.id) === id;
        }) || null;
    }
    function obtenerMozoPorNumero(numeroMozo) {
        var numero = Number(numeroMozo || 0);
        return mozosNumerados.find(function (item) {
            return Number(item.numero) === numero;
        }) || null;
    }
    function reconstruirSelectorMozos() {
        if (!selectorMozoMesa) return;
        var actual = selectorMozoMesa.value || '';
        var html = ['<option value="">Sin asignar</option>'];
        mozosNumerados.forEach(function (mozo) {
            html.push('<option value="' + mozo.id + '" data-numero="' + mozo.numero + '">' + escapar(mozo.etiqueta) + '</option>');
        });
        selectorMozoMesa.innerHTML = html.join('');
        if (actual && selectorMozoMesa.querySelector('option[value="' + actual + '"]')) {
            selectorMozoMesa.value = actual;
        }
    }
    function abrirSelectorMozoMesa(numeroMesa, cuenta) {
        if (!mozosNumerados.length) {
            finalizarAperturaMesa(cuenta);
            return;
        }
        var opcionesSelect = ['<option value="">Elegí un mozo...</option>'];
        mozosNumerados.forEach(function (mozo) {
            opcionesSelect.push('<option value="' + mozo.id + '" data-numero="' + mozo.numero + '">' + escapar(mozo.etiqueta) + '</option>');
        });
        Swal.fire({
            title: 'Mesa ' + numeroMesa,
            html:
                '<div class="salon-mozo-popup">' +
                    '<p class="salon-mozo-popup__texto">¿Qué mozo atiende esta mesa?</p>' +
                    '<div class="salon-mozo-popup__grid">' +
                        '<div class="salon-mozo-popup__campo">' +
                            '<label for="swal-mozo-numero">Número de mozo</label>' +
                            '<input id="swal-mozo-numero" class="swal2-input salon-mozo-popup__input" inputmode="numeric" autocomplete="off" placeholder="Ej: 1">' +
                        '</div>' +
                        '<div class="salon-mozo-popup__campo">' +
                            '<label for="swal-mozo-select">O elegir de la lista</label>' +
                            '<select id="swal-mozo-select" class="swal2-select salon-mozo-popup__select">' + opcionesSelect.join('') + '</select>' +
                        '</div>' +
                    '</div>' +
                    '<div class="salon-mozo-popup__ayuda">Podés escribir el número del mozo o elegirlo de la lista.</div>' +
                '</div>',
            showCancelButton: true,
            confirmButtonText: 'Abrir mesa',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: 'var(--verde-sanmartin)',
            background: 'var(--card-bg)',
            color: 'var(--text-color)',
            customClass: {
                popup: 'salon-mozo-popup__swal'
            },
            didOpen: function () {
                var popup = Swal.getPopup();
                if (!popup) return;
                var inputNumero = popup.querySelector('#swal-mozo-numero');
                var selectMozo = popup.querySelector('#swal-mozo-select');
                if (inputNumero) {
                    inputNumero.focus();
                    inputNumero.select();
                    inputNumero.addEventListener('input', function () {
                        this.value = this.value.replace(/\D+/g, '');
                        var encontrado = obtenerMozoPorNumero(this.value);
                        selectMozo.value = encontrado ? String(encontrado.id) : '';
                    });
                    inputNumero.addEventListener('keydown', function (event) {
                        if (event.key === 'Enter') {
                            event.preventDefault();
                            Swal.clickConfirm();
                        }
                    });
                }
                if (selectMozo) {
                    selectMozo.addEventListener('change', function () {
                        var elegido = obtenerMozoPorId(this.value);
                        if (elegido && inputNumero) {
                            inputNumero.value = String(elegido.numero);
                        }
                    });
                }
            },
            preConfirm: function () {
                var popup = Swal.getPopup();
                var inputNumero = popup.querySelector('#swal-mozo-numero');
                var selectMozo = popup.querySelector('#swal-mozo-select');
                var numero = (inputNumero && inputNumero.value || '').trim();
                var idElegido = (selectMozo && selectMozo.value || '').trim();
                var mozo = numero ? obtenerMozoPorNumero(numero) : obtenerMozoPorId(idElegido);
                if (!mozo) {
                    Swal.showValidationMessage('Ingresá un número válido o elegí un mozo de la lista.');
                    return false;
                }
                return mozo.id;
            }
        }).then(function (resultado) {
            if (!resultado.isConfirmed) {
                mesaActual = null;
                borrarMesaActualGuardada();
                enfocarMesaRapida();
                return;
            }
            asignarMozoCuenta(cuenta, resultado.value);
            finalizarAperturaMesa(cuenta);
        });
    }
    function enfocarCantidad() {
        window.setTimeout(function () {
            if (!modalEstaAbierto() || !inputCant) return;
            inputCant.focus({preventScroll: true});
            inputCant.select();
        }, 30);
    }
    // Bloquea los controles que están detrás de la comanda (también para Tab).
    // No se aplica al resto del documento para permitir los avisos SweetAlert.
    var fondoInerteComanda = [];
    function bloquearFondoComanda() {
        fondoInerteComanda = [];
        Array.prototype.forEach.call(root.children, function (elemento) {
            if (elemento === modalComanda || elemento === modalOverlay) return;
            fondoInerteComanda.push({elemento: elemento, anterior: elemento.inert});
            elemento.inert = true;
        });
    }
    function restaurarFondoComanda() {
        fondoInerteComanda.forEach(function (registro) { registro.elemento.inert = registro.anterior; });
        fondoInerteComanda = [];
    }
    function hayAlertaSobreComanda() {
        return !!(window.Swal && typeof Swal.isVisible === "function" && Swal.isVisible());
    }
    function abrirComanda() {
        if (!modalComanda) return;
        modalComanda.classList.add("is-open");
        modalComanda.setAttribute("aria-hidden", "false");
        if (modalOverlay) {
            modalOverlay.classList.add("is-open");
            modalOverlay.setAttribute("aria-hidden", "false");
        }
        bloquearFondoComanda();
        document.body.style.overflow = "hidden";
        // Foco inmediato + otro después de mostrar el modal para evitar que
        // un botón de la grilla se lo vuelva a llevar al fondo.
        if (inputCant) inputCant.focus({preventScroll: true});
        enfocarCantidad();
    }
    // Si otro script devuelve accidentalmente el foco al fondo, recuperarlo.
    document.addEventListener('focusin', function (event) {
        if (!modalEstaAbierto() || !modalComanda || hayAlertaSobreComanda()) return;
        if (modalComanda.contains(event.target)) return;
        if (inputCant && !document.activeElement.closest('.swal2-container')) {
            inputCant.focus({preventScroll: true});
        }
    });
    // Tab queda en la comanda, no en los botones de mesas del fondo.
    document.addEventListener('keydown', function (event) {
        if (!modalEstaAbierto() || !modalComanda || hayAlertaSobreComanda() || event.key !== 'Tab') return;
        var elementos = Array.prototype.filter.call(modalComanda.querySelectorAll(
            'input:not([disabled]),select:not([disabled]),button:not([disabled]),a[href]'
        ), function (el) { return el.getClientRects().length > 0; });
        if (!elementos.length) return;
        var primero = elementos[0], ultimo = elementos[elementos.length - 1];
        if (event.shiftKey && document.activeElement === primero) {event.preventDefault(); ultimo.focus();}
        else if (!event.shiftKey && document.activeElement === ultimo) {event.preventDefault(); primero.focus();}
    }, true);
    function cerrarComanda() {
        cerrarSugerencias();
        modoParcial = false;
        filaTeclado = 0;
        var cuenta = cuentaActual();
        limpiarSeleccion(cuenta);
        guardar();
        if (modalComanda) {
            modalComanda.classList.remove("is-open");
            modalComanda.setAttribute("aria-hidden", "true");
        }
        if (modalOverlay) {
            modalOverlay.classList.remove("is-open");
            modalOverlay.setAttribute("aria-hidden", "true");
        }
        restaurarFondoComanda();
        document.body.style.overflow = "";
        actualizarMesas();
        enfocarMesaRapida();
    }
    function actualizarSelectorMozo(cuenta) {
        if (!selectorMozoMesa)
            return;
        selectorMozoMesa.value = cuenta && cuenta.mozo_id ? String(cuenta.mozo_id) : "";
    }
    function finalizarAperturaMesa(cuenta) {
        modoParcial = false;
        filaTeclado = 0;
        limpiarSeleccion(cuenta);
        tituloMesa.textContent = "Mesa " + mesaActual;
        estadoMesa.textContent = cuenta.mozo_nombre ? "MESA " + mesaActual + " \u00B7 " + cuenta.mozo_nombre : "MESA " + mesaActual;
        actualizarSelectorMozo(cuenta);
        mensajeSeleccionar.hidden = true;
        mensajeSeleccionar.classList.add("is-hidden");
        areaComanda.hidden = false;
        guardar();
        actualizarMesas();
        render();
        abrirComanda();
    }
    function asignarMozoCuenta(cuenta, mozoId) {
        var mozo = obtenerMozoPorId(mozoId);
        if (!mozo) {
            cuenta.mozo_id = null;
            cuenta.mozo_nombre = "";
        }
        else {
            cuenta.mozo_id = mozo.id;
            cuenta.mozo_nombre = mozo.nombre;
        }
        guardar();
        estadoMesa.textContent = cuenta.mozo_nombre ? "MESA " + mesaActual + " \u00B7 " + cuenta.mozo_nombre : "MESA " + mesaActual;
        actualizarMesas();
    }
    function seleccionarMesa(numero) {
        var numeroStr = String(numero || "").trim();
        var numeroInt = parseInt(numeroStr, 10);
        if (!numeroStr || isNaN(numeroInt) || numeroInt < 1 || numeroInt > 100) {
            Swal.fire({
                icon: "warning",
                title: "Mesa inv\u00E1lida",
                text: "Ingres\u00E1 una mesa del 1 al 100.",
                confirmButtonColor: "var(--azul-sanmartin)",
                background: "var(--card-bg)",
                color: "var(--text-color)"
            }).then(function () {
                enfocarMesaRapida();
            });
            return;
        }
        mesaActual = String(numeroInt);
        var cuenta = normalizarCuenta(mesaActual);
        // v121: usar la ventana de mozos numerados (1, 2, 3...) en vez del selector antiguo.
        if (cuenta.mozo_nombre || !mozosNumerados.length) {
            finalizarAperturaMesa(cuenta);
            return;
        }
        abrirSelectorMozoMesa(mesaActual, cuenta);
    }
    function liberarMesaActual() {
        var numeroMesa = mesaActual;
        if (numeroMesa) {
            // Al completar una venta se libera el UUID del borrador fiscal;
            // una mesa nueva nunca hereda el comprobante de la anterior.
            try { localStorage.removeItem('sanmartin_borrador_fiscal_mesa_' + numeroMesa); }
            catch (e) { /* acceso restringido a storage */ }
            cuentas[numeroMesa] = {
                items: [],
                total: 0,
                mozo_id: null,
                mozo_nombre: ""
            };
        }
        modoParcial = false;
        filaTeclado = 0;
        mesaActual = null;
        borrarMesaActualGuardada();
        guardar();
        actualizarMesas();
        if (modalComanda) {
            modalComanda.classList.remove("is-open");
            modalComanda.setAttribute("aria-hidden", "true");
        }
        if (modalOverlay) {
            modalOverlay.classList.remove("is-open");
            modalOverlay.setAttribute("aria-hidden", "true");
        }
        restaurarFondoComanda();
        document.body.style.overflow = "";
        enfocarMesaRapida();
    }
    // Estado asociado a la lista exacta de productos, no a la mesa vacia.
    function firmaTicket(cuenta) {
        return JSON.stringify((cuenta && cuenta.items || []).filter(function (i) {
            return Number(i.cantidad || 0) > 0;
        }).map(function (i) {
            return [Number(i.producto_id || 0), String(i.codigo || ''),
                Number(i.cantidad || 0), Number(i.precio || 0),
                String(i.origen || ''), Number(i.detalle_id || 0)];
        }));
    }
    function estadoVisibleTicket(cuenta) {
        if (!cuenta || !cuenta.items || !cuenta.items.length) return '';
        if (cuenta.ticket_firma !== firmaTicket(cuenta)) return '';
        return cuenta.ticket_estado === 'impreso' || cuenta.ticket_estado === 'pendiente'
            ? cuenta.ticket_estado : '';
    }
    function consultarEstadoTickets() {
        var url = root.getAttribute('data-print-status-url');
        if (!url || document.hidden) return;
        var ids = [];
        Object.keys(cuentas).forEach(function (mesa) {
            var c = cuentas[mesa];
            if (c && c.ticket_estado === 'pendiente' && Number(c.ticket_id) > 0)
                ids.push(Number(c.ticket_id));
        });
        if (!ids.length) return;
        fetch(url + '?ids=' + ids.slice(0, 100).join(','),
            {credentials:'same-origin',cache:'no-store'})
        .then(function (r) { if (!r.ok) throw new Error('Estado no disponible'); return r.json(); })
        .then(function (data) {
            if (data.status !== 'ok' || !data.estados) return;
            var cambiado = false;
            Object.keys(cuentas).forEach(function (mesa) {
                var c = cuentas[mesa];
                // No confirmar una impresión anterior si otro ticket ya fue enviado.
                if (c && c.ticket_estado === 'pendiente' &&
                    data.estados[String(c.ticket_id)] === 'impreso') {
                    c.ticket_estado = 'impreso';
                    cambiado = true;
                }
            });
            if (cambiado) { guardar(); actualizarMesas(); if (mesaActual) render(); }
        }).catch(function (e) { console.warn('Consulta ticket:', e.message); });
    }
    function actualizarMesas() {
        botonesMesa.forEach(function (boton) {
            var numero = String(boton.getAttribute("data-mesa"));
            var cuenta = cuentas[numero];
            var items = [];
            if (cuenta && Array.isArray(cuenta.items)) {
                items = cuenta.items.filter(function (item) {
                    return (item && Number(item.cantidad || 0) > 0);
                });
            }
            var ocupada = items.length > 0;
            var total = 0;
            items.forEach(function (item) {
                total += Number(item.precio || 0) * Number(item.cantidad || 0);
            });
            var seleccionada = numero === String(mesaActual || "");
            boton.classList.toggle("mesa-ocupada", ocupada);
            boton.classList.toggle("is-ocupada", ocupada);
            boton.classList.toggle("mesa-seleccionada", seleccionada);
            boton.classList.toggle("is-actual", seleccionada);
            var estadoTicket = ocupada ? estadoVisibleTicket(cuenta) : '';
            boton.classList.toggle('ticket-en-cola', estadoTicket === 'pendiente');
            boton.classList.toggle('ticket-impreso', estadoTicket === 'impreso');
            if (ocupada) {
                var htmlOcupada = "<span class=\"salon-pos__mesa-numero\">" + escapar(numero) + "</span>" + "<span class=\"salon-pos__mesa-total\">" + dinero(total) + "</span>" + (cuenta && cuenta.mozo_nombre ? "<span class=\"salon-pos__mesa-mozo\">\uD83E\uDDD1\u200D\uD83C\uDF73 " + escapar(cuenta.mozo_nombre) + "</span>" : "") + "<span class=\"salon-pos__mesa-items\">" + items.length + (items.length === 1 ? " producto" : " productos") + "</span>" + (estadoTicket ? "<span class=\"salon-pos__mesa-ticket\">" + (estadoTicket === 'impreso' ? '✓ Control impreso' : '⌛ En cola') + "</span>" : '');
                if (boton.innerHTML !== htmlOcupada) boton.innerHTML = htmlOcupada;
            }
            else {
                var htmlLibre = "<span class=\"salon-pos__mesa-numero\">" + escapar(numero) + "</span>" + "<span class=\"salon-pos__mesa-libre\">Libre</span>";
                if (boton.innerHTML !== htmlLibre) boton.innerHTML = htmlLibre;
            }
        });
    }
    function agregarProducto(producto) {
        var cuenta = cuentaActual();
        if (!cuenta) {
            return;
        }
        var cantidad = parseInt(inputCant.value, 10);
        if (!cantidad || cantidad < 1) {
            cantidad = 1;
        }
        var existente = cuenta.items.find(function (item) {
            if (producto.id && item.producto_id) {
                return (Number(producto.id) === Number(item.producto_id));
            }
            return (String(producto.codigo) === String(item.codigo));
        });
        if (existente) {
            existente.cantidad += cantidad;
            if (existente.seleccionado) {
                existente.cant_pagar = 1;
            }
        }
        else {
            cuenta.items.push({
                producto_id: producto.id,
                codigo: producto.codigo,
                nombre: producto.nombre,
                precio: producto.precio,
                cantidad: cantidad,
                seleccionado: false,
                cant_pagar: 1
            });
        }
        recalcular(cuenta);
        guardar();
        actualizarMesas();
        render();
        inputCant.value = 1;
        buscador.value = "";
        cerrarSugerencias();
        enfocarCantidad();
    }
    function buscarProductos(texto) {
        texto = String(texto || "").trim().toLowerCase();
        if (!texto) {
            return [];
        }
        var exactos = [];
        var otros = [];
        productos.forEach(function (producto) {
            var codigo = String(producto.codigo).toLowerCase();
            var nombre = String(producto.nombre).toLowerCase();
            if (codigo === texto) {
                // Ante el mismo codigo en web y Salon, elegir el articulo del Salon.
                if (producto.es_salon) exactos.unshift(producto);
                else exactos.push(producto);
                return;
            }
            if (codigo.indexOf(texto) === 0) {
                exactos.push(producto);
                return;
            }
            if (codigo.indexOf(texto) !== -1 || nombre.indexOf(texto) !== -1) {
                otros.push(producto);
            }
        });
        return exactos.concat(otros).slice(0, 8);
    }
    function cerrarSugerencias() {
        sugerencias = [];
        sugerenciaActiva = -1;
        if (listaSugerencias) {
            listaSugerencias.innerHTML = "";
            listaSugerencias.classList.remove("is-visible");
        }
    }
    function pintarSugerencias() {
        if (!listaSugerencias || !sugerencias.length) {
            cerrarSugerencias();
            return;
        }
        var html = "";
        sugerencias.forEach(function (producto, index) {
            var clase = index === sugerenciaActiva ? " is-activa" : "";
            html += "<li class=\"salon-pos__sugerencia" + clase + "\" data-index=\"" + index + "\">" + "<div class=\"salon-pos__sugerencia-main\">" + "<strong>" + escapar(producto.nombre) + "</strong>" + "<span>C\u00F3d. " + escapar(producto.codigo) + "</span>" + "</div>" + "<b>" + dinero(producto.precio) + "</b>" + "</li>";
        });
        listaSugerencias.innerHTML = html;
        listaSugerencias.classList.add("is-visible");
    }
    function resumenSeleccion(cuenta) {
        var cantidad = 0;
        var total = 0;
        if (!cuenta) {
            return {
                cantidad: 0,
                total: 0
            };
        }
        cuenta.items.forEach(function (item) {
            if (!item.seleccionado) {
                return;
            }
            var cant = Number(item.cant_pagar || 1);
            if (cant < 1) {
                cant = 1;
            }
            if (cant > item.cantidad) {
                cant = item.cantidad;
            }
            cantidad += cant;
            total += item.precio * cant;
        });
        return {
            cantidad: cantidad,
            total: total
        };
    }
    function toggleSeleccion(index) {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items[index]) {
            return;
        }
        var item = cuenta.items[index];
        item.seleccionado = !item.seleccionado;
        item.cant_pagar = 1;
        guardar();
        render();
    }
    function cambiarPago(index, diferencia) {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items[index]) {
            return;
        }
        var item = cuenta.items[index];
        if (!item.seleccionado) {
            return;
        }
        var cantidad = Number(item.cant_pagar || 1) + diferencia;
        if (cantidad < 1) {
            cantidad = 1;
        }
        if (cantidad > item.cantidad) {
            cantidad = item.cantidad;
        }
        item.cant_pagar = cantidad;
        guardar();
        render();
    }
    function cambiarCantidad(index, diferencia) {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items[index]) {
            return;
        }
        var item = cuenta.items[index];
        item.cantidad += diferencia;
        if (item.cantidad <= 0) {
            cuenta.items.splice(index, 1);
        }
        else if (item.cant_pagar > item.cantidad) {
            item.cant_pagar = item.cantidad;
        }
        if (filaTeclado >= cuenta.items.length) {
            filaTeclado = Math.max(0, cuenta.items.length - 1);
        }
        recalcular(cuenta);
        guardar();
        actualizarMesas();
        render();
    }
    function cambiarModoParcial(activar) {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items.length) {
            return;
        }
        modoParcial = Boolean(activar);
        filaTeclado = 0;
        limpiarSeleccion(cuenta);
        if (modoParcial) {
            cerrarSugerencias();
            if (document.activeElement && typeof document.activeElement.blur === "function") {
                document.activeElement.blur();
            }
        }
        else {
            enfocarCantidad();
        }
        guardar();
        render();
    }
    function toggleModoParcial() {
        cambiarModoParcial(!modoParcial);
    }
    function moverFilaTeclado(diferencia) {
        var cuenta = cuentaActual();
        if (!modoParcial || !cuenta || !cuenta.items.length) {
            return;
        }
        filaTeclado += diferencia;
        if (filaTeclado < 0) {
            filaTeclado = cuenta.items.length - 1;
        }
        if (filaTeclado >= cuenta.items.length) {
            filaTeclado = 0;
        }
        render();
        var fila = listaComanda.querySelector(".salon-pos__fila-pos[data-index=\"" + filaTeclado + "\"]");
        if (fila && typeof fila.scrollIntoView === "function") {
            fila.scrollIntoView({
                block: "nearest"
            });
        }
    }
    function render() {
        var cuenta = cuentaActual();
        if (!cuenta) {
            return;
        }
        recalcular(cuenta);
        if (!cuenta.items.length) {
            listaComanda.innerHTML = "";
            listaVacia.hidden = false;
        }
        else {
            listaVacia.hidden = true;
            var html = "";
            cuenta.items.forEach(function (item, index) {
                var clase = "";
                if (item.seleccionado) {
                    clase += " is-seleccionado";
                }
                if (modoParcial && index === filaTeclado) {
                    clase += " is-teclado";
                }
                html += "<div class=\"salon-pos__fila-pos" + clase + "\" data-index=\"" + index + "\">";
                if (item.origen === 'web') {
                    html += "<div class=\"salon-pos__fila-cant\" data-no-toggle=\"1\"><strong>" + item.cantidad + "</strong></div>";
                } else {
                    html += "<div class=\"salon-pos__fila-cant\" data-no-toggle=\"1\">" + "<button type=\"button\" data-action=\"restar\" data-index=\"" + index + "\">\u2212</button>" + "<strong>" + item.cantidad + "</strong>" + "<button type=\"button\" data-action=\"sumar\" data-index=\"" + index + "\">+</button>" + "</div>";
                }
                html += "<div class=\"salon-pos__fila-codigo\">" + escapar(item.codigo) + "</div>";
                html += "<div class=\"salon-pos__fila-descripcion\">" + "<strong>" + escapar(item.nombre) + "</strong>";
                if (modoParcial && item.seleccionado) {
                    html += "<div class=\"salon-pos__pago-inline\" data-no-toggle=\"1\">" + "<span>Cobrar</span>" + "<button type=\"button\" data-action=\"pagar-menos\" data-index=\"" + index + "\">\u2212</button>" + "<strong>" + item.cant_pagar + "</strong>" + "<button type=\"button\" data-action=\"pagar-mas\" data-index=\"" + index + "\">+</button>" + "<small>de " + item.cantidad + "</small>" + "</div>";
                }
                if (item.origen === 'web') html += '<small class="salon-pos__origen-web">Pedido web</small>';
                html += "</div>";
                html += "<div class=\"salon-pos__fila-unitario\">" + dinero(item.precio) + "</div>";
                html += "<div class=\"salon-pos__fila-total\">" + dinero(item.precio * item.cantidad) + "</div>";
                html += "</div>";
            });
            listaComanda.innerHTML = html;
        }
        var resumen = resumenSeleccion(cuenta);
        cantidadLineas.textContent = cuenta.items.length === 1 ? "1 producto" : cuenta.items.length + " productos";
        totalCuenta.textContent = dinero(cuenta.total);
        if (modoParcial) {
            resumenAccion.textContent = resumen.cantidad > 0 ? (resumen.cantidad + (resumen.cantidad === 1 ? " unidad seleccionada" : " unidades seleccionadas")) : "F2 salir \u00B7 \u2191\u2193 mover \u00B7 Enter seleccionar \u00B7 +/- cantidad";
            totalSeleccionado.textContent = resumen.cantidad > 0 ? dinero(resumen.total) : "$0";
            if (btnParcial) {
                btnParcial.textContent = "\u2715 Cancelar parcial";
                btnParcial.classList.add("is-activo");
            }
            btnAccion.textContent = resumen.cantidad > 0 ? ("\uD83D\uDCB5 Cobrar selecci\u00F3n \u00B7 " + dinero(resumen.total)) : "\uD83D\uDCB5 Seleccion\u00E1 productos";
            btnAccion.classList.add("is-parcial");
            btnAccion.classList.remove("is-completa");
        }
        else {
            resumenAccion.textContent = cuenta.items.length ? ("Mesa " + mesaActual + " \u00B7 " + cuenta.items.length + (cuenta.items.length === 1 ? " producto" : " productos")) : "Mesa sin productos";
            totalSeleccionado.textContent = cuenta.items.length ? dinero(cuenta.total) : "$0";
            if (btnParcial) {
                btnParcial.textContent = "\u2702 Dividir / Pago parcial";
                btnParcial.classList.remove("is-activo");
            }
            btnAccion.textContent = cuenta.items.length ? ("\uD83D\uDCB5 Pagar mesa \u00B7 " + dinero(cuenta.total)) : "\uD83D\uDCB5 Pagar mesa";
            btnAccion.classList.add("is-completa");
            btnAccion.classList.remove("is-parcial");
        }
        if (btnParcial) {
            btnParcial.disabled = !cuenta.items.length || enviando;
        }
        btnAccion.disabled = !cuenta.items.length || enviando || (modoParcial && resumen.cantidad === 0);
        btnTicket.disabled = !cuenta.items.length || enviando || (modoParcial && resumen.cantidad === 0);
        btnTicket.textContent = modoParcial ? '🖨 Ticket selección' : '🖨 Ticket mesa';
        guardar();
        actualizarMesas();
    }
    function obtenerCsrf() {
        var input = document.querySelector("#salon-csrf-form input[name=\"csrfmiddlewaretoken\"]");
        return input ? input.value : "";
    }
    function obtenerItemsTicket(cuenta, soloSeleccionados) {
        var items = [];
        cuenta.items.forEach(function (item) {
            if (soloSeleccionados && !item.seleccionado) {
                return;
            }
            var cantidad = soloSeleccionados ? Number(item.cant_pagar || 1) : Number(item.cantidad);
            items.push({
                producto_id: item.producto_id,
                codigo: item.codigo,
                nombre: item.nombre,
                precio: item.precio,
                cantidad: cantidad,
                origen: item.origen || '',
                pedido_id: item.pedido_id || 0,
                detalle_id: item.detalle_id || 0
            });
        });
        return items;
    }
    function enviarTicket(items, tipo) {
        var url = root.getAttribute("data-print-url");
        if (!url) {
            return Promise.reject(new Error("No se encontr\u00F3 la URL de impresi\u00F3n."));
        }
        enviando = true;
        render();
        return esperarRespaldoAntesDeCobrar().then(function(){return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": obtenerCsrf()
            },
            body: JSON.stringify({
                mesa: mesaActual,
                mozo: (cuentaActual() && cuentaActual().mozo_nombre) ? cuentaActual().mozo_nombre : "",
                tipo: tipo,
                items: items
            })
        }).then(function (response) {
            return response.json().catch(function () {
                return {};
            }).then(function (data) {
                if (!response.ok || data.status !== "ok") {
                    throw new Error(data.mensaje || "No se pudo enviar el ticket.");
                }
                return data;
            });
        });}).finally(function () {
            enviando = false;
            if (mesaActual) {
                render();
            }
        });
    }
    function buscarClienteCuentaCorriente(total) {
        if (!cuentasCorrientesPOS.length) {
            return Swal.fire({
                icon: 'info', title: 'No hay clientes cargados',
                text: 'Creá primero una persona desde Panel → Cuentas.',
                confirmButtonColor: 'var(--naranja-sterak)',
                background: 'var(--card-bg)', color: 'var(--text-color)'
            }).then(function () { return {isConfirmed: false}; });
        }

        return Swal.fire({
            title: 'Cargar a cuenta corriente',
            html: '<p class="salon-credito__aviso">No se recibe dinero ahora. El consumo se sumará a la deuda o descontará el saldo a favor.</p>' +
                  '<label class="salon-credito__label" for="salon-credito-buscar">Buscar cliente</label>' +
                  '<input id="salon-credito-buscar" class="salon-credito__buscador" placeholder="Nombre o teléfono" autocomplete="off">' +
                  '<label class="salon-credito__label" for="salon-credito-cliente">Seleccioná una persona</label>' +
                  '<select id="salon-credito-cliente" class="salon-credito__clientes" size="6"></select>' +
                  '<div class="salon-credito__saldo" id="salon-credito-saldo"></div>' +
                  '<strong class="salon-credito__importe">Consumo: ' + dinero(total) + '</strong>',
            showCancelButton: true,
            confirmButtonText: 'Agregar consumo',
            cancelButtonText: 'Volver',
            confirmButtonColor: 'var(--naranja-sterak)',
            background: 'var(--card-bg)', color: 'var(--text-color)',
            didOpen: function () {
                var buscador = document.getElementById('salon-credito-buscar');
                var selector = document.getElementById('salon-credito-cliente');
                var saldo = document.getElementById('salon-credito-saldo');
                function normalizar(texto) {
                    return String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
                }
                function mostrarSaldo() {
                    var cliente = cuentasCorrientesPOS.find(function (c) { return String(c.id) === selector.value; });
                    if (!cliente) { saldo.textContent = 'Elegí un cliente de la lista.'; return; }
                    var actual = Number(cliente.saldo || 0);
                    var despues = actual - Number(total || 0);
                    saldo.textContent = 'Saldo actual: ' + dinero(actual) + ' · Después: ' + dinero(despues);
                }
                function filtrar() {
                    var filtro = normalizar(buscador.value.trim());
                    var previo = selector.value;
                    selector.textContent = '';
                    cuentasCorrientesPOS.filter(function (c) {
                        return normalizar(c.nombre + ' ' + (c.telefono || '')).includes(filtro);
                    }).slice(0, 100).forEach(function (c) {
                        var opcion = document.createElement('option');
                        opcion.value = c.id;
                        opcion.textContent = c.nombre + (c.telefono ? ' · ' + c.telefono : '');
                        selector.appendChild(opcion);
                    });
                    if ([].some.call(selector.options, function (o) { return o.value === previo; })) {
                        selector.value = previo;
                    } else {
                        selector.selectedIndex = -1;
                    }
                    mostrarSaldo();
                }
                buscador.addEventListener('input', filtrar);
                selector.addEventListener('change', mostrarSaldo);
                filtrar();
                buscador.focus();
            },
            preConfirm: function () {
                var selector = document.getElementById('salon-credito-cliente');
                var id = Number(selector && selector.value || 0);
                var cliente = cuentasCorrientesPOS.find(function (c) { return Number(c.id) === id; });
                if (!cliente) {
                    Swal.showValidationMessage('Elegí una persona para registrar el consumo.');
                    return false;
                }
                return {id: cliente.id, nombre: cliente.nombre};
            }
        }).then(function (res) {
            if (!res.isConfirmed) return {isConfirmed: false};
            return {isConfirmed: true, value: 'cuenta_corriente', cuentaCorrienteId: res.value.id, cuentaCorrienteNombre: res.value.nombre};
        });
    }

    function elegirMedioPago(total, titulo, modoFiscal) {
        var opciones = {
            efectivo: '\uD83D\uDCB5 Efectivo',
            mercadopago: '\uD83D\uDCF1 Mercado Pago',
            debito: '\uD83D\uDCB3 Débito'
        };
        if (!modoFiscal) opciones.cuenta_corriente = '\uD83D\uDCD2 Cuenta corriente (fiado)';
        return Swal.fire({
            title: titulo || 'Registrar cobro',
            html: '<div style="margin-bottom:10px;color:var(--texto-mutado);">Total del consumo</div>' +
                  '<div style="font-size:1.55rem;font-weight:900;margin-bottom:14px;">' + dinero(total) + '</div>',
            // Mantener el radio de SweetAlert para conservar los cobros actuales.
            // CSS aislado evita la franja blanca y dispone opciones en tarjetas 2 x 2.
            input: 'radio', inputOptions: opciones,
            customClass: { popup: 'salon-cobro-alert' },
            inputValidator: function (valor) { return !valor ? 'Elegí el medio de cobro.' : null; },
            showCancelButton: true,
            confirmButtonText: 'Continuar', cancelButtonText: 'Cancelar',
            confirmButtonColor: 'var(--verde-sanmartin, #188659)',
            background: 'var(--card-bg)', color: 'var(--text-color)'
        }).then(function (res) {
            if (!res.isConfirmed || res.value !== 'cuenta_corriente') return res;
            return buscarClienteCuentaCorriente(total);
        });
    }

    function registrarCobroSalon(items, tipoPago, modoFiscal, cuentaCorrienteId) {
        var cuenta = cuentaActual();
        if (!cuenta || !items.length) {
            return Promise.reject(new Error("No hay productos para cobrar."));
        }
        var url = root.getAttribute("data-charge-url");
        if (!url) {
            return Promise.reject(new Error("Falta configurar la URL de cobro del sal\u00F3n."));
        }
        // Cada cobro, no solo la cuenta corriente, conserva el mismo ID en
        // reintentos: si Render completó el cobro pero se perdió la respuesta,
        // volver a intentar NO crea una segunda venta.
        var storageCobro = 'sterak_pos_cobro_pendiente_v1';
        var firma = JSON.stringify({mesa: mesaActual, tipo_pago: tipoPago,
            mozo: cuenta.mozo_nombre || '', cliente: cuentaCorrienteId || null, items: items});
        var opPendiente = null;
        try {
            var previa = JSON.parse(localStorage.getItem(storageCobro) || 'null');
            if (previa && previa.firma === firma && previa.creado > Date.now() - 24*60*60*1000)
                opPendiente = previa;
        } catch (error) { /* navegador sin storage */ }
        if (!opPendiente) {
            opPendiente = {
                firma: firma, creado: Date.now(),
                id: (window.crypto && window.crypto.randomUUID
                    ? window.crypto.randomUUID().replace(/-/g, '')
                    : Date.now().toString(36) + Math.random().toString(36).slice(2))
            };
            try { localStorage.setItem(storageCobro, JSON.stringify(opPendiente)); }
            catch (error) { /* no guardar jamás datos fiscales ni claves */ }
        }
        // No borrar el identificador de cobro ante un timeout. Render puede
        // haber confirmado el cobro aunque el navegador no haya recibido el 200.
        var controladorCobro = window.AbortController ? new AbortController() : null;
        var temporizadorCobro = controladorCobro ? window.setTimeout(function () {
            controladorCobro.abort();
        }, 20000) : null;
        function confirmarCobroLocal(data) {
                try {
                    // Limpiar solamente el cobro que acabamos de completar.
                    var actual = JSON.parse(localStorage.getItem(storageCobro) || 'null');
                    if (actual && actual.id === opPendiente.id) localStorage.removeItem(storageCobro);
                    if (tipoPago === 'cuenta_corriente') localStorage.removeItem('sterak_pos_credito_pendiente');
                } catch (error) { /* no afecta el cobro */ }
                if (tipoPago === 'cuenta_corriente') {
                    var cliente = cuentasCorrientesPOS.find(function (c) {
                        return Number(c.id) === Number(data.cuenta_corriente_id);
                    });
                    if (cliente) cliente.saldo = Number(data.cuenta_saldo || 0);
                }
        }
        function recuperarCobroSinRespuesta(errorOriginal) {
            var statusUrl = root.getAttribute('data-charge-status-url');
            if (!statusUrl) throw new Error('No se pudo confirmar el cobro. Consultá Ventas antes de reintentarlo.');
            return fetch(statusUrl + '?operacion_id=' + encodeURIComponent(opPendiente.id), {
                credentials: 'same-origin', cache: 'no-store'
            }).then(function(res) {
                if (!res.ok) throw new Error('Consulta de estado no disponible.');
                return res.json();
            }).then(function(resultado) {
                if (resultado.status === 'ok' && resultado.confirmado && resultado.cobro) {
                    confirmarCobroLocal(resultado.cobro);
                    return resultado.cobro;
                }
                throw new Error('Cobro sin confirmación (' + opPendiente.id.slice(0,8) + '). Revisá Ventas antes de reintentarlo; la mesa sigue abierta.');
            }).catch(function(error) {
                if (error.message.indexOf('Cobro sin confirmación') === 0) throw error;
                throw new Error('Sin respuesta de Render. Revisá Ventas antes de reintentar; conservamos el identificador del cobro.');
            });
        }
        enviando = true;
        render();
        return fetch(url, {
            credentials: "same-origin",
            signal: controladorCobro ? controladorCobro.signal : undefined,
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": obtenerCsrf()
            },
            body: JSON.stringify({
                mesa: mesaActual,
                mozo: cuenta.mozo_nombre || "",
                tipo_pago: tipoPago,
                cuenta_corriente_id: cuentaCorrienteId || null,
                operacion_id: opPendiente.id,
                modo_fiscal: Boolean(modoFiscal),
                items: items
            })
        }).then(function (response) {
            return response.json().catch(function () { return {}; }).then(function (data) {
                if (!response.ok || data.status !== "ok") {
                    var mensaje = data.mensaje || (response.status === 403
                        ? 'La sesión venció o el formulario no tiene CSRF válido. Volvé a iniciar sesión.'
                        : 'No se pudo registrar el cobro.');
                    throw new Error(mensaje);
                }
                confirmarCobroLocal(data);
                return data;
            });
        }).catch(function(error) {
            // Un error HTTP valido (400/403/500) ya tiene mensaje y NO se
            // reintenta silenciosamente. Solo red/timeout justifica consultar.
            if (error.name === 'AbortError' || error.name === 'TypeError')
                return recuperarCobroSinRespuesta(error);
            throw error;
        }).finally(function () {
            if (temporizadorCobro !== null) window.clearTimeout(temporizadorCobro);
            enviando = false;
            if (mesaActual)
                render();
        });
    }
    function mostrarError(error) {
        Swal.fire({
            icon: "error",
            title: "No se pudo completar",
            text: error.message || "Ocurri\u00F3 un error.",
            background: "var(--card-bg)",
            color: "var(--text-color)"
        });
    }
    function preguntarTicketCuenta(datos) {
        if (!datos || !datos.comprobante_id) return Promise.resolve();
        return Swal.fire({
            icon: 'success',
            title: 'Consumo pasado a cuenta',
            html: '<div style="margin:6px 0 12px">Se registró la deuda a nombre de <b></b>.</div>' +
                  '<div style="font-weight:800;margin:10px 0">Consumo: ' + dinero(datos.total || 0) + '</div>' +
                  '<small>No ingresó dinero a caja. ¿Imprimir comprobante no fiscal?</small>',
            showCancelButton: true,
            confirmButtonText: '🖨 Imprimir ticket',
            cancelButtonText: 'Listo, sin imprimir',
            confirmButtonColor: 'var(--naranja-sterak)',
            background: 'var(--card-bg)', color: 'var(--text-color)',
            didOpen: function (popup) {
                // Usar textContent para el nombre ingresado, nunca HTML.
                var nombre = popup.querySelector('b');
                if (nombre) nombre.textContent = datos.cuenta_corriente_nombre || 'cliente';
            }
        }).then(function (res) {
            if (!res.isConfirmed) return;
            return fetch('/dashboard/cuentas/comprobante/' + Number(datos.comprobante_id) + '/imprimir/', {
                method: 'POST', headers: {'X-CSRFToken': obtenerCsrf()}
            }).then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok || data.status !== 'ok') throw new Error(data.mensaje || 'No se pudo encolar el ticket.');
                    return Swal.fire({icon:'success',title:'Ticket enviado a caja',text:'La ticketera lo imprimirá cuando esté conectada.',timer:1600,showConfirmButton:false,background:'var(--card-bg)',color:'var(--text-color)'});
                });
            }).catch(mostrarError);
        });
    }
    function imprimirMesa() {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items.length || enviando) return Promise.resolve();
        // En división, un control de caja con SOLAMENTE los renglones y cantidades elegidos.
        // Nunca marcar el control de la mesa completa como impreso por un ticket parcial.
        if (modoParcial) {
            var elegidos = obtenerItemsTicket(cuenta, true);
            if (!elegidos.length) {
                return Swal.fire({icon:'info',title:'Elegí productos',
                    text:'Seleccioná una línea y ajustá la cantidad a cobrar. Luego presioná Ticket.',
                    background:'var(--card-bg)',color:'var(--text-color)'});
            }
            var firmaParcial = JSON.stringify(elegidos.map(function(it) {
                return [it.detalle_id, it.producto_id, it.codigo, it.precio, it.cantidad];
            }));
            function mandarParcial() {
                return enviarTicket(elegidos, 'cuenta_parcial').then(function(data) {
                    if (!data.ticket_id) throw new Error('No se recibió el identificador del ticket. Revisá la cola antes de reenviar.');
                    cuenta.ultimo_ticket_parcial_firma = firmaParcial;
                    cuenta.ultimo_ticket_parcial_id = Number(data.ticket_id);
                    guardar();
                    return Swal.fire({icon:'success', title:'Control parcial enviado',
                        text:'Solo se enviaron los productos seleccionados. La mesa sigue abierta y no se cobró nada.',
                        timer:1900,showConfirmButton:false,
                        background:'var(--card-bg)',color:'var(--text-color)'});
                }).catch(mostrarError);
            }
            if (cuenta.ultimo_ticket_parcial_firma === firmaParcial) {
                return Swal.fire({icon:'question',title:'Ya enviaste esta selección',
                    text:'¿Querés enviar una segunda copia del mismo control parcial?',
                    showCancelButton:true,confirmButtonText:'Reimprimir',cancelButtonText:'Cancelar',
                    background:'var(--card-bg)',color:'var(--text-color)'})
                    .then(function(r){ if (r.isConfirmed) return mandarParcial(); });
            }
            return mandarParcial();
        }
        var firma = firmaTicket(cuenta);
        var estado = estadoVisibleTicket(cuenta);
        if (estado === 'pendiente') {
            return Swal.fire({icon:'info',title:'Ticket en cola',
                text:'Ya se envió esta versión de la mesa. No se mandará otra copia.',
                background:'var(--card-bg)',color:'var(--text-color)'});
        }
        function enviar() {
            return enviarTicket(obtenerItemsTicket(cuenta, false), 'cuenta_mesa')
            .then(function (data) {
                if (!data.ticket_id) throw new Error('El servidor no devolvió el número del ticket. Consultá la cola antes de reintentar.');
                // Si la cuenta cambió durante la petición, no marcar los productos nuevos.
                if (firmaTicket(cuenta) === firma) {
                    cuenta.ticket_id = Number(data.ticket_id);
                    cuenta.ticket_firma = firma;
                    cuenta.ticket_estado = 'pendiente';
                    guardar(); actualizarMesas(); render();
                    consultarEstadoTickets();
                }
                return Swal.fire({icon:'success',title:'Ticket en cola',
                    text:'La mesa cambiará a verde cuando la ticketera confirme la impresión.',
                    timer:1700,showConfirmButton:false,
                    background:'var(--card-bg)',color:'var(--text-color)'});
            }).catch(mostrarError);
        }
        if (estado === 'impreso') {
            return Swal.fire({icon:'question',title:'Este control ya se imprimió',
                text:'¿Querés enviar otra copia a la impresora de caja?',
                showCancelButton:true,confirmButtonText:'Sí, reimprimir',cancelButtonText:'Cancelar',
                background:'var(--card-bg)',color:'var(--text-color)'})
            .then(function (r) { if (r.isConfirmed) return enviar(); });
        }
        return enviar();
    }
    function cobrarParcial() {
        if (enviando) return;
        var cuenta = cuentaActual();
        if (!cuenta)
            return;
        var resumen = resumenSeleccion(cuenta);
        var items = obtenerItemsTicket(cuenta, true);
        if (!items.length || resumen.cantidad <= 0)
            return;
        elegirMedioPago(resumen.total, "Cobro parcial \u00B7 Mesa " + mesaActual, false).then(function (resultado) {
            if (!resultado.isConfirmed)
                return;
            registrarCobroSalon(items, resultado.value, false, resultado.cuentaCorrienteId).then(function (datosCobro) {
                cuenta.items.forEach(function (item) {
                    if (!item.seleccionado)
                        return;
                    var cantidad = Number(item.cant_pagar || 1);
                    item.cantidad -= cantidad;
                    item.seleccionado = false;
                    item.cant_pagar = item.cantidad > 0 ? 1 : 0;
                });
                cuenta.items = cuenta.items.filter(function (item) {
                    return item.cantidad > 0;
                });
                recalcular(cuenta);
                delete cuenta.ultimo_ticket_parcial_firma;
                delete cuenta.ultimo_ticket_parcial_id;
                guardar();
                if (!cuenta.items.length) {
                    if (resultado.value !== 'cuenta_corriente') Swal.fire({
                        icon: "success",
                        title: resultado.value === 'cuenta_corriente' ? 'Consumo a cuenta registrado' : 'Pago registrado',
                        text: resultado.value === 'cuenta_corriente' ? 'El importe se cargó al cliente. No entró dinero a caja.' : 'La venta ya quedó incluida en el cierre de caja.', 
                        timer: 1200,
                        showConfirmButton: false,
                        background: "var(--card-bg)",
                        color: "var(--text-color)"
                    });
                    liberarMesaActual();
                    if (resultado.value === 'cuenta_corriente') preguntarTicketCuenta(datosCobro);
                    return;
                }
                filaTeclado = Math.min(filaTeclado, cuenta.items.length - 1);
                actualizarMesas();
                render();
                if (resultado.value === 'cuenta_corriente') {
                    preguntarTicketCuenta(datosCobro);
                    return;
                }
                Swal.fire({
                    icon: "success",
                    title: resultado.value === 'cuenta_corriente' ? 'Consumo parcial a cuenta' : 'Pago parcial registrado',
                    text: resultado.value === 'cuenta_corriente' ? 'El importe fue agregado a la cuenta del cliente.' : 'Ya suma al cierre de caja.', 
                    timer: 1100,
                    showConfirmButton: false,
                    background: "var(--card-bg)",
                    color: "var(--text-color)"
                });
            }).catch(mostrarError);
        });
    }
    function cobrarMesa(modoFiscal) {
        if (enviando) return;
        var cuenta = cuentaActual();
        modoFiscal = Boolean(modoFiscal);
        if (!cuenta || !cuenta.items.length)
            return;
        var numeroMesa = mesaActual;
        var items = obtenerItemsTicket(cuenta, false);
        var titulo = modoFiscal ? "Cierre fiscal · Mesa " + numeroMesa : "Cobrar Mesa " + numeroMesa;
        elegirMedioPago(cuenta.total, titulo, modoFiscal).then(function (resultado) {
            if (!resultado.isConfirmed)
                return;
            registrarCobroSalon(items, resultado.value, modoFiscal, resultado.cuentaCorrienteId).then(function (datosCobro) {
                if (resultado.value === 'cuenta_corriente') {
                    liberarMesaActual();
                    preguntarTicketCuenta(datosCobro);
                    return;
                }
                Swal.fire({
                    icon: "success",
                    title: modoFiscal ? "Cierre fiscal registrado" : (resultado.value === 'cuenta_corriente' ? 'Mesa enviada a cuenta corriente' : 'Mesa cobrada'),
                    text: modoFiscal ? "La venta quedó marcada para facturación fiscal." : (resultado.value === 'cuenta_corriente' ? 'El importe pasó a la cuenta del cliente; no ingresó dinero a caja.' : 'La venta quedó registrada en el cierre de caja.'),
                    timer: 1400,
                    showConfirmButton: false,
                    background: "var(--card-bg)",
                    color: "var(--text-color)"
                });
                liberarMesaActual();
            }).catch(mostrarError);
        });
    }

    // Emisión MANUAL por *, independiente del medio de cobro.
    // Con ARCA deshabilitado conserva el borrador de diagnóstico.
    function cobrarMesaFiscal() {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items.length || enviando) return;
        var items = obtenerItemsTicket(cuenta, false);
        var firma = JSON.stringify({mesa: mesaActual, items: items});
        var habilitado = root.getAttribute('data-fiscal-emission-enabled') === '1';
        Swal.fire({
            icon: habilitado ? 'warning' : 'info',
            title: habilitado ? 'Emitir Factura B con ARCA' : 'Preparación fiscal · Sin CAE',
            html: habilitado
                ? '<p><b>Solicitarás un CAE real si está configurado PRODUCCIÓN.</b></p>' +
                  '<p>Confirmá que todos los productos están gravados al 21% de IVA y que los datos de la mesa son correctos.</p>' +
                  '<p>La mesa NO se cobrará ni cerrará automáticamente. Se enviará a imprimir solo si ARCA autoriza.</p>'
                : '<p>Se guardará un borrador de la mesa. No se factura ni se imprime.</p>',
            showCancelButton: true,
            confirmButtonText: habilitado ? 'Sí, facturar con *' : 'Guardar borrador',
            cancelButtonText: 'Cancelar',
            background: 'var(--card-bg)', color: 'var(--text-color)'
        }).then(function (resultado) {
            if (!resultado.isConfirmed) return;
            var clave = 'sanmartin_borrador_fiscal_mesa_' + mesaActual;
            var op = null;
            try {
                var previo = JSON.parse(localStorage.getItem(clave) || 'null');
                if (previo && previo.firma === firma) op = previo.id;
            } catch (e) { /* almacenamiento deshabilitado */ }
            if (!op) {
                if (window.crypto && window.crypto.randomUUID) op = window.crypto.randomUUID();
                else op = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var n = Math.floor(Math.random() * 16);
                    return (c === 'x' ? n : (n & 3 | 8)).toString(16);
                });
                try { localStorage.setItem(clave, JSON.stringify({firma: firma, id: op})); }
                catch (e) { /* almacenamiento deshabilitado */ }
            }
            var url = root.getAttribute('data-fiscal-draft-url');
            if (!url) { mostrarError(new Error('Falta la URL de borradores fiscales.')); return; }
            enviando = true;
            render();
            fetch(url, {
                method: 'POST',
                headers: {'Content-Type':'application/json','X-CSRFToken':obtenerCsrf()},
                body: JSON.stringify({operacion_id:op, mesa:mesaActual,
                    mozo:cuenta.mozo_nombre || '', items:items})
            }).then(function(resp) {
                return resp.json().then(function(data) {
                    if (!resp.ok || data.status !== 'ok') throw new Error(data.mensaje || 'No se guardó el borrador.');
                    return data;
                });
            }).then(function(data) {
                if (!habilitado) return Swal.fire({icon:'info',title:'Borrador #' + data.borrador_id,
                    text:'NO es factura: no tiene CAE. La mesa permanece abierta.',
                    confirmButtonText:'Entendido', background:'var(--card-bg)',color:'var(--text-color)'});
                var emitirUrl = root.getAttribute('data-fiscal-emit-url');
                if (!emitirUrl) throw new Error('Falta la URL de emisión fiscal.');
                return fetch(emitirUrl, {method:'POST',
                    headers: {'Content-Type':'application/json','X-CSRFToken':obtenerCsrf()},
                    body:JSON.stringify({borrador_id:data.borrador_id,
                        confirmacion:'FACTURAR_CON_ASTERISCO',iva_21_confirmado:true})
                }).then(function(r){return r.json().then(function(d){
                    if(!r.ok || d.status!=='ok') throw new Error(d.mensaje || 'ARCA no autorizó la factura.');
                    return d;
                });}).then(function(d){
                    return Swal.fire({icon:'success', title:'Factura B · '+d.numero,
                        text:'CAE: '+d.cae+' · La ticketera la imprimirá desde la cola fiscal. La mesa sigue abierta.',
                        confirmButtonText:'Entendido',background:'var(--card-bg)',color:'var(--text-color)'});
                });
            }).catch(mostrarError).finally(function() {enviando = false; render();});
        });
    }
    botonesMesa.forEach(function (boton) {
        boton.addEventListener("click", function () {
            seleccionarMesa(boton.getAttribute("data-mesa"));
        });
    });
    // v156: estando en la grilla del POS, Enter ubica el cursor en Mesa rápida.
    // No secuestrar Enter dentro de botones, enlaces, campos o diálogos.
    document.addEventListener("keydown", function (event) {
        if (event.key !== "Enter" || event.repeat || event.altKey || event.ctrlKey ||
            event.metaKey || event.shiftKey || modalEstaAbierto() || enviando ||
            (window.Swal && typeof Swal.isVisible === "function" && Swal.isVisible())) return;
        var objetivo = event.target;
        if (objetivo === inputMesaRapida) return; // Enter acá abre la mesa elegida.
        if (objetivo && objetivo.closest && objetivo.closest(
                'input,textarea,select,button,a,summary,[contenteditable="true"],[role="dialog"]')) return;
        // Otras ventanas internas también tienen sus propios controles.
        if (document.querySelector('[role="dialog"][aria-modal="true"]:not([hidden])')) return;
        event.preventDefault();
        event.stopPropagation();
        enfocarMesaRapida();
    });
    if (inputMesaRapida) {
        inputMesaRapida.addEventListener("keydown", function (event) {
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            // Enter sin número solo deja Mesa rápida preparada para escribir.
            if (!String(inputMesaRapida.value || "").trim()) {
                inputMesaRapida.focus();
                return;
            }
            seleccionarMesa(inputMesaRapida.value);
        });
    }
    // v160: navegación del teclado sólo dentro de la comanda.
    // En Mozo, Arriba/Abajo siguen eligiendo mozos normalmente.
    if (selectorMozoMesa) {
        selectorMozoMesa.addEventListener('keydown', function (event) {
            if (!modalEstaAbierto() || event.altKey || event.ctrlKey || event.metaKey) return;
            if (event.key === 'ArrowRight' || event.key === 'Enter') {
                event.preventDefault(); event.stopPropagation(); enfocarCantidad();
            }
        });
    }
    if (inputCant) {
        // v156: los comandos se introducen en CANTIDAD, nunca en Código.
        inputCant.addEventListener("keydown", function (event) {
            if (!modalEstaAbierto() || event.altKey || event.ctrlKey || event.metaKey) return;
            if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
                event.preventDefault(); event.stopPropagation();
                if (buscador) { buscador.focus({preventScroll:true}); buscador.select(); }
                return;
            }
            if (event.key === 'ArrowUp' ||
                (event.key === 'ArrowLeft' && inputCant.selectionStart === 0)) {
                event.preventDefault(); event.stopPropagation();
                if (selectorMozoMesa) selectorMozoMesa.focus({preventScroll:true});
                return;
            }
            if (event.key !== "Enter") return;
            event.preventDefault();
            event.stopPropagation();
            var valor = String(inputCant.value || "").trim();
            if (valor === ".." || valor === "/" || valor === "//" ||
                valor === "*" || valor === "**") {
                inputCant.value = "1";
                cerrarSugerencias();
                if (valor === "..") imprimirMesa();
                else if (valor === "/" || valor === "//") cobrarMesa(false);
                else cobrarMesaFiscal(); // Solo borrador fiscal, sin CAE.
                return;
            }
            // Para cantidades válidas: Enter pasa al campo Código.
            var cantidad = Number(valor);
            inputCant.value = /^\d+$/.test(valor) && Number.isSafeInteger(cantidad) &&
                cantidad > 0 ? String(cantidad) : "1";
            if (buscador) {
                buscador.focus();
                buscador.select();
            }
        });
        // Si se pegó un atajo y luego se abandona el campo, no debe convertirse
        // silenciosamente en una cantidad al agregar un producto.
        inputCant.addEventListener("blur", function () {
            var valor = String(inputCant.value || "").trim();
            var numero = Number(valor);
            if (!/^\d+$/.test(valor) || !Number.isSafeInteger(numero) || numero < 1) {
                inputCant.value = "1";
            }
        });
    }
    if (buscador) {
        buscador.addEventListener("input", function () {
            sugerencias = buscarProductos(buscador.value);
            sugerenciaActiva = sugerencias.length ? 0 : -1;
            pintarSugerencias();
        });
        buscador.addEventListener("keydown", function (event) {
            // Flecha izquierda vuelve a Cantidad solo al inicio del texto;
            // Arriba vuelve si no hay sugerencias abiertas que recorrer.
            if (!event.altKey && !event.ctrlKey && !event.metaKey &&
                (event.key === 'ArrowLeft' && buscador.selectionStart === 0 && buscador.selectionEnd === 0 ||
                 event.key === 'ArrowUp' && !(sugerencias.length && listaSugerencias && listaSugerencias.classList.contains('is-visible')))) {
                event.preventDefault(); event.stopPropagation(); enfocarCantidad(); return;
            }
            if (event.key === "ArrowDown" && sugerencias.length) {
                event.preventDefault();
                event.stopPropagation();
                sugerenciaActiva++;
                if (sugerenciaActiva >= sugerencias.length) {
                    sugerenciaActiva = 0;
                }
                pintarSugerencias();
                return;
            }
            if (event.key === "ArrowUp" && sugerencias.length) {
                event.preventDefault();
                event.stopPropagation();
                sugerenciaActiva--;
                if (sugerenciaActiva < 0) {
                    sugerenciaActiva = sugerencias.length - 1;
                }
                pintarSugerencias();
                return;
            }
            if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                // Primer Esc: cerrar la lista; segundo Esc: volver a las mesas.
                if (listaSugerencias && listaSugerencias.classList.contains("is-visible")) {
                    cerrarSugerencias();
                } else if (modoParcial) {
                    cambiarModoParcial(false);
                } else {
                    cerrarComanda();
                }
                return;
            }
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            var valor = String(buscador.value || "").trim();
            // Código del producto queda dedicado exclusivamente al catálogo.
            // Resolver la busqueda usando el texto ACTUAL, no una lista vieja
            // o una segunda capa de listeners (v124).
            var resultados = buscarProductos(valor);
            if (resultados.length) {
                var index = sugerenciaActiva >= 0 && sugerenciaActiva < resultados.length
                    ? sugerenciaActiva : 0;
                agregarProducto(resultados[index]);
            } else if (valor) {
                sugerencias = [];
                sugerenciaActiva = -1;
                cerrarSugerencias();
            }
        });
    }
    if (listaSugerencias) {
        listaSugerencias.addEventListener("click", function (event) {
            var item = event.target.closest(".salon-pos__sugerencia");
            if (!item) {
                return;
            }
            var index = Number(item.getAttribute("data-index"));
            if (sugerencias[index]) {
                agregarProducto(sugerencias[index]);
            }
        });
    }
    if (listaComanda) {
        listaComanda.addEventListener("click", function (event) {
            var boton = event.target.closest("[data-action]");
            if (boton) {
                event.stopPropagation();
                var index = Number(boton.getAttribute("data-index"));
                var accion = boton.getAttribute("data-action");
                if (accion === "sumar") {
                    cambiarCantidad(index, 1);
                }
                if (accion === "restar") {
                    cambiarCantidad(index, -1);
                }
                if (accion === "pagar-mas") {
                    cambiarPago(index, 1);
                }
                if (accion === "pagar-menos") {
                    cambiarPago(index, -1);
                }
                return;
            }
            if (event.target.closest("[data-no-toggle=\"1\"]")) {
                return;
            }
            var fila = event.target.closest(".salon-pos__fila-pos");
            if (fila && modoParcial) {
                filaTeclado = Number(fila.getAttribute("data-index"));
                toggleSeleccion(filaTeclado);
            }
        });
    }
    if (selectorMozoMesa) {
        selectorMozoMesa.addEventListener("change", function () {
            var cuenta = cuentaActual();
            if (!cuenta)
                return;
            asignarMozoCuenta(cuenta, selectorMozoMesa.value);
        });
    }
    function resumenPendienteMesasLocal() {
        var abiertas = 0, importe = 0, detalle = [];
        Object.keys(cuentas).forEach(function(mesa) {
            var c = normalizarCuenta(mesa);
            var valor = c.items.reduce(function(acc, it) {
                return acc + Number(it.cantidad || 0) * Number(it.precio || 0);
            }, 0);
            if (c.items.length && valor > 0) {
                abiertas++; importe += valor;
                detalle.push({mesa:mesa, total:valor});
            }
        });
        detalle.sort(function(a,b){return Number(a.mesa)-Number(b.mesa);});
        return {mesas:abiertas, importe:importe, detalle:detalle};
    }
    function verResumenVentas() {
        var local = resumenPendienteMesasLocal();
        var html = '<div class="salon-ventas-resumen">' +
            '<div class="salon-ventas-cifras">' +
            '<div><small>Total registrado hoy · Render</small><strong id="sm-venta-total">Cargando...</strong></div>' +
            '<div><small>Ventas de salón · hoy</small><strong id="sm-venta-salon">Cargando...</strong></div>' +
            '<div><small>Facturado fiscal (CAE)</small><strong id="sm-venta-fiscal">Consultando...</strong></div>' +
            '<div><small>Sin conciliar</small><strong id="sm-venta-sinfactura">Por venta</strong></div>' +
            '<div><small>Mesas abiertas · este navegador</small><strong>' + local.mesas + ' · ' + dinero(local.importe) + '</strong></div>' +
            '</div><h4 class="salon-ventas-subtitulo">Mesas por cerrar (esta PC)</h4>' +
            '<div class="salon-ventas-mesas">' + (local.detalle.length ? local.detalle.map(function(it){
                return '<span>Mesa ' + escapar(it.mesa) + ' · <b>' + dinero(it.total) + '</b></span>';
            }).join('') : '<span>No hay mesas pendientes guardadas aquí.</span>') + '</div>' +
            '<p id="sm-venta-nota" class="salon-ventas-nota">Los datos de las ventas se consultan a Render. Las mesas abiertas se leen de este navegador; todavía no están centralizadas.</p>' +
            '<div class="salon-ventas-acciones">' +
            '<button type="button" id="sm-refrescar-ventas" class="salon-pos__atajo">↻ Actualizar</button>' +
            '<button type="button" id="sm-reiniciar-ventas" class="salon-pos__atajo salon-pos__atajo--peligro" title="Apartar ventas finalizadas del historial visible; NO elimina documentos ni cuentas de deudores">🧹 Reiniciar historial</button></div>' +
            '<small class="salon-ventas-advertencia">Se reinician los totales visibles y se ocultan ventas finalizadas anteriores. Los comprobantes y las cuentas de deudores quedan intactos. Esta opción no borra facturas fiscales.</small></div>';
        Swal.fire({title:'📊 Ventas y mesas',html:html,width:'660px',
            confirmButtonText:'Volver al salón',
            background:'var(--card-bg)', color:'var(--text-color)',
            didOpen:function(){
                function cargar(){
                    var url = root.getAttribute('data-sales-url');
                    fetch(url, {credentials:'same-origin',cache:'no-store'})
                    .then(function(r){return r.json().then(function(d){if(!r.ok||d.status!=='ok')throw new Error(d.mensaje||'No se pudieron leer las ventas');return d;});})
                    .then(function(d){
                        var t=document.getElementById('sm-venta-total');
                        var s=document.getElementById('sm-venta-salon');
                        var n=document.getElementById('sm-venta-sinfactura');
                        if(t)t.textContent=dinero(d.total_registrado);
                        if(s)s.textContent=dinero(d.total_salon);
                        var f=document.getElementById('sm-venta-fiscal');
                        if(f)f.textContent=dinero(d.total_facturado_fiscal || 0) + ' (' + (d.cantidad_facturas_fiscales || 0) + ')';
                        if(n)n.textContent='Pendiente de vincular';
                        var note=document.getElementById('sm-venta-nota');
                        if(note)note.textContent='Solo pedidos finalizados hoy ('+d.fecha+'), sin tickets temporales. No equivalen necesariamente a cobros conciliados. No se almacena CAE: no es posible separar facturado/no facturado con certeza. Mesas abiertas: únicamente este navegador.';
                    }).catch(function(err){
                        var note=document.getElementById('sm-venta-nota');
                        if(note)note.textContent='No se pudieron leer las ventas de Render: '+err.message+' · Mesas abiertas: solo este navegador.';
                    });
                }
                var btn=document.getElementById('sm-refrescar-ventas');
                if(btn)btn.addEventListener('click',cargar);
                var limpiar=document.getElementById('sm-reiniciar-ventas');
                if(limpiar)limpiar.addEventListener('click', function(){
                    window.smReiniciarHistorialVentas(root.getAttribute('data-reset-sales-url'),function(){
                        verResumenVentas();
                    },limpiar);
                });
                cargar();
            }
        });
    }
    var btnVentas=document.getElementById('salon-ver-ventas');
    if(btnVentas)btnVentas.addEventListener('click',verResumenVentas);
    if (btnParcial) {
        btnParcial.addEventListener("click", toggleModoParcial);
    }
    if (btnAccion) {
        btnAccion.addEventListener("click", function () {
            if (modoParcial) {
                cobrarParcial();
            }
            else {
                cobrarMesa(false);
            }
        });
    }
    if (btnTicket) {
        btnTicket.addEventListener("click", imprimirMesa);
    }
    if (btnCerrarComanda) {
        btnCerrarComanda.addEventListener("click", cerrarComanda);
    }
    if (btnCerrarComandaInferior) {
        btnCerrarComandaInferior.addEventListener("click", cerrarComanda);
    }
    if (modalOverlay) {
        modalOverlay.addEventListener("click", cerrarComanda);
    }
    document.addEventListener("keydown", function (event) {
        if (!mesaActual) {
            return;
        }
        if (event.key === "F2") {
            event.preventDefault();
            event.stopPropagation();
            toggleModoParcial();
            return;
        }
        if (event.ctrlKey && event.key === "Enter") {
            event.preventDefault();
            event.stopPropagation();
            if (modoParcial) {
                cobrarParcial();
            }
            else {
                cobrarMesa(false);
            }
            return;
        }
        // Los campos de la comanda manejan sus propias flechas/Enter.
        // No dejar que el modo parcial les robe las teclas.
        if (modoParcial && (event.target === buscador || event.target === inputCant ||
                            event.target === selectorMozoMesa)) {
            return;
        }
        if (modoParcial) {
            if (event.key === "ArrowDown") {
                event.preventDefault();
                event.stopPropagation();
                moverFilaTeclado(1);
                return;
            }
            if (event.key === "ArrowUp") {
                event.preventDefault();
                event.stopPropagation();
                moverFilaTeclado(-1);
                return;
            }
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                event.stopPropagation();
                toggleSeleccion(filaTeclado);
                return;
            }
            if (event.key === "+" || event.key === "=") {
                event.preventDefault();
                event.stopPropagation();
                cambiarPago(filaTeclado, 1);
                return;
            }
            if (event.key === "-") {
                event.preventDefault();
                event.stopPropagation();
                cambiarPago(filaTeclado, -1);
                return;
            }
        }
        if (event.key === "Escape") {
            event.preventDefault();
            if (listaSugerencias && listaSugerencias.classList.contains("is-visible")) {
                cerrarSugerencias();
                return;
            }
            if (modoParcial) {
                cambiarModoParcial(false);
                return;
            }
            if (modalEstaAbierto()) {
                cerrarComanda();
            }
        }
    });
    document.addEventListener("click", function (event) {
        if (!event.target.closest(".salon-pos__field--buscador")) {
            cerrarSugerencias();
        }
    });
    sincronizarPedidosWebSalon(pedidosWebIniciales);
    window.setInterval(refrescarPedidosWebSalon, 25000);
    window.setInterval(consultarEstadoTickets, 4500);
    window.setTimeout(consultarEstadoTickets, 900);
    document.addEventListener('visibilitychange',function () { if (!document.hidden) refrescarPedidosWebSalon(); });
    window.addEventListener("pagehide", guardar);
    window.addEventListener("beforeunload", guardar);
    if (mesaActual && document.querySelector(".salon-pos__mesa[data-mesa=\"" + mesaActual + "\"]")) {
        normalizarCuenta(mesaActual);
        tituloMesa.textContent = "Mesa " + mesaActual;
        estadoMesa.textContent = "MESA " + mesaActual;
        mensajeSeleccionar.hidden = true;
        mensajeSeleccionar.classList.add("is-hidden");
        areaComanda.hidden = false;
        render();
    }
    else {
        mesaActual = null;
        borrarMesaActualGuardada();
        actualizarMesas();
    }
    // Abrimos la caja solamente después de recuperar el respaldo del servidor.
    // El almacenamiento del navegador sirve como copia en caso de migración.
    if (respaldoUrl) {
        indicarRespaldo('Recuperando comandas de esta PC...');
        fetch(respaldoUrl,{credentials:'same-origin',cache:'no-store'})
        .then(function(res){if (!res.ok) throw new Error('No se pudo leer la base local');return res.json();})
        .then(function(d){
            if (d.status !== 'ok' || !d.cuentas || typeof d.cuentas !== 'object')
                throw new Error('La copia de mesas no es válida');
            respaldoVersion = Number(d.version || 0);
            if (respaldoVersion > 0) {
                cuentas = d.cuentas;
                try { localStorage.setItem(storageKey,JSON.stringify(cuentas)); }catch(e){}
            }
            respaldoPreparado = true;
            root.style.pointerEvents = '';
            indicarRespaldo(respaldoVersion ? 'Mesas recuperadas de esta PC' : 'Caja local lista');
            sincronizarPedidosWebSalon(pedidosWebIniciales);
            if (mesaActual) render();
            else actualizarMesas();
        }).catch(function(err){ bloquearRespaldo(err.message); });
    }
    enfocarMesaRapida();
})();

// ==========================================================================
// # MODAL DE BIENVENIDA DEL MENÚ PÚBLICO
// ==========================================================================

document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('modal-bienvenida-menu');
    const botonCerrar = document.getElementById('btn-cerrar-bienvenida-menu');

    if (!modal || !botonCerrar) {
        return;
    }

    const fondo = modal.querySelector('[data-bienvenida-cerrar]');
    const claveSesion = 'bienvenidaBuffetMostradaV1';
    let yaMostrada = false;

    try {
        yaMostrada = sessionStorage.getItem(claveSesion) === '1';
    } catch (error) {
        yaMostrada = false;
    }

    function abrirBienvenida() {
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('bienvenida-menu-abierta');

        try {
            sessionStorage.setItem(claveSesion, '1');
        } catch (error) {
            // Si el navegador bloquea sessionStorage, el modal igual funciona.
        }

        window.setTimeout(function () {
            botonCerrar.focus();
        }, 180);
    }

    function cerrarBienvenida() {
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('bienvenida-menu-abierta');
    }

    botonCerrar.addEventListener('click', cerrarBienvenida);

    if (fondo) {
        fondo.addEventListener('click', cerrarBienvenida);
    }

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && modal.classList.contains('is-open')) {
            cerrarBienvenida();
        }
    });

    if (!yaMostrada) {
        window.addEventListener('load', function () {
            // El loader termina primero y después aparece la tarjeta.
            window.setTimeout(abrirBienvenida, 900);
        }, { once: true });
    }
});


// ==========================================================================
// SISTEMA SM - CONFIGURACIÓN RÁPIDA + FIX FILTRO/COMANDA
// ==========================================================================

(function () {
    function normalizar(texto) {
        return String(texto || "")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function obtenerCsrfConfig() {
        var input = document.querySelector('#config-csrf-form input[name="csrfmiddlewaretoken"]');
        if (input) return input.value;

        var cookie = document.cookie.split(';').map(function (c) { return c.trim(); }).find(function (c) {
            return c.indexOf('csrftoken=') === 0;
        });

        return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
    }

    function estadoConfig(mensaje, tipo) {
        var estado = document.getElementById('config-estado-guardado');
        if (!estado) return;

        estado.textContent = mensaje || '';
        estado.classList.toggle('is-error', tipo === 'error');

        if (mensaje && tipo !== 'error') {
            window.clearTimeout(estado.dataset.timer);
            estado.dataset.timer = window.setTimeout(function () {
                estado.textContent = '';
            }, 2200);
        }
    }

    window.guardarConfiguracion = async function guardarConfiguracion(elemento) {
        var panel = document.querySelector('.config-sistema');
        if (!panel || !elemento) return;

        var campo = elemento.dataset.configCampo;
        if (!campo) return;

        var url = panel.dataset.configUrl || '/dashboard/configuracion/actualizar/';
        var valor = elemento.type === 'checkbox' ? (elemento.checked ? 'true' : 'false') : elemento.value;

        if (campo === 'descuento_efectivo_porcentaje') {
            var numero = parseInt(valor || '0', 10);
            if (Number.isNaN(numero)) numero = 0;
            numero = Math.max(0, Math.min(numero, 100));
            elemento.value = numero;
            valor = String(numero);
        }

        if (campo === 'hora_cierre' && !valor) {
            estadoConfig('Ingresá una hora válida.', 'error');
            return;
        }

        var valorAnterior = elemento.type === 'checkbox' ? !elemento.checked : elemento.defaultValue;
        var datos = new FormData();
        datos.append('campo', campo);
        datos.append('valor', valor);

        elemento.disabled = true;
        estadoConfig('Guardando...');

        try {
            var response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': obtenerCsrfConfig(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: datos
            });

            var data = await response.json().catch(function () {
                return {status: 'error', mensaje: 'Respuesta inválida del servidor.'};
            });

            if (!response.ok || data.status !== 'ok') {
                throw new Error(data.mensaje || 'No se pudo guardar la configuración.');
            }

            if (elemento.type !== 'checkbox') {
                elemento.defaultValue = elemento.value;
            }

            if (campo === 'buffet_habilitado') {
                var boton = document.getElementById('btn-estado-global');
                if (boton) {
                    boton.classList.toggle('is-danger', elemento.checked);
                    boton.classList.toggle('is-success', !elemento.checked);
                    boton.textContent = elemento.checked ? '🔴 Pausar pedidos' : '🟢 Activar pedidos';
                }
            }

            if (campo === 'salon_habilitado') {
                document.querySelectorAll('[href$="/salon/"], [href*="/salon/"]').forEach(function (link) {
                    link.hidden = !elemento.checked;
                });
            }

            estadoConfig('Guardado ✓');
        } catch (error) {
            console.error(error);
            estadoConfig(error.message, 'error');

            if (elemento.type === 'checkbox') {
                elemento.checked = valorAnterior;
            } else {
                elemento.value = valorAnterior;
            }
        } finally {
            elemento.disabled = false;
        }
    };

    function ocultarCabeceraComandaSM() {
        var modal = document.getElementById('salon-comanda-modal') || document;

        modal.querySelectorAll(
            '#comanda-header-nuevo, .comanda-header-nuevo, ' +
            '.salon-pos__lista-head, .salon-pos__lista-head--fix, ' +
            '.salon-pos__lista-head--real, .salon-pos__lista-head--columnas-fijas, ' +
            '.salon-pos__tabla thead, #salon-comanda-modal thead'
        ).forEach(function (el) {
            if (el && el.parentNode) {
                el.parentNode.removeChild(el);
            }
        });
    }

    function productoCoincidePuesto(producto, puestoActivo) {
        if (!puestoActivo || puestoActivo === 'todos') return true;

        var puestos = String(producto.dataset.puestos || '')
            .split(',')
            .map(function (x) { return String(x).trim(); })
            .filter(Boolean);

        if (puestos.indexOf(String(puestoActivo)) !== -1) return true;

        return normalizar(producto.textContent).indexOf(normalizar(puestoActivo)) !== -1;
    }

    function obtenerPuestoActivo() {
        var btn =
            document.querySelector('.menu-admin-filtro.is-active') ||
            document.querySelector('.menu-admin-filtro.active') ||
            document.querySelector('.btn-filtro-menu.is-active') ||
            document.querySelector('.btn-filtro-menu.active');

        if (!btn) return 'todos';
        return String(btn.dataset.puesto || btn.getAttribute('data-puesto') || btn.textContent || 'todos').trim();
    }

    function aplicarFiltroMenuSM() {
        var input =
            document.getElementById('buscador-menu-admin') ||
            document.querySelector('.menu-admin-buscador input') ||
            document.querySelector('#tab-menu input[type="search"]') ||
            document.querySelector('input[placeholder*="Buscar"]');

        var texto = normalizar(input ? input.value : '');
        var puestoActivo = obtenerPuestoActivo();
        var totalVisibles = 0;

        document.querySelectorAll('.categoria-menu, .menu-admin-categoria').forEach(function (categoria) {
            var visiblesCategoria = 0;

            categoria.querySelectorAll('.fila-producto-menu, .menu-admin-producto').forEach(function (producto) {
                var busqueda = normalizar(producto.dataset.busqueda || producto.getAttribute('data-busqueda') || producto.textContent);
                var visible = (!texto || busqueda.indexOf(texto) !== -1) && productoCoincidePuesto(producto, puestoActivo);

                producto.hidden = !visible;

                if (visible) {
                    producto.style.removeProperty('display');
                    visiblesCategoria += 1;
                    totalVisibles += 1;
                } else {
                    producto.style.setProperty('display', 'none', 'important');
                }
            });

            categoria.hidden = visiblesCategoria === 0;
            if (visiblesCategoria === 0) {
                categoria.style.setProperty('display', 'none', 'important');
            } else {
                categoria.style.removeProperty('display');
                if (texto && categoria.tagName && categoria.tagName.toLowerCase() === 'details') {
                    categoria.open = true;
                }
            }

            var cantidad = categoria.querySelector('.menu-admin-categoria__cantidad');
            if (cantidad) {
                cantidad.textContent = visiblesCategoria + ' producto' + (visiblesCategoria === 1 ? '' : 's');
            }
        });

        var sinResultados = document.getElementById('menu-admin-sin-resultados');
        if (sinResultados) {
            sinResultados.hidden = totalVisibles > 0;
            sinResultados.style.setProperty('display', totalVisibles > 0 ? 'none' : 'block', 'important');
        }
    }

    window.filtrarMenu = function (puesto, boton) {
        document.querySelectorAll('.menu-admin-filtro, .btn-filtro-menu').forEach(function (btn) {
            btn.classList.remove('is-active', 'active');
        });

        if (boton) {
            boton.classList.add('is-active', 'active');
            boton.dataset.puesto = puesto || 'todos';
        }

        aplicarFiltroMenuSM();
    };

    function iniciarSistemaSMFinal() {
        ocultarCabeceraComandaSM();
        aplicarFiltroMenuSM();

        document.querySelectorAll('.config-sistema [data-config-campo]').forEach(function (campo) {
            if (campo.dataset.configReady === '1') return;
            campo.dataset.configReady = '1';
            campo.addEventListener('change', function () {
                window.guardarConfiguracion(campo);
            });
        });

        var input =
            document.getElementById('buscador-menu-admin') ||
            document.querySelector('.menu-admin-buscador input') ||
            document.querySelector('#tab-menu input[type="search"]') ||
            document.querySelector('input[placeholder*="Buscar"]');

        if (input && input.dataset.filtroSistemaSMFinal !== '1') {
            input.dataset.filtroSistemaSMFinal = '1';
            input.addEventListener('input', aplicarFiltroMenuSM);
            input.addEventListener('keyup', aplicarFiltroMenuSM);
            input.addEventListener('search', aplicarFiltroMenuSM);
            input.addEventListener('change', aplicarFiltroMenuSM);
        }

        var modal = document.getElementById('salon-comanda-modal') || document.body;
        if (modal && modal.dataset.sinCabeceraComandaSMFinal !== '1') {
            modal.dataset.sinCabeceraComandaSMFinal = '1';
            new MutationObserver(function () {
                window.requestAnimationFrame(ocultarCabeceraComandaSM);
                window.setTimeout(ocultarCabeceraComandaSM, 80);
            }).observe(modal, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarSistemaSMFinal);
    } else {
        iniciarSistemaSMFinal();
    }

    window.addEventListener('load', iniciarSistemaSMFinal);
    [100, 300, 700, 1400, 2600].forEach(function (t) {
        window.setTimeout(iniciarSistemaSMFinal, t);
    });
})();



// ==========================================================================

(function () {
    function iniciarSwitchConfigRobusto() {
        document.querySelectorAll('.config-switch').forEach(function (switchVisual) {
            if (switchVisual.dataset.switchRobusto === '1') return;
            switchVisual.dataset.switchRobusto = '1';

            switchVisual.addEventListener('click', function (event) {
                var label = switchVisual.closest('label');
                var input = label ? label.querySelector('input[type="checkbox"][data-config-campo]') : null;

                if (!input) {
                    input = switchVisual.previousElementSibling;
                }

                if (!input || input.disabled || !input.dataset || !input.dataset.configCampo) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();

                input.checked = !input.checked;

                if (typeof window.guardarConfiguracion === 'function') {
                    window.guardarConfiguracion(input);
                } else {
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarSwitchConfigRobusto);
    } else {
        iniciarSwitchConfigRobusto();
    }

    window.addEventListener('load', iniciarSwitchConfigRobusto);
})();


// ==========================================================================
// SISTEMA SM V89 - REFRESCAR CUENTAS POR MESA
// ==========================================================================

(function () {
    function refrescarMesasCuandoCorresponde() {
        const tabMesas = document.getElementById('tab-mesas');
        if (!tabMesas) return;

        const visible = tabMesas.style.display !== 'none' && !tabMesas.hidden;

        if (visible && typeof window.renderizarMesas === 'function') {
            window.setTimeout(window.renderizarMesas, 80);
            window.setTimeout(window.renderizarMesas, 300);
        }
    }

    document.addEventListener('click', function (event) {
        const boton = event.target.closest('[onclick*="mesas"], #btn-tab-mesas');
        if (boton) {
            window.setTimeout(refrescarMesasCuandoCorresponde, 100);
            window.setTimeout(refrescarMesasCuandoCorresponde, 400);
        }
    });

    window.addEventListener('load', function () {
        window.setTimeout(refrescarMesasCuandoCorresponde, 300);
    });
})();


// ==========================================================================
// SISTEMA SM V91 - GRILLA SALÓN ROBUSTA + TICKET PARCIAL
// ==========================================================================

(function () {
    function refrescarGrillaSalon() {
        var wrap = document.querySelector('.salon-pos__tabla-wrap');
        var lista = document.getElementById('lista-comanda');
        var header = document.getElementById('salon-pos-grilla-header');

        if (!wrap || !lista) {
            return;
        }

        var hayProductos = lista.querySelectorAll('.salon-pos__fila-pos').length > 0;

        wrap.classList.toggle('has-products', hayProductos);
        wrap.classList.toggle('is-empty', !hayProductos);

        if (header) {
            header.style.setProperty('display', hayProductos ? 'grid' : 'none', 'important');
        }
    }

    function iniciarGrillaSalonV91() {
        refrescarGrillaSalon();

        var lista = document.getElementById('lista-comanda');
        if (lista && lista.dataset.grillaV91 !== '1') {
            lista.dataset.grillaV91 = '1';

            new MutationObserver(function () {
                window.requestAnimationFrame(refrescarGrillaSalon);
                window.setTimeout(refrescarGrillaSalon, 80);
            }).observe(lista, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarGrillaSalonV91);
    } else {
        iniciarGrillaSalonV91();
    }

    window.addEventListener('load', iniciarGrillaSalonV91);

    document.addEventListener('click', function () {
        window.setTimeout(refrescarGrillaSalon, 60);
        window.setTimeout(refrescarGrillaSalon, 180);
    });

    document.addEventListener('input', function () {
        window.setTimeout(refrescarGrillaSalon, 80);
    });
})();


// ==========================================================================
// SISTEMA SM V93 - CONFIGURACIÓN ROBUSTA
// Guarda switches de Configuración y recarga para reflejar el cambio real.
// ==========================================================================

(function () {
    function obtenerCsrfConfigV93() {
        var input = document.querySelector('#config-csrf-form input[name="csrfmiddlewaretoken"]');
        if (input && input.value) {
            return input.value;
        }

        var cookie = document.cookie.split(';').map(function (c) { return c.trim(); }).find(function (c) {
            return c.indexOf('csrftoken=') === 0;
        });

        return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
    }

    function estadoConfigV93(mensaje, tipo) {
        var estado = document.getElementById('config-estado-guardado');
        if (!estado) return;

        estado.textContent = mensaje || '';
        estado.classList.toggle('is-error', tipo === 'error');

        if (mensaje && tipo !== 'error') {
            window.clearTimeout(estado.dataset.timer);
            estado.dataset.timer = window.setTimeout(function () {
                estado.textContent = '';
            }, 2600);
        }
    }

    window.guardarConfiguracion = async function guardarConfiguracion(elemento) {
        var panel = document.querySelector('.config-sistema');
        if (!panel || !elemento) return;

        var campo = elemento.dataset.configCampo;
        if (!campo) return;

        var url = panel.dataset.configUrl || '/dashboard/configuracion/actualizar/';
        var valor = elemento.type === 'checkbox' ? (elemento.checked ? 'true' : 'false') : elemento.value;
        var valorAnterior = elemento.type === 'checkbox' ? !elemento.checked : elemento.defaultValue;

        if (campo === 'descuento_efectivo_porcentaje') {
            var numero = parseInt(valor || '0', 10);
            if (Number.isNaN(numero)) numero = 0;
            numero = Math.max(0, Math.min(numero, 100));
            elemento.value = numero;
            valor = String(numero);
        }

        if (campo === 'hora_cierre' && !valor) {
            estadoConfigV93('Ingresá una hora válida.', 'error');
            return;
        }

        var datos = new FormData();
        datos.append('campo', campo);
        datos.append('valor', valor);

        elemento.disabled = true;
        estadoConfigV93('Guardando...');

        try {
            var response = await fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': obtenerCsrfConfigV93(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: datos
            });

            var data = await response.json().catch(function () {
                return {status: 'error', mensaje: 'Respuesta inválida del servidor.'};
            });

            if (!response.ok || data.status !== 'ok') {
                throw new Error(data.mensaje || 'No se pudo guardar la configuración.');
            }

            if (elemento.type !== 'checkbox') {
                elemento.defaultValue = elemento.value;
            }

            estadoConfigV93('Guardado ✓');

            // Recargamos para que el panel, menú público y banners tomen el estado real.
            window.setTimeout(function () {
                window.location.reload();
            }, 550);

        } catch (error) {
            console.error(error);
            estadoConfigV93(error.message || 'No se pudo guardar.', 'error');

            if (elemento.type === 'checkbox') {
                elemento.checked = valorAnterior;
            } else {
                elemento.value = valorAnterior;
            }

            window.alert(error.message || 'No se pudo guardar la configuración.');
        } finally {
            elemento.disabled = false;
        }
    };

    function inputDeSwitch(switchVisual) {
        if (!switchVisual) return null;

        var label = switchVisual.closest('label');
        var input = label ? label.querySelector('input[type="checkbox"][data-config-campo]') : null;

        if (!input) {
            input = switchVisual.previousElementSibling;
        }

        if (!input || !input.dataset || !input.dataset.configCampo) {
            return null;
        }

        return input;
    }

    function iniciarConfigV93() {
        var panel = document.querySelector('.config-sistema');
        if (!panel || panel.dataset.configV93 === '1') return;

        panel.dataset.configV93 = '1';

        // Click sobre la perilla visual: manejamos nosotros, antes del label.
        panel.addEventListener('click', function (event) {
            var switchVisual = event.target.closest('.config-switch');
            if (!switchVisual || !panel.contains(switchVisual)) return;

            var input = inputDeSwitch(switchVisual);
            if (!input || input.disabled) return;

            event.preventDefault();
            event.stopPropagation();
            if (typeof event.stopImmediatePropagation === 'function') {
                event.stopImmediatePropagation();
            }

            input.checked = !input.checked;
            window.guardarConfiguracion(input);
        }, true);

        // Cambios sobre input real / time / number.
        panel.querySelectorAll('[data-config-campo]').forEach(function (campo) {
            if (campo.dataset.configV93Ready === '1') return;
            campo.dataset.configV93Ready = '1';

            campo.addEventListener('change', function () {
                window.guardarConfiguracion(campo);
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarConfigV93);
    } else {
        iniciarConfigV93();
    }

    window.addEventListener('load', iniciarConfigV93);
})();



// ==========================================================================
// SISTEMA SM V107 - POPUP SECUENCIAL CON X
// X = siguiente imagen. En la última X, cierra el popup.
// ==========================================================================

(function () {
    function iniciarPopupSecuencialSM() {
        var modal = document.getElementById('modal-bienvenida-menu');

        if (!modal || modal.dataset.popupSecuencialV107 === '1') {
            return;
        }

        modal.dataset.popupSecuencialV107 = '1';

        var slides = Array.prototype.slice.call(
            modal.querySelectorAll('.bienvenida-popup-slide')
        );
        var dots = Array.prototype.slice.call(
            modal.querySelectorAll('.bienvenida-popup-dot')
        );
        var btnPrev = modal.querySelector('[data-popup-prev]');
        var btnNext = modal.querySelector('[data-popup-next]');
        var botonCerrar = document.getElementById('btn-cerrar-bienvenida-menu');
        var index = 0;

        function mostrar(n) {
            if (!slides.length) {
                return;
            }

            index = Math.max(0, Math.min(n, slides.length - 1));

            slides.forEach(function (slide, i) {
                slide.classList.toggle('is-active', i === index);
            });

            dots.forEach(function (dot, i) {
                dot.classList.toggle('is-active', i === index);
            });
        }

        function cerrarModal() {
            modal.classList.remove('is-open');
            modal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('bienvenida-menu-abierta');
        }

        if (btnPrev) {
            btnPrev.addEventListener('click', function (event) {
                event.preventDefault();
                mostrar(index - 1);
            });
        }

        if (btnNext) {
            btnNext.addEventListener('click', function (event) {
                event.preventDefault();

                if (index < slides.length - 1) {
                    mostrar(index + 1);
                } else {
                    mostrar(0);
                }
            });
        }

        dots.forEach(function (dot, i) {
            dot.addEventListener('click', function (event) {
                event.preventDefault();
                mostrar(i);
            });
        });

        if (botonCerrar) {
            botonCerrar.addEventListener('click', function (event) {
                // Frenamos el cierre viejo para que la X primero pase al siguiente popup.
                event.preventDefault();
                event.stopPropagation();
                if (event.stopImmediatePropagation) {
                    event.stopImmediatePropagation();
                }

                if (slides.length > 1 && index < slides.length - 1) {
                    mostrar(index + 1);
                    return;
                }

                cerrarModal();
            }, true);
        }

        // Siempre arranca en la primera imagen cuando se abre.
        var observer = new MutationObserver(function () {
            if (modal.classList.contains('is-open')) {
                mostrar(0);
            }
        });

        observer.observe(modal, {
            attributes: true,
            attributeFilter: ['class']
        });

        mostrar(0);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarPopupSecuencialSM);
    } else {
        iniciarPopupSecuencialSM();
    }

    window.addEventListener('load', iniciarPopupSecuencialSM);
})();

// ==========================================================================
// SISTEMA SM V97 - PRECIO RÁPIDO ROBUSTO
// ==========================================================================
(function () {
    function iniciarPrecioRapidoV97() {
        document.querySelectorAll('.menu-admin-precio-form').forEach(function (form) {
            if (form.dataset.precioRapidoV97 === '1') return;
            form.dataset.precioRapidoV97 = '1';

            form.addEventListener('submit', function (event) {
                if (typeof window.editarPrecioAjax === 'function') {
                    window.editarPrecioAjax(event, form);
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarPrecioRapidoV97);
    } else {
        iniciarPrecioRapidoV97();
    }

    window.addEventListener('load', iniciarPrecioRapidoV97);
})();



// SAN MARTIN v108 - CUENTAS E IMPRESION
// ==========================================================================
// STERAKFOOD V100 - CUENTAS: NO SALTAR AL INICIO + ENTER AVANZA CAMPOS
// ==========================================================================

(function () {
    function abrirCuentasDesdeUrl() {
        var params = new URLSearchParams(window.location.search);
        var tab = params.get('tab');
        var hash = window.location.hash || '';

        if (tab !== 'cuentas' && hash.indexOf('cuenta-') === -1 && hash !== '#tab-cuentas') {
            return;
        }

        var btn = document.getElementById('btn-tab-cuentas');

        if (typeof abrirTab === 'function') {
            abrirTab('cuentas', btn);
        }

        if (hash.indexOf('cuenta-') !== -1) {
            var cuenta = document.querySelector(hash);
            if (cuenta) {
                cuenta.open = true;
                window.setTimeout(function () {
                    cuenta.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 120);
            }
        }
    }

    function camposNavegables(form) {
        return Array.prototype.slice.call(
            form.querySelectorAll(
                'input:not([type="hidden"]):not([type="checkbox"]), select, textarea, button[type="submit"]'
            )
        ).filter(function (campo) {
            return (
                !campo.disabled
                &&
                campo.offsetParent !== null
            );
        });
    }

    function instalarEnterCuentas() {
        var panel = document.querySelector('.cuentas-panel');

        if (!panel || panel.dataset.enterCuentasV100 === '1') {
            return;
        }

        panel.dataset.enterCuentasV100 = '1';

        panel.addEventListener('keydown', function (event) {
            if (event.key !== 'Enter') {
                return;
            }

            var target = event.target;

            if (!target.matches('input, select, textarea')) {
                return;
            }

            // En textarea dejamos Shift+Enter para salto de línea si algún día se usa.
            if (target.tagName === 'TEXTAREA' && event.shiftKey) {
                return;
            }

            var form = target.closest('form');

            if (!form || !panel.contains(form)) {
                return;
            }

            var campos = camposNavegables(form);
            var index = campos.indexOf(target);

            if (index === -1) {
                return;
            }

            event.preventDefault();

            var siguiente = campos[index + 1];

            if (siguiente) {
                siguiente.focus();

                if (
                    siguiente.tagName === 'INPUT'
                    &&
                    siguiente.type !== 'file'
                    &&
                    typeof siguiente.select === 'function'
                ) {
                    siguiente.select();
                }

                return;
            }

            // Si ya estás en el último campo, recién ahí manda el formulario.
            var boton = form.querySelector('button[type="submit"]');
            if (boton) {
                boton.focus();
                boton.click();
            }
        });
    }

    function iniciarCuentasV100() {
        abrirCuentasDesdeUrl();
        instalarEnterCuentas();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarCuentasV100);
    } else {
        iniciarCuentasV100();
    }

    window.addEventListener('load', iniciarCuentasV100);
})();



// ==========================================================================
// STERAKFOOD V102 - BUSCADOR INMEDIATO DE CUENTAS
// Busca nombre, teléfono o nota; filtra estado y mantiene los acordeones.
// ==========================================================================
(function () {
    function iniciarBuscadorCuentasV102() {
        var panel = document.getElementById('tab-cuentas');
        if (!panel || panel.dataset.buscadorCuentasV102 === '1') return;
        panel.dataset.buscadorCuentasV102 = '1';

        var entrada = panel.querySelector('#cuentas-buscar');
        var estado = panel.querySelector('#cuentas-filtro-estado');
        var borrar = panel.querySelector('#cuentas-limpiar');
        var contador = panel.querySelector('#cuentas-resultados');
        var vacio = panel.querySelector('#cuentas-sin-resultados');
        if (!entrada || !estado) return;

        function normalizar(valor) {
            return String(valor || '').normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .toLocaleLowerCase('es')
                .trim();
        }

        // Leer el DOM cada vez: las tarjetas cambian por AJAX y no se recarga el panel.
        function filtrar() {
            var tarjetas = Array.prototype.slice.call(panel.querySelectorAll('.cuentas-lista .cuenta-card'));
            var catalogo = tarjetas.map(function (card) {
                return {
                    card: card,
                    texto: normalizar([
                        card.dataset.cuentaNombre,
                        card.dataset.cuentaTelefono,
                        card.dataset.cuentaNota
                    ].join(' ')),
                    estado: card.dataset.cuentaEstado || ''
                };
            });
            var palabras = normalizar(entrada.value).split(/\s+/).filter(Boolean);
            var tipo = estado.value;
            var visibles = 0;
            catalogo.forEach(function (item) {
                var coincideTexto = palabras.every(function (palabra) { return item.texto.includes(palabra); });
                var coincideEstado = tipo === 'todos' || item.estado === tipo;
                var mostrar = coincideTexto && coincideEstado;
                item.card.hidden = !mostrar;
                if (mostrar) visibles++;
            });
            if (contador) contador.textContent = visibles + ' de ' + catalogo.length;
            if (vacio) vacio.hidden = visibles !== 0 || catalogo.length === 0;
        }

        panel.addEventListener('sm-cuentas-actualizadas', filtrar);
        entrada.addEventListener('input', filtrar);
        estado.addEventListener('change', filtrar);
        if (borrar) borrar.addEventListener('click', function () {
            entrada.value = '';
            estado.value = 'todos';
            filtrar();
            entrada.focus();
        });

        filtrar();
    }

    // El Salón carga la sección Cuentas al abrirla; permitir iniciar el fragmento.
    window.sterakInitBuscadorCuentas = iniciarBuscadorCuentasV102;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarBuscadorCuentasV102);
    } else {
        iniciarBuscadorCuentasV102();
    }
})();

// San Martín v161 - Mozos sin recargas: formulario y lista quedan abiertos.
(function(){
  function init(){
    var form = document.getElementById('salon-form-agregar-mozo');
    var bloque = document.getElementById('salon-gestion-mozos');
    if (!form || !bloque || bloque.dataset.iniciado === '1') return;
    bloque.dataset.iniciado = '1';
    var csrf = form.querySelector('input[name="csrfmiddlewaretoken"]');
    var lista = bloque.querySelector('.salon-pos__personal-lista');
    function avisar(texto, error) {
      if (window.Swal) window.Swal.fire({toast:true,position:'top-end',icon:error?'error':'success',
        title:texto,timer:2600,showConfirmButton:false,background:'var(--card-bg)',color:'var(--text-color)'});
      else if (error) window.alert(texto);
    }
    function numerar() {
      lista.querySelectorAll('.salon-pos__personal-chip').forEach(function(chip,indice){
        var numero=chip.querySelector('.salon-pos__personal-numero');
        if (numero) numero.textContent=String(indice+1);
      });
    }
    form.addEventListener('submit', async function(event){
      event.preventDefault();
      var boton=form.querySelector('button[type="submit"]');
      if (boton) boton.disabled=true;
      try {
        var res=await fetch(form.action,{method:'POST',credentials:'same-origin',
          headers:{'X-CSRFToken':csrf.value,'X-Requested-With':'XMLHttpRequest'},body:new FormData(form)});
        var d=await res.json().catch(function(){return {};});
        if(!res.ok||d.status!=='ok') throw Error(d.mensaje || 'No se pudo agregar el mozo.');
        lista.querySelectorAll('small').forEach(function(el){el.remove();});
        var chip=document.createElement('span');chip.className='salon-pos__personal-chip';
        var numero=document.createElement('b');numero.className='salon-pos__personal-numero';
        var etiqueta=document.createTextNode(' '+d.mozo.nombre+' ');
        var borrar=document.createElement('button');borrar.type='button';borrar.textContent='×';
        borrar.title='Eliminar mozo';borrar.dataset.salonBorrarMozo=d.mozo.eliminar_url;borrar.dataset.nombre=d.mozo.nombre;
        chip.append(numero,etiqueta,borrar);lista.appendChild(chip);numerar();
        form.reset();form.querySelector('input[name="nombre"]').focus({preventScroll:true});
        window.dispatchEvent(new CustomEvent('sm-mozos-modificados',{detail:{accion:'agregar',mozo:d.mozo}}));
        avisar('Mozo agregado: '+d.mozo.nombre);
      }catch(e){avisar(e.message||'Error al agregar mozo.',true);}
      finally{if(boton)boton.disabled=false;}
    });
    bloque.addEventListener('click', async function(event){
      var boton=event.target.closest('[data-salon-borrar-mozo]');
      if(!boton) return;
      if(!window.confirm('¿Eliminar a '+(boton.dataset.nombre||'este mozo')+'?')) return;
      boton.disabled=true;
      try {
        var res=await fetch(boton.dataset.salonBorrarMozo,{method:'POST',credentials:'same-origin',
          headers:{'X-CSRFToken':csrf.value,'X-Requested-With':'XMLHttpRequest'}});
        var d=await res.json().catch(function(){return {};});
        if(!res.ok||d.status!=='ok') throw Error(d.mensaje||'No se pudo eliminar el mozo.');
        var nombre=boton.dataset.nombre;
        var id=Number((boton.dataset.salonBorrarMozo.match(/\/(\d+)\/eliminar\/?$/)||[])[1]||0);
        boton.closest('.salon-pos__personal-chip').remove();numerar();
        window.dispatchEvent(new CustomEvent('sm-mozos-modificados',{detail:{accion:'eliminar',mozo:{id:id,nombre:nombre}}}));
        avisar('Mozo eliminado: '+nombre);
      }catch(e){boton.disabled=false;avisar(e.message||'Error al eliminar mozo.',true);}
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

// SAN MARTIN v163 - Cuentas sin recargas y saldar deuda en una sola accion.
(function () {
    'use strict';
    function iniciar() {
        var panel = document.getElementById('tab-cuentas');
        if (!panel || panel.dataset.ajaxCuentasV163 === '1') return;
        panel.dataset.ajaxCuentasV163 = '1';
        var lista = panel.querySelector('.cuentas-lista');
        var aviso = panel.querySelector('#cuentas-ajax-mensaje');
        if (!lista) return;

        function informar(mensaje, error) {
            if (aviso) {
                aviso.hidden = false;
                aviso.textContent = mensaje;
                aviso.classList.toggle('is-error', Boolean(error));
            }
            if (window.Swal) {
                window.Swal.fire({
                    toast: true, position: 'top-end',
                    icon: error ? 'error' : 'success',
                    title: mensaje, timer: error ? 4300 : 2600,
                    showConfirmButton: false,
                    background: 'var(--card-bg)', color: 'var(--text-color)'
                });
            }
        }

        function moneda(valor) {
            var numero = Number(valor);
            return '$' + (Number.isFinite(numero) ? numero.toLocaleString('es-AR', {minimumFractionDigits:0,maximumFractionDigits:2}) : '0');
        }

        function actualizarDatos(data, form, eraNueva) {
            var totalDeuda = panel.querySelector('[data-cuentas-total-deuda]');
            var totalFavor = panel.querySelector('[data-cuentas-total-favor]');
            if (totalDeuda) totalDeuda.textContent = moneda(data.total_deuda);
            if (totalFavor) totalFavor.textContent = moneda(data.total_favor);
            var id = 'cuenta-' + String(data.cuenta_id);
            var vieja = document.getElementById(id);

            if (data.eliminada) {
                if (vieja) vieja.remove();
            } else if (data.html) {
                var contenedor = document.createElement('template');
                contenedor.innerHTML = data.html.trim();
                var tarjeta = contenedor.content.firstElementChild;
                if (!tarjeta || !tarjeta.matches('.cuenta-card')) {
                    throw new Error('El servidor devolvio una ficha incompleta.');
                }
                if (vieja) {
                    tarjeta.open = vieja.open;
                    vieja.replaceWith(tarjeta);
                } else {
                    // Crear una cuenta nueva sin mover ni cerrar las otras fichas.
                    var tarjetas = Array.from(lista.querySelectorAll('.cuenta-card'));
                    var siguiente = tarjetas.find(function (c) {
                        return c.dataset.cuentaNombre.localeCompare(tarjeta.dataset.cuentaNombre, 'es', {sensitivity:'base'}) > 0;
                    });
                    if (siguiente) lista.insertBefore(tarjeta, siguiente);
                    else lista.appendChild(tarjeta);
                }
            }

            var totalTarjetas = lista.querySelectorAll('.cuenta-card').length;
            var vacioGeneral = lista.querySelector('.cuentas-vacio');
            if (totalTarjetas && vacioGeneral) vacioGeneral.remove();
            if (!totalTarjetas && !vacioGeneral) {
                var vacio = document.createElement('div');
                vacio.className = 'cuentas-vacio';
                vacio.textContent = 'Todavía no hay cuentas. Creá una arriba para empezar.';
                lista.prepend(vacio);
            }
            panel.dispatchEvent(new CustomEvent('sm-cuentas-actualizadas'));
            if (eraNueva) {
                form.reset();
                var nombre = form.querySelector('input[name="nombre"]');
                if (nombre) nombre.focus({preventScroll:true});
            } else if (!data.eliminada && form.matches('.cuenta-mov-form')) {
                var tarjetaAbierta = document.getElementById(id);
                if (tarjetaAbierta) {
                    var monto = tarjetaAbierta.querySelector('.cuenta-mov-form [name="monto"]');
                    if (monto) monto.focus({preventScroll:true});
                }
            }
        }

        // La captura evita el onsubmit antiguo que forzaba navegar y confirmar 2 veces.
        panel.addEventListener('submit', async function (event) {
            var form = event.target;
            if (!panel.contains(form) || !form.matches('form[data-cuenta-ajax]')) return;
            event.preventDefault();
            event.stopPropagation();
            if (form.dataset.enviando === '1') return;

            var pregunta = form.dataset.confirm || '';
            if (form.matches('.cuenta-saldar-form')) {
                // Confirmar que se cobro realmente: saldar NO significa perdonar la deuda.
                pregunta += '\nEsto registra un PAGO en la cuenta; no elimina movimientos ni genera ingreso en caja.';
            }
            if (pregunta && !window.confirm(pregunta)) return;

            var boton = form.querySelector('button[type="submit"]');
            var eraNueva = form.classList.contains('cuentas-form-card');
            form.dataset.enviando = '1';
            if (boton) boton.disabled = true;
            try {
                var datosFormulario = new FormData(form);
                var token = datosFormulario.get('csrfmiddlewaretoken');
                if (!token) throw new Error('Falta el token de seguridad del formulario.');
                var respuesta = await fetch(form.action, {
                    method: 'POST', body: datosFormulario, credentials: 'same-origin',
                    headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': token}
                });
                var datos = await respuesta.json().catch(function () { return {}; });
                if (!respuesta.ok || datos.status !== 'ok') {
                    throw new Error(datos.mensaje || 'No se pudo guardar. Comproba la conexion o volve a iniciar sesion.');
                }
                actualizarDatos(datos, form, eraNueva);
                informar(datos.mensaje || 'Cuenta actualizada.', false);
            } catch (error) {
                informar(error.message || 'No se pudo actualizar la cuenta.', true);
            } finally {
                form.dataset.enviando = '';
                if (boton && boton.isConnected) boton.disabled = false;
            }
        }, true);
    }
    window.sterakInitAjaxCuentas = iniciar;
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
    else iniciar();
})();

// SterakFood v105 - Reimpresión desde Cuentas sin navegar fuera del panel
(function () {
    function obtenerTokenCSRF() {
        var campo = document.querySelector('.cuentas-form-card input[name="csrfmiddlewaretoken"]');
        if (campo && campo.value) return campo.value;
        var cookie = document.cookie.split(';').map(function (x) { return x.trim(); }).find(function (x) {return x.startsWith('csrftoken=');});
        return cookie ? decodeURIComponent(cookie.substring(10)) : '';
    }
    document.addEventListener('click', function (event) {
        var boton = event.target.closest('#tab-cuentas [data-cuenta-imprimir-url]');
        if (!boton || boton.disabled) return;
        event.preventDefault();
        var url = boton.getAttribute('data-cuenta-imprimir-url');
        boton.disabled = true;
        fetch(url, {method:'POST', headers:{'X-CSRFToken': obtenerTokenCSRF()}})
            .then(function (res) {
                return res.json().then(function (data) {
                    if (!res.ok || data.status !== 'ok') throw new Error(data.mensaje || 'No se pudo solicitar la impresión.');
                    return data;
                });
            }).then(function (data) {
                Swal.fire({toast:true,position:'top-end',icon:'success',title:data.mensaje || 'Ticket enviado a caja',timer:2500,showConfirmButton:false,background:'var(--card-bg)',color:'var(--text-color)'});
            }).catch(function (error) {
                Swal.fire({icon:'error',title:'No se pudo imprimir',text:error.message || 'Error de conexión.',background:'var(--card-bg)',color:'var(--text-color)'});
            }).finally(function () {boton.disabled=false;});
    });
})();


// ==========================================================================
// SAN MARTÍN V111 - EDITOR RÁPIDO DEL CATÁLOGO PRIVADO DE SALÓN
// ==========================================================================
(function () {
    'use strict';

    function iniciarEditorSalonV111() {
        var panel = document.getElementById('salon-editor-codigos');
        if (!panel || panel.dataset.editorSalonV111 === '1') return;
        panel.dataset.editorSalonV111 = '1';

        var inputBuscar = document.getElementById('salon-catalogo-buscar');
        var lista = document.getElementById('salon-catalogo-lista');
        var contador = document.getElementById('salon-catalogo-contador');
        var mensaje = document.getElementById('salon-catalogo-mensaje');
        var recargar = document.getElementById('salon-catalogo-recargar');
        var productos = [];
        var cargando = false;
        var cargado = false;
        var maxVisibles = 40;

        function normalizar(valor) {
            return String(valor || '').normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .toLocaleLowerCase('es').trim();
        }
        function escapar(valor) {
            return String(valor === undefined || valor === null ? '' : valor)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }
        function avisar(texto, error) {
            mensaje.textContent = texto || '';
            mensaje.classList.toggle('is-error', Boolean(error));
        }
        function tokenCsrf() {
            var campo = document.querySelector('#salon-csrf-form input[name="csrfmiddlewaretoken"]');
            if (campo && campo.value) return campo.value;
            var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
            return match ? decodeURIComponent(match[1]) : '';
        }
        function precioVisible(valor) {
            // Base de datos usa punto decimal. Se permite editar el importe.
            return String(valor === undefined || valor === null ? '0' : valor);
        }
        function renderizar() {
            lista.textContent = '';
            if (!cargado) return;

            var busqueda = normalizar(inputBuscar.value);
            var palabras = busqueda.split(/\s+/).filter(Boolean);
            var encontrados = productos.filter(function (producto) {
                var campo = normalizar(producto.codigo + ' ' + producto.nombre);
                return palabras.every(function (p) { return campo.indexOf(p) !== -1; });
            });
            contador.textContent = encontrados.length + ' de ' + productos.length + ' productos';
            if (!encontrados.length) {
                var p = document.createElement('p');
                p.className = 'salon-catalogo__vacio';
                p.textContent = 'No encontramos productos con ese código o nombre.';
                lista.appendChild(p);
                return;
            }
            encontrados.slice(0, maxVisibles).forEach(function (producto) {
                var fila = document.createElement('article');
                fila.className = 'salon-catalogo__fila';
                fila.dataset.id = producto.id;
                fila.innerHTML =
                    '<div class="salon-catalogo__identidad">' +
                      '<span class="salon-catalogo__codigo">#' + escapar(producto.codigo) + '</span>' +
                      '<div class="salon-catalogo__nombre">' + escapar(producto.nombre) +
                      (!producto.disponible ? ' <small class="salon-catalogo__inactivo">Inactivo</small>' : '') +
                      '</div>' +
                    '</div>' +
                    '<label class="salon-catalogo__precio-label">Precio $' +
                      '<input class="salon-catalogo__precio" type="text" inputmode="decimal" aria-label="Precio de ' +
                      escapar(producto.nombre) + '" value="' + escapar(precioVisible(producto.precio)) + '">' +
                    '</label>' +
                    '<div class="salon-catalogo__acciones">' +
                      '<button type="button" class="salon-catalogo__guardar">Guardar</button>' +
                      '<button type="button" class="salon-catalogo__editar" aria-expanded="false">Editar</button>' +
                    '</div>' +
                    '<div class="salon-catalogo__extras" hidden>' +
                      '<label>Código<input type="text" class="salon-catalogo__codigo-input" inputmode="numeric" maxlength="20" value="' + escapar(producto.codigo) + '"></label>' +
                      '<label>Nombre<input type="text" class="salon-catalogo__nombre-input" maxlength="200" value="' + escapar(producto.nombre) + '"></label>' +
                      '<label class="salon-catalogo__disponibilidad"><input class="salon-catalogo__activo" type="checkbox"' +
                        (producto.disponible ? ' checked' : '') + '> Disponible en Salón POS</label>' +
                    '</div>';
                var inputPrecio = fila.querySelector('.salon-catalogo__precio');
                var botonGuardar = fila.querySelector('.salon-catalogo__guardar');
                var botonEditar = fila.querySelector('.salon-catalogo__editar');
                var extras = fila.querySelector('.salon-catalogo__extras');
                var inputCodigo = fila.querySelector('.salon-catalogo__codigo-input');
                var inputNombre = fila.querySelector('.salon-catalogo__nombre-input');
                var inputActivo = fila.querySelector('.salon-catalogo__activo');

                function guardar() {
                    if (botonGuardar.disabled) return;
                    var datos = {
                        codigo: inputCodigo.value.trim(),
                        nombre: inputNombre.value.trim(),
                        precio: inputPrecio.value.trim(),
                        disponible: inputActivo.checked
                    };
                    if (!datos.nombre || !datos.codigo || !datos.precio) {
                        avisar('Completá el código, el nombre y el precio.', true);
                        return;
                    }
                    botonGuardar.disabled = true;
                    botonEditar.disabled = true;
                    botonGuardar.textContent = 'Guardando...';
                    avisar('');
                    fetch(panel.dataset.editUrlTemplate.replace('999999', String(producto.id)), {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'X-CSRFToken': tokenCsrf(),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify(datos)
                    }).then(function (res) {
                        return res.json().then(function (data) {
                            if (!res.ok || data.status !== 'ok') {
                                throw Error(data.mensaje || 'No se pudo guardar.');
                            }
                            return data;
                        });
                    }).then(function (data) {
                        var actualizado = data.producto;
                        producto.codigo = actualizado.codigo;
                        producto.nombre = actualizado.nombre;
                        producto.precio = actualizado.precio;
                        producto.disponible = actualizado.disponible;
                        fila.querySelector('.salon-catalogo__codigo').textContent = '#' + producto.codigo;
                        fila.querySelector('.salon-catalogo__nombre').textContent = producto.nombre;
                        inputPrecio.value = precioVisible(producto.precio);
                        extras.hidden = true;
                        botonEditar.setAttribute('aria-expanded', 'false');
                        botonEditar.textContent = 'Editar';
                        fila.classList.add('is-guardado');
                        setTimeout(function () { fila.classList.remove('is-guardado'); }, 1700);
                        avisar(data.mensaje || 'Cambios guardados.');

                        // Hace que el buscador del POS utilice el nuevo precio sin recargar.
                        window.dispatchEvent(new CustomEvent('salon-catalogo-actualizado', {
                            detail: actualizado
                        }));
                    }).catch(function (error) {
                        avisar(error.message || 'Error de conexión. Intentá otra vez.', true);
                    }).finally(function () {
                        botonGuardar.disabled = false;
                        botonEditar.disabled = false;
                        botonGuardar.textContent = 'Guardar';
                    });
                }

                botonGuardar.addEventListener('click', guardar);
                botonEditar.addEventListener('click', function () {
                    extras.hidden = !extras.hidden;
                    botonEditar.setAttribute('aria-expanded', String(!extras.hidden));
                    botonEditar.textContent = extras.hidden ? 'Editar' : 'Cerrar';
                    if (!extras.hidden) inputCodigo.focus();
                });
                [inputPrecio, inputCodigo, inputNombre].forEach(function (input) {
                    input.addEventListener('keydown', function (event) {
                        if (event.key === 'Enter') {
                            event.preventDefault();
                            guardar();
                        }
                    });
                });
                lista.appendChild(fila);
            });
            if (encontrados.length > maxVisibles) {
                var aviso = document.createElement('p');
                aviso.className = 'salon-catalogo__vacio';
                aviso.textContent = 'Mostrando los primeros ' + maxVisibles + ' resultados. Escribí más para encontrar otro artículo.';
                lista.appendChild(aviso);
            }
        }
        function cargar() {
            if (cargando) return;
            cargando = true;
            avisar('Cargando productos...');
            fetch(panel.dataset.listUrl, {credentials: 'same-origin', cache: 'no-store'})
                .then(function (res) {
                    return res.json().then(function (data) {
                        if (!res.ok || data.status !== 'ok') throw Error(data.mensaje || 'No se pudo cargar el catálogo.');
                        return data;
                    });
                })
                .then(function (data) {
                    productos = data.productos || [];
                    cargado = true;
                    avisar('');
                    renderizar();
                })
                .catch(function (error) { avisar(error.message, true); })
                .finally(function () { cargando = false; });
        }

        panel.addEventListener('toggle', function () {
            if (panel.open && !cargado) cargar();
        });
        inputBuscar.addEventListener('input', renderizar);
        recargar.addEventListener('click', cargar);
        if (panel.open) cargar();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarEditorSalonV111);
    } else {
        iniciarEditorSalonV111();
    }
})();


/* ==========================================================================
   SAN MARTIN V118 — WHEEL SCROLL EN COMANDA DEL SALON
   ========================================================================== */
(function () {
    function iniciarWheelComandaSalon() {
        var modal = document.getElementById('salon-comanda-modal');
        var lista = document.getElementById('lista-comanda');
        if (!modal || !lista || modal.dataset.wheelScrollInit === '1') return;
        modal.dataset.wheelScrollInit = '1';

        modal.addEventListener('wheel', function (event) {
            if (!lista || lista.hidden) return;
            if (lista.scrollHeight <= lista.clientHeight) return;

            var editable = event.target.closest('input, textarea, select');
            var estaEnLista = !!event.target.closest('#lista-comanda');
            if (estaEnLista) return;
            if (editable && !event.target.closest('.salon-pos__actionbar--pos')) return;

            lista.scrollTop += event.deltaY;
            event.preventDefault();
        }, { passive: false });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarWheelComandaSalon);
    } else {
        iniciarWheelComandaSalon();
    }
})();

// SAN MARTIN V120 — Ventanas independientes para Mozos, Importar y Editar catálogo.
(function () {
    function iniciarModalesSalonV120() {
        var salon = document.getElementById('salon-pos') || document.getElementById('tab-config');
        if (!salon || salon.dataset.herramientasV120 === '1') return;
        salon.dataset.herramientasV120 = '1';
        var modalActual = null;
        var botonAnterior = null;
        function cerrar() {
            if (!modalActual) return;
            var bloque = modalActual.querySelector('details.salon-pos__tool');
            if (bloque) bloque.open = false;
            modalActual.hidden = true;
            modalActual.setAttribute('aria-hidden', 'true');
            modalActual = null;
            document.body.classList.remove('salon-tools-modal-open');
            if (botonAnterior && document.contains(botonAnterior)) botonAnterior.focus();
            botonAnterior = null;
        }
        function abrir(tipo, boton) {
            var modal = document.getElementById('salon-tool-dialog-' + tipo);
            if (!modal) return;
            cerrar();
            // Cerrar el desplegable al mostrar el editor; el usuario permanece en Mesas.
            var desplegable = document.getElementById('salon-menu-herramientas');
            if (desplegable) desplegable.open = false;
            modalActual = modal;
            botonAnterior = boton;
            modal.hidden = false;
            modal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('salon-tools-modal-open');
            var bloque = modal.querySelector('details.salon-pos__tool');
            if (bloque) bloque.open = true; // El editor AJAX escucha este 'toggle'.
            var foco = modal.querySelector('input[type="text"],input[type="search"],input[type="file"],.salon-pos__tool-cerrar');
            if (foco) foco.focus({preventScroll: true});
        }
        salon.addEventListener('click', function (event) {
            var abrirBoton = event.target.closest('[data-salon-tool-open]');
            if (abrirBoton) {
                event.preventDefault();
                abrir(abrirBoton.getAttribute('data-salon-tool-open'), abrirBoton);
                return;
            }
            if (event.target.closest('[data-salon-tool-close]')) {
                event.preventDefault();
                cerrar();
            }
        });
        document.addEventListener('keydown', function (event) {
            if (!modalActual) return;
            if (event.key === 'Escape') {
                event.preventDefault();
                event.stopPropagation();
                cerrar();
                return;
            }
            if (event.key !== 'Tab') return;
            var selectores = 'button:not([disabled]):not([tabindex="-1"]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]';
            var posibles = Array.prototype.slice.call(modalActual.querySelectorAll(selectores));
            var visibles = posibles.filter(function (el) { return el.getClientRects().length > 0; });
            if (!visibles.length) return;
            var primero = visibles[0], ultimo = visibles[visibles.length - 1];
            if (event.shiftKey && document.activeElement === primero) { event.preventDefault(); ultimo.focus(); }
            else if (!event.shiftKey && document.activeElement === ultimo) { event.preventDefault(); primero.focus(); }
        }, true);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciarModalesSalonV120);
    else iniciarModalesSalonV120();
})();


// San Martín v131: sondeo FEDummy, SOLO homologación; sin factura ni credenciales.
(function () {
    function iniciarPruebaArca() {
        var formulario = document.getElementById('fiscal-probar-arca-form');
        var resultado = document.getElementById('fiscal-probar-arca-resultado');
        if (!formulario || !resultado) return;
        formulario.addEventListener('submit', async function (ev) {
            ev.preventDefault();
            var boton = formulario.querySelector('button[type="submit"]');
            boton.disabled = true;
            resultado.textContent = 'Consultando ARCA (homologación)...';
            resultado.className = 'fiscal-prep__estado';
            try {
                var datos = new FormData(formulario);
                var respuesta = await fetch(formulario.action, {
                    method: 'POST', body: datos, credentials: 'same-origin',
                    headers: {'Accept':'application/json'},
                });
                var cuerpo = await respuesta.json();
                if (!respuesta.ok || cuerpo.status === 'error') {
                    throw new Error(cuerpo.mensaje || 'La conexión falló.');
                }
                var estados = cuerpo.estados || {};
                resultado.classList.add(cuerpo.status === 'ok' ? 'fiscal-prep__estado--ok' : 'fiscal-prep__estado--aviso');
                resultado.textContent = (cuerpo.mensaje || 'Respuesta de homologación.') +
                    ' AppServer: ' + (estados.AppServer || '-') +
                    ' · DbServer: ' + (estados.DbServer || '-') +
                    ' · AuthServer: ' + (estados.AuthServer || '-') +
                    '. Esto NO confirma permisos para facturar.';
            } catch (error) {
                resultado.classList.add('fiscal-prep__estado--error');
                resultado.textContent = 'Prueba fallida: ' + (error.message || 'Error desconocido.');
            } finally {
                boton.disabled = false;
            }
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciarPruebaArca);
    else iniciarPruebaArca();
})();


// v157: un solo botón de reinicio con doble clic de confirmación, sin cuadro modal.
(function(){
    'use strict';
    function csrfToken(){
        var input=document.querySelector('input[name="csrfmiddlewaretoken"]');
        if(input&&input.value)return input.value;
        var m=document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m?decodeURIComponent(m[1]):'';
    }
    window.smReiniciarHistorialVentas=function(url,alTerminar,boton){
        if(!url||!boton)return;
        if(boton.dataset.cargando==='1')return;
        if(boton.dataset.confirmar!=='1'){
            boton.dataset.confirmar='1';
            boton.dataset.etiquetaOriginal=boton.textContent;
            boton.textContent='¿Confirmar reinicio? Volvé a pulsar';
            boton.title='Segundo clic: reinicia el historial visible; no elimina deudores ni ventas originales';
            setTimeout(function(){
                if(boton.isConnected&&boton.dataset.confirmar==='1'){
                    boton.dataset.confirmar='0';boton.textContent=boton.dataset.etiquetaOriginal;
                }
            },8000);
            return;
        }
        boton.dataset.confirmar='0';boton.dataset.cargando='1';boton.disabled=true;
        boton.textContent='Reiniciando...';
        fetch(url,{method:'POST',credentials:'same-origin',
            headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken()},
            body:JSON.stringify({confirmacion:'REINICIAR'})
        }).then(function(r){return r.json().then(function(d){if(!r.ok||d.status!=='ok')throw new Error(d.mensaje||'Error al reiniciar');return d;});})
          .then(function(d){
              boton.dataset.cargando='0';
              boton.textContent='✓ Historial reiniciado ('+d.cantidad_archivada+')';
              if(typeof alTerminar==='function')alTerminar();
              else window.location.reload();
          }).catch(function(e){
              boton.dataset.cargando='0';boton.disabled=false;
              boton.textContent='Error: '+(e.message||'No se pudo reiniciar');
              setTimeout(function(){if(boton.isConnected){boton.textContent=boton.dataset.etiquetaOriginal||'Reiniciar historial';}},5000);
          });
    };
    document.addEventListener('DOMContentLoaded',function(){
        var b=document.getElementById('sm-reiniciar-ventas-panel');
        if(b)b.addEventListener('click',function(){
            window.smReiniciarHistorialVentas(b.getAttribute('data-reset-url'),null,b);
        });
    });
})();

// v157: impresión. Render guarda opciones, el agente Windows las consulta por clave.
(function(){
    'use strict';
    function iniciar(){
        var root=document.getElementById('sm-impresoras-panel');
        if(!root)return;
        var form=document.getElementById('sm-impresoras-form');
        var msg=document.getElementById('sm-impresoras-mensaje');
        var estado=document.getElementById('sm-impresoras-estado');
        var vincular=document.getElementById('sm-impresoras-vincular');
        var btnAbrir=document.getElementById('sm-impresoras-abrir');
        var dialogo=document.getElementById('sm-impresoras-dialogo');
        var focoAnterior=null;
        function cerrarDialogo(){
            if(!dialogo||dialogo.hidden)return;
            dialogo.hidden=true;
            document.body.style.overflow='';
            if(focoAnterior&&focoAnterior.isConnected)focoAnterior.focus({preventScroll:true});
        }
        if(btnAbrir&&dialogo){
            btnAbrir.addEventListener('click',function(){
                focoAnterior=document.activeElement;
                dialogo.hidden=false;
                document.body.style.overflow='hidden';
                var primerCampo=form.querySelector('input');
                if(primerCampo)primerCampo.focus({preventScroll:true});
            });
            dialogo.querySelectorAll('[data-impresoras-cerrar]').forEach(function(btn){
                btn.addEventListener('click',cerrarDialogo);
            });
            document.addEventListener('keydown',function(ev){
                if(dialogo.hidden)return;
                if(ev.key==='Escape'){ev.preventDefault();ev.stopPropagation();cerrarDialogo();return;}
                if(ev.key!=='Tab')return;
                var els=Array.from(dialogo.querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),summary')).filter(function(el){return el.getClientRects().length>0&&el.tabIndex!==-1;});
                if(!els.length)return;
                if(ev.shiftKey&&document.activeElement===els[0]){ev.preventDefault();els[els.length-1].focus();}
                else if(!ev.shiftKey&&document.activeElement===els[els.length-1]){ev.preventDefault();els[0].focus();}
            },true);
        }
        function csrf(){
            var input=document.querySelector('input[name="csrfmiddlewaretoken"]');
            if(input&&input.value)return input.value;
            var m=document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
            return m?decodeURIComponent(m[1]):'';
        }
        function fill(d){
            ['caja_windows','ip_cocina','ip_barra','ancho_ticket'].forEach(function(k){if(form.elements[k]&&d[k]!=null)form.elements[k].value=d[k];});
            estado.textContent=!d.vinculada?'Sin PC vinculada':d.ultima_conexion?'Última conexión: '+new Date(d.ultima_conexion).toLocaleString('es-AR'):'Clave generada · Aún no conectada';
        }
        function send(url,payload){
            return fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify(payload||{})})
              .then(function(r){return r.json().then(function(d){if(!r.ok||d.status!=='ok')throw Error(d.mensaje||'No se pudo guardar');return d;});});
        }
        fetch(root.dataset.leer,{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
            if(d.status!=='ok')throw Error(d.mensaje||'Sin permiso');
            fill(d.configuracion);
        }).catch(function(e){estado.textContent='No se pudo leer: '+e.message;});
        form.addEventListener('submit',function(ev){
            ev.preventDefault();
            var data={};['caja_windows','ip_cocina','ip_barra','ancho_ticket'].forEach(function(k){data[k]=form.elements[k].value;});
            msg.textContent='Guardando...';
            send(root.dataset.guardar,data).then(function(d){fill(d.configuracion);msg.textContent='✓ Guardado. La ticketera vinculada tomará el cambio al consultar Render.';})
              .catch(function(e){msg.textContent='Error: '+e.message;});
        });
        vincular.addEventListener('click',function(){
            if(!window.confirm('¿Generar una nueva clave? Si la PC ya estaba vinculada, la clave anterior dejará de servir.'))return;
            vincular.disabled=true;msg.textContent='Preparando vinculación...';
            send(root.dataset.vincular,{}).then(function(d){
                var blob=new Blob([JSON.stringify(d.archivo,null,2)],{type:'application/json'});
                var url=URL.createObjectURL(blob);var a=document.createElement('a');
                a.href=url;a.download=d.nombre_archivo||'VINCULAR_IMPRESORA_SAN_MARTIN.json';
                document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url);},1000);
                msg.textContent='Clave descargada. Copiala en datos_locales como impresoras_config.json. No la compartas.';
                estado.textContent='Esperando conexión desde la PC';
            }).catch(function(e){msg.textContent='Error: '+e.message;}).finally(function(){vincular.disabled=false;});
        });
    }
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',iniciar);else iniciar();
})();

// Alta de producto en iframe seguro del propio dominio, sin cerrar la mesa ni recargar.
window.addEventListener('message', function(event){
    var iframe=document.getElementById('salon-form-producto-iframe');
    if (!iframe || event.origin!==window.location.origin || event.source!==iframe.contentWindow) return;
    var datos=event.data||{};
    if (datos.tipo==='sm-producto-cerrar') {
        var cerrar=document.querySelector('#salon-tool-dialog-producto [data-salon-tool-close="producto"]');
        if (cerrar) cerrar.click();
        return;
    }
    if (datos.tipo!=='sm-producto-guardado' || !datos.producto) return;
    var p=datos.producto;
    window.dispatchEvent(new CustomEvent('salon-catalogo-actualizado', {detail:p}));
    var actualizar=document.getElementById('salon-catalogo-recargar');
    if (actualizar) actualizar.click();
});
