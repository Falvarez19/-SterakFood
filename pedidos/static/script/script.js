// ==========================================================================
// MÓDULO 0: PANTALLA DE CARGA Y PORCENTAJE
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
    const porcentajeEl = document.getElementById("carga-porcentaje");
    if (porcentajeEl) {
        let progreso = 0;
        const intervalo = setInterval(() => {
            if (progreso < 90) {
                progreso += Math.floor(Math.random() * 15) + 5;
                if (progreso > 90)
                    progreso = 90;
                porcentajeEl.textContent = progreso + "%";
            }
        }, 80);
        window.addEventListener("load", function () {
            clearInterval(intervalo);
            porcentajeEl.textContent = "100%";
            setTimeout(() => {
                const preloader = document.getElementById("pantalla-carga");
                if (preloader) {
                    preloader.style.opacity = "0";
                    preloader.style.visibility = "hidden";
                    document.body.classList.remove("bloquear-scroll");
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
    const puesto = parametros.get("puesto") || "";
    fetch(`/carrito/agregar/${productoId}/?puesto=${puesto}`).then(respuesta => respuesta.json()).then(datos => {
        if (datos.status === "ok") {
            document.getElementById("badge-contador").innerText = datos.total_items;
            if (document.getElementById("carrito-sidebar").classList.contains("abierto")) {
                cargarDetalleCarrito();
            }
        }
    });
}
function abrirCarrito() {
    document.getElementById("carrito-sidebar").classList.add("abierto");
    document.getElementById("carrito-overlay").classList.add("activo");
    cargarDetalleCarrito();
}
function cerrarCarrito() {
    document.getElementById("carrito-sidebar").classList.remove("abierto");
    document.getElementById("carrito-overlay").classList.remove("activo");
}
function cargarDetalleCarrito() {
    fetch("/carrito/ver/").then(res => res.json()).then(datos => {
        const contenedor = document.getElementById("carrito-items");
        contenedor.innerHTML = "";
        if (datos.items.length === 0) {
            contenedor.innerHTML = "<p style=\"text-align:center; color:var(--texto-mutado); margin-top:20px;\">Tu carrito est\u00E1 vac\u00EDo.</p>";
            document.getElementById("carrito-precio-total").innerText = "0.00";
        }
        else {
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
            document.getElementById("carrito-precio-total").innerText = parseFloat(datos.total_general).toFixed(2);
        }
    });
}
function sumarItem(llave) {
    fetch(`/carrito/sumar/${llave}/`).then(res => res.json()).then(datos => {
        if (datos.status === "ok") {
            document.getElementById("badge-contador").innerText = datos.total_items;
            cargarDetalleCarrito();
        }
    });
}
function restarItem(llave) {
    fetch(`/carrito/restar/${llave}/`).then(res => res.json()).then(datos => {
        if (datos.status === "ok") {
            document.getElementById("badge-contador").innerText = datos.total_items;
            cargarDetalleCarrito();
        }
    });
}
function eliminarItem(llave) {
    fetch(`/carrito/eliminar/${llave}/`).then(res => res.json()).then(datos => {
        if (datos.status === "ok") {
            document.getElementById("badge-contador").innerText = datos.total_items;
            cargarDetalleCarrito();
        }
    });
}
function vaciarCarritoTotal() {
    Swal.fire({
        title: "\u00BFVaciar todo el pedido?",
        text: "Vas a eliminar todos los productos del carrito.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#dc3545",
        cancelButtonColor: "#6c757d",
        confirmButtonText: "S\u00ED, vaciar",
        cancelButtonText: "Cancelar"
    }).then(result => {
        if (result.isConfirmed) {
            fetch("/carrito/limpiar/").then(res => res.json()).then(datos => {
                if (datos.status === "ok") {
                    document.getElementById("badge-contador").innerText = "0";
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
    const total = document.getElementById("carrito-precio-total").innerText;
    if (total === "0.00" || total === "0") {
        Swal.fire({ icon: "info", title: "Carrito Vac\u00EDo", text: "Agreg\u00E1 algo rico antes de confirmar tu pedido.", confirmButtonColor: "#1e7b45" });
        return;
    }
    cerrarCarrito();
    document.getElementById("modal-entrega").classList.add("activo");
    document.body.style.overflow = "hidden";
    const parametros = new URLSearchParams(window.location.search);
    const puestoActual = parametros.get("puesto") || "";
    const labelMesa = document.getElementById("label-mesa");
    const radioMostrador = document.querySelector("input[name=\"tipo_entrega\"][value=\"mostrador\"]");
    const puestosSinMesa = ["kiosco", "barra", "parrilla", "foodtruck"];
    if (!labelMesa || puestosSinMesa.includes(puestoActual)) {
        if (labelMesa) labelMesa.style.display = "none";
        if (radioMostrador) radioMostrador.checked = true;
        toggleFormularioMesa();
    }
    else {
        if (labelMesa) labelMesa.style.display = "block";
        document.querySelectorAll("input[name=\"tipo_entrega\"]").forEach(r => r.checked = false);
        document.querySelectorAll("input[name=\"tipo_pago\"]").forEach(r => r.checked = false);
        toggleFormularioMesa();
    }
}
function cerrarModalEntrega() {
    document.getElementById("modal-entrega").classList.remove("activo");
    document.body.style.overflow = "auto";
}
function toggleFormularioMesa() {
    const opcionEntrega = document.querySelector("input[name=\"tipo_entrega\"]:checked");
    const formMesa = document.getElementById("form-mesa");
    const seccionPago = document.getElementById("seccion-pago");
    const opcionPago = document.querySelector("input[name=\"tipo_pago\"]:checked");
    const formTelefono = document.getElementById("form-telefono");
    if (seccionPago) {
        if (opcionEntrega) {
            seccionPago.classList.remove("oculto");
        }
        else {
            seccionPago.classList.add("oculto");
        }
    }
    if (formMesa) {
        if (opcionEntrega && opcionEntrega.value === "mesa") {
            formMesa.classList.remove("oculto");
            formMesa.style.display = "flex";
        }
        else {
            formMesa.classList.add("oculto");
            formMesa.style.display = "none";
        }
    }
    if (formTelefono) {
        if (opcionPago && opcionPago.value === "efectivo") {
            formTelefono.classList.remove("oculto");
            formTelefono.style.display = "flex";
        }
        else {
            formTelefono.classList.add("oculto");
            formTelefono.style.display = "none";
        }
    }
    actualizarResumenPago();
}

function actualizarResumenPago() {
    const resumen = document.getElementById("resumen-pago");
    const totalElemento = document.getElementById("carrito-precio-total");
    const totalFinalElemento = document.getElementById("modal-total-final");
    const totalOriginalElemento = document.getElementById("modal-total-original");
    const aviso = document.getElementById("modal-descuento-aviso");
    if (!resumen || !totalElemento || !totalFinalElemento) return;
    const totalOriginal = parseFloat(totalElemento.innerText) || 0;
    const pago = document.querySelector("input[name=\"tipo_pago\"]:checked");
    const descuentoActivo = resumen.dataset.descuentoActivo === "1";
    const porcentaje = parseFloat(resumen.dataset.descuentoPorcentaje) || 0;
    const aplicaDescuento = descuentoActivo && pago && pago.value === "efectivo" && porcentaje > 0;
    const totalFinal = aplicaDescuento ? totalOriginal * (1 - porcentaje / 100) : totalOriginal;
    totalFinalElemento.innerText = "$" + totalFinal.toFixed(2);
    if (totalOriginalElemento) {
        totalOriginalElemento.innerText = "$" + totalOriginal.toFixed(2);
        totalOriginalElemento.style.display = aplicaDescuento ? "inline" : "none";
    }
    if (aviso) aviso.style.display = aplicaDescuento ? "block" : "none";
}

// ==========================================================================
// MÓDULO 3: PROCESAMIENTO AJAX HACIA DJANGO Y PAGOS
// ==========================================================================

function validarYEnviar(event) {
    if (event)
        event.preventDefault();
    let nombreCliente = document.getElementById("nombre_cliente").value.trim();
    const telefonoInput = document.getElementById("telefono_cliente");
    const telefonoCliente = telefonoInput ? telefonoInput.value.trim() : "";
    const comentarios = document.getElementById("comentarios_pedido") ? document.getElementById("comentarios_pedido").value.trim() : "";
    const tipoEntregaElement = document.querySelector("input[name=\"tipo_entrega\"]:checked");
    const tipoPagoElement = document.querySelector("input[name=\"tipo_pago\"]:checked");
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    if (!tipoEntregaElement || !tipoPagoElement) {
        Swal.fire({ icon: "warning", title: "Faltan datos", text: "Por favor complet\u00E1 opciones de entrega y pago.", confirmButtonColor: "#ff6600" });
        return;
    }
    const tipoEntrega = tipoEntregaElement.value;
    const tipoPago = tipoPagoElement.value;
    let numeroMesa = "";
    if (nombreCliente === "") {
        Swal.fire({ icon: "warning", title: "Falta tu nombre", text: "Escrib\u00ED tu nombre y apellido para identificarte.", confirmButtonColor: "#ff6600" });
        return;
    }
    if (tipoPago === "efectivo" && telefonoCliente === "") {
        Swal.fire({ icon: "warning", title: "Tel\u00E9fono requerido", text: "Por favor dejanos tu WhatsApp para coordinar el pago.", confirmButtonColor: "#ff6600" });
        return;
    }
    if (tipoEntrega === "mesa") {
        numeroMesa = document.getElementById("numero_mesa").value.trim();
        if (numeroMesa === "") {
            Swal.fire({ icon: "warning", title: "N\u00FAmero de Mesa", text: "Ingres\u00E1 el n\u00FAmero de mesa donde est\u00E1s.", confirmButtonColor: "#ff6600" });
            return;
        }
    }
    let comentariosFinales = comentarios;
    if (tipoEntrega === "mesa") {
        const checkArmar = document.getElementById("armar_mesa");
        if (checkArmar && checkArmar.checked) {
            comentariosFinales = comentariosFinales ? comentariosFinales + " | FALTA ARMAR MESA" : "FALTA ARMAR MESA";
        }
    }
    if (comentariosFinales !== "")
        nombreCliente = `${nombreCliente} (Nota: ${comentariosFinales})`.substring(0, 99);
    Swal.fire({
        title: "Procesando...",
        text: "\u00A1Llevando el pedido a toda velocidad!",
        showConfirmButton: false,
        allowOutsideClick: false,
        allowEscapeKey: false,
        background: "var(--card-bg)",
        color: "var(--text-color)",
        didOpen: () => {
            Swal.showLoading();
        },
        customClass: {
            popup: "alerta-con-marco"
        }
    });
    const formData = new FormData();
    formData.append("nombre_cliente", nombreCliente);
    formData.append("telefono_cliente", telefonoCliente);
    formData.append("tipo_entrega", tipoEntrega);
    formData.append("numero_mesa", numeroMesa);
    formData.append("tipo_pago", tipoPago);
    fetch("/procesar/", { method: "POST", body: formData, headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrfToken } }).then(res => res.json()).then(datos => {
        if (datos.status === "ok") {
            cerrarModalEntrega();
            if (tipoPago === "mercadopago") {
                if (datos.mp_id)
                    window.location.href = `https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=${datos.mp_id}`;
                else
                    Swal.fire({ icon: "error", title: "Error de cobro", text: "El servidor no gener\u00F3 el link de Mercado Pago." });
            }
            else if (tipoPago === "nave") {
                if (datos.nave_url) {
                    window.location.href = datos.nave_url;
                }
                else {
                    Swal.fire({
                        title: "\u00A1MODO / Nave!",
                        text: "Estamos terminando de configurar la conexi\u00F3n con Nave. \u00A1Estar\u00E1 lista muy pronto!",
                        icon: "info",
                        confirmButtonColor: "#ff6600"
                    });
                }
            }
            else if (tipoPago === "efectivo") {
                let fraseUbicacion = tipoEntrega === "mesa" ? `ando en la mesa ${numeroMesa}` : `pedí para retirar en el mostrador`;
                let mensajeWa = `Hola soy ${document.getElementById("nombre_cliente").value.trim()}, ${fraseUbicacion}, mi número de pedido es #${datos.pedido_id} y lo quiero confirmar para acercarme a pagarlo o avísame si me cobras cuando el pedido llegue a la mesa.`;
                let numeroBuffet = "5491178246455";
                let linkWa = `https://wa.me/${numeroBuffet}?text=${encodeURIComponent(mensajeWa)}`;
                Swal.fire({
                    title: "\u00A1Pedido Registrado!",
                    text: "Toca el bot\u00F3n para enviarnos un WhatsApp y confirmarnos tu pago.",
                    icon: "success",
                    confirmButtonText: "Enviar WhatsApp \uD83D\uDCAC",
                    confirmButtonColor: "#25D366",
                    allowOutsideClick: false
                }).then(() => {
                    window.open(linkWa, "_blank");
                    setTimeout(() => {
                        window.location.href = `/seguimiento/${datos.pedido_id}/`;
                    }, 500);
                });
            }
            else {
                window.location.href = `/seguimiento/${datos.pedido_id}/`;
            }
        }
        else {
            Swal.fire({ icon: "error", title: "Oops...", text: "Error: " + datos.mensaje });
        }
    }).catch(error => {
        Swal.fire({ icon: "error", title: "Error de red", text: "No se pudo conectar con el servidor." });
    });
}

// ==========================================================================
// MÓDULO 4: OPCIONES Y PERSONALIZACIÓN DE PRODUCTOS
// ==========================================================================

function actualizarPrecioVisual(contenedor) {
    if (!contenedor) {
        return;
    }
    const tarjeta = contenedor.closest(".tarjeta-producto");
    if (!tarjeta) {
        return;
    }
    const precioElement = tarjeta.querySelector(".precio");
    if (!precioElement) {
        return;
    }
    if (!precioElement.dataset.precioOriginal) {
        const precioBaseTexto = precioElement.innerText.replace("$", "").replace(",", ".");
        precioElement.dataset.precioOriginal = parseFloat(precioBaseTexto);
    }
    let precioActual = parseFloat(precioElement.dataset.precioOriginal);
    contenedor.querySelectorAll("input:checked").forEach(input => {
        const texto = input.value;
        if (texto.includes("(+")) {
            const extra = parseFloat(texto.split("(+")[1].split(")")[0]);
            if (!isNaN(extra)) {
                precioActual += extra;
            }
        }
        if (texto.includes("(-")) {
            const descuento = parseFloat(texto.split("(-")[1].split(")")[0]);
            if (!isNaN(descuento)) {
                precioActual -= descuento;
            }
        }
    });
    precioElement.innerText = "$" + precioActual.toFixed(2);
    precioElement.style.transition = "all 0.3s ease";
    precioElement.style.transform = "scale(1.15)";
    precioElement.style.color = "var(--naranja-sterak)";
    setTimeout(() => {
        precioElement.style.transform = "scale(1)";
        precioElement.style.color = "";
    }, 300);
}
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".opciones-contenedor").forEach((contenedor, indiceContenedor) => {
        const atributos = [
            {
                nombre: "Variante",
                valor: contenedor.dataset.variante,
                clave: "variante",
                tipo: "radio"
            },
            {
                nombre: "Guarnici\u00F3n",
                valor: contenedor.dataset.guarnicion,
                clave: "guarnicion",
                tipo: "radio"
            },
            {
                nombre: "Punto de cocci\u00F3n",
                valor: contenedor.dataset.punto,
                clave: "punto",
                tipo: "radio"
            },
            {
                nombre: "Relleno",
                valor: contenedor.dataset.relleno,
                clave: "relleno",
                tipo: "radio"
            },
            {
                nombre: "Salsa",
                valor: contenedor.dataset.salsa,
                clave: "salsa",
                tipo: "radio"
            },
            {
                nombre: "Hielo",
                valor: contenedor.dataset.hielo,
                clave: "hielo",
                tipo: "radio"
            },
            {
                nombre: "Adicional",
                valor: contenedor.dataset.adicional,
                clave: "adicional",
                tipo: "checkbox"
            }
        ];
        let tieneOpciones = false;
        const wrapper = document.createElement("div");
        wrapper.className = "opciones-wrapper";
        wrapper.style.display = "none";
        wrapper.style.flexDirection = "column";
        wrapper.style.gap = "8px";
        const tarjetaProducto = contenedor.closest(".tarjeta-producto");
        const nombreDelPlato = tarjetaProducto ? tarjetaProducto.querySelector("h3").innerText.toLowerCase() : "";
        const esPlatoDeHuevo = nombreDelPlato.includes("omel") || nombreDelPlato.includes("tortilla");
        atributos.forEach(attr => {
            if (attr.valor && attr.valor.trim() !== "") {
                tieneOpciones = true;
                const grupo = document.createElement("div");
                grupo.className = "opciones-grupo grupo-" + attr.clave + "-" + contenedor.dataset.id;
                grupo.dataset.clave = attr.clave;
                grupo.dataset.requerido = (attr.tipo === "radio") ? "true" : "false";
                const txtOpcional = (attr.tipo === "checkbox") ? " (Opcional)" : "";
                grupo.innerHTML = "<div class=\"opciones-titulo\">" + "Eleg\u00ED " + attr.nombre + txtOpcional + ":" + "</div>";
                attr.valor.split(",").forEach(opcion => {
                    const label = document.createElement("label");
                    label.className = "opcion-item";
                    const input = document.createElement("input");
                    input.type = attr.tipo;
                    input.value = opcion.trim();
                    if (attr.tipo === "radio") {
                        input.name = "radio-" + attr.clave + "-" + contenedor.dataset.id + "-" + indiceContenedor;
                    }
                    else {
                        input.className = "chk-adicional-" + contenedor.dataset.id;
                    }
                    input.addEventListener("change", () => {
                        grupo.classList.remove("error");
                        actualizarPrecioVisual(contenedor);
                    });
                    const marcador = document.createElement("div");
                    marcador.className = "opcion-marcador";
                    label.appendChild(input);
                    label.appendChild(marcador);
                    label.appendChild(document.createTextNode(opcion.trim()));
                    grupo.appendChild(label);
                });
                if (attr.clave === "punto" && !esPlatoDeHuevo) {
                    const avisoParrilla = document.createElement("div");
                    avisoParrilla.style.fontSize = "0.8rem";
                    avisoParrilla.style.color = "var(--naranja-brillo)";
                    avisoParrilla.style.fontWeight = "bold";
                    avisoParrilla.style.marginTop = "4px";
                    avisoParrilla.innerHTML = "\u23F1\uFE0F La carne tiene una espera de 20 a 40 min seg\u00FAn cocci\u00F3n.";
                    grupo.appendChild(avisoParrilla);
                }
                wrapper.appendChild(grupo);
            }
        });
        if (tieneOpciones) {
            const btnToggle = document.createElement("button");
            btnToggle.type = "button";
            btnToggle.className = "btn-toggle-opciones";
            btnToggle.innerHTML = "Personalizar " + "<span class=\"icono-toggle\">\u25BC</span>";
            btnToggle.addEventListener("click", () => {
                if (wrapper.style.display === "none") {
                    wrapper.style.display = "flex";
                    btnToggle.innerHTML = "Ocultar " + "<span class=\"icono-toggle\">\u25B2</span>";
                    btnToggle.classList.add("abierto");
                }
                else {
                    wrapper.style.display = "none";
                    btnToggle.innerHTML = "Personalizar " + "<span class=\"icono-toggle\">\u25BC</span>";
                    btnToggle.classList.remove("abierto");
                }
            });
            contenedor.appendChild(btnToggle);
            contenedor.appendChild(wrapper);
        }
    });
});

// ==========================================================================
// AGREGAR PRODUCTO CON SUS OPCIONES
// ==========================================================================

function agregarConOpciones(productoId, boton) {
    const tarjeta = boton.closest(".tarjeta-producto");
    if (!tarjeta) {
        return;
    }
    const contenedor = tarjeta.querySelector(".opciones-contenedor[data-id=\"" + productoId + "\"]");
    if (!contenedor) {
        return;
    }
    const parametrosActuales = new URLSearchParams(window.location.search);
    const puesto = parametrosActuales.get("puesto") || "";
    let fetchParams = new URLSearchParams();
    if (puesto) {
        fetchParams.append("puesto", puesto);
    }
    let faltanOpciones = false;
    let teniaPuntoDeCoccion = false;
    const tarjetaProducto = contenedor.closest(".tarjeta-producto");
    const nombreDelPlato = tarjetaProducto ? tarjetaProducto.querySelector("h3").innerText.toLowerCase() : "";
    const esPlatoDeHuevo = nombreDelPlato.includes("omel") || nombreDelPlato.includes("tortilla");
    contenedor.querySelectorAll(".opciones-grupo").forEach(grupo => {
        const clave = grupo.dataset.clave;
        const esRequerido = grupo.dataset.requerido === "true";
        if (esRequerido) {
            const inputSeleccionado = grupo.querySelector("input[type=\"radio\"]:checked");
            if (!inputSeleccionado) {
                grupo.classList.add("error");
                faltanOpciones = true;
            }
            else {
                grupo.classList.remove("error");
                fetchParams.append(clave, inputSeleccionado.value);
                if (clave === "punto" && !esPlatoDeHuevo) {
                    teniaPuntoDeCoccion = true;
                }
            }
        }
        else if (clave === "adicional") {
            let adicionalesElegidos = [];
            grupo.querySelectorAll("input[type=\"checkbox\"]:checked").forEach(chk => {
                adicionalesElegidos.push(chk.value);
            });
            if (adicionalesElegidos.length > 0) {
                fetchParams.append("adicional", adicionalesElegidos.join(" + "));
            }
        }
    });
    if (faltanOpciones) {
        const wrapper = contenedor.querySelector(".opciones-wrapper");
        const btnToggle = contenedor.querySelector(".btn-toggle-opciones");
        if (wrapper && wrapper.style.display === "none") {
            wrapper.style.display = "flex";
            if (btnToggle) {
                btnToggle.innerHTML = "Ocultar " + "<span class=\"icono-toggle\">\u25B2</span>";
                btnToggle.classList.add("abierto");
            }
        }
        Swal.fire({
            icon: "error",
            title: "Falta seleccionar opciones",
            text: "Por favor, seleccion\u00E1 las opciones marcadas en rojo.",
            confirmButtonColor: "#ff6600"
        });
        return;
    }
    const urlFinal = "/carrito/agregar/" + productoId + "/?" + fetchParams.toString();
    const textoOriginal = boton.innerText;
    boton.innerText = "Cargando...";
    boton.disabled = true;
    fetch(urlFinal).then(response => response.json()).then(data => {
        boton.disabled = false;
        if (data.status === "ok") {
            if (teniaPuntoDeCoccion) {
                Swal.fire({
                    icon: "info",
                    title: "\u00A1Marchando a la Parrilla! \uD83E\uDD69",
                    text: "Record\u00E1 que la carne tiene un tiempo de espera de 20 a 40 minutos seg\u00FAn el punto de cocci\u00F3n elegido.",
                    confirmButtonColor: "#ff6600",
                    timer: 5000
                });
            }
            boton.innerText = "\u00A1Agregado! \u2714";
            boton.style.backgroundColor = "var(--naranja-sterak)";
            boton.style.color = "#000";
            contenedor.querySelectorAll("input").forEach(input => {
                input.checked = false;
            });
            actualizarPrecioVisual(contenedor);
            const wrapper = contenedor.querySelector(".opciones-wrapper");
            const btnToggle = contenedor.querySelector(".btn-toggle-opciones");
            if (wrapper) {
                wrapper.style.display = "none";
            }
            if (btnToggle) {
                btnToggle.innerHTML = "Personalizar " + "<span class=\"icono-toggle\">\u25BC</span>";
                btnToggle.classList.remove("abierto");
            }
            setTimeout(() => {
                boton.innerText = textoOriginal;
                boton.style.backgroundColor = "";
                boton.style.color = "";
            }, 1500);
            const badge = document.getElementById("badge-contador");
            if (badge) {
                badge.innerText = data.total_items;
            }
            const carritoSidebar = document.getElementById("carrito-sidebar");
            if (carritoSidebar && carritoSidebar.classList.contains("abierto")) {
                cargarDetalleCarrito();
            }
        }
        else {
            boton.innerText = textoOriginal;
            Swal.fire({
                icon: "error",
                title: "No se pudo agregar",
                text: data.mensaje || "Intent\u00E1 nuevamente."
            });
        }
    }).catch(error => {
        console.error("Error agregando producto:", error);
        boton.disabled = false;
        boton.innerText = textoOriginal;
        Swal.fire({
            icon: "error",
            title: "Error de conexi\u00F3n",
            text: "No se pudo agregar el producto al carrito."
        });
    });
}

// ==========================================================================
// MÓDULO 5: DASHBOARD Y ADMINISTRACIÓN AJAX
// ==========================================================================

function abrirTab(tabId, btnElement) {
    document.querySelectorAll(".tab-content").forEach(el => el.style.display = "none");
    document.querySelectorAll(".tab-btn, .panel-tab-btn").forEach(el => el.classList.remove("active"));
    const tabSeleccionada = document.getElementById("tab-" + tabId);
    if (tabSeleccionada)
        tabSeleccionada.style.display = "block";
    if (btnElement) {
        btnElement.classList.add("active");
    }
    else {
        const btnActivo = document.getElementById("btn-tab-" + tabId);
        if (btnActivo)
            btnActivo.classList.add("active");
    }
    localStorage.setItem("tabDashboardActiva", tabId);
}
document.addEventListener("DOMContentLoaded", function () {
    if (document.querySelector(".dash-tabs") || document.querySelector(".panel-tabs")) {
        let tabGuardada = "inicio";
        let botonGuardado = document.getElementById("btn-tab-" + tabGuardada);
        if (botonGuardado && botonGuardado.hidden) {
            tabGuardada = "inicio";
            botonGuardado = document.getElementById("btn-tab-inicio");
        }
        abrirTab(tabGuardada, botonGuardado);
    }
});
// =========================================================
// CONFIGURACIÓN RÁPIDA DEL SISTEMA
// Guarda switches/campos del panel desde script.js
// =========================================================
function obtenerCSRFConfiguracion() {
    const input = document.querySelector('#config-csrf-form input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;

    const nombre = 'csrftoken=';
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(nombre)) {
            return decodeURIComponent(cookie.substring(nombre.length));
        }
    }
    return '';
}

function mostrarEstadoConfiguracion(mensaje, tipo = 'ok') {
    const estado = document.getElementById('config-estado-guardado');
    if (!estado) return;

    estado.textContent = mensaje;
    estado.classList.toggle('is-error', tipo === 'error');
    estado.style.color = tipo === 'error' ? '#ff4d4d' : 'var(--verde-sanmartin)';

    clearTimeout(window.__timerConfigGuardado);
    window.__timerConfigGuardado = setTimeout(() => {
        estado.textContent = '';
        estado.classList.remove('is-error');
    }, tipo === 'error' ? 5000 : 2500);
}

async function respuestaJSONSegura(response) {
    const texto = await response.text();
    try {
        return JSON.parse(texto);
    } catch (error) {
        if (response.status === 403) {
            return {
                status: 'error',
                mensaje: 'No autorizado o CSRF vencido. Cerrá sesión del panel, volvé a entrar con el PIN y probá de nuevo.'
            };
        }
        return {
            status: 'error',
            mensaje: texto ? texto.slice(0, 180) : 'Respuesta vacía del servidor.'
        };
    }
}

window.guardarConfiguracion = async function guardarConfiguracion(elemento) {
    const panel = document.querySelector('.config-sistema');
    if (!panel || !elemento) return;

    const campo = elemento.dataset.configCampo;
    if (!campo) return;

    const url = panel.dataset.configUrl || '/dashboard/configuracion/actualizar/';
    let valor = elemento.type === 'checkbox' ? (elemento.checked ? 'true' : 'false') : elemento.value;

    if (campo === 'descuento_efectivo_porcentaje') {
        let numero = parseInt(valor || '0', 10);
        if (Number.isNaN(numero)) numero = 0;
        numero = Math.max(0, Math.min(numero, 100));
        elemento.value = numero;
        valor = String(numero);
    }

    if (campo === 'hora_cierre' && !valor) {
        mostrarEstadoConfiguracion('Ingresá una hora válida.', 'error');
        return;
    }

    const valorAnterior = elemento.type === 'checkbox' ? !elemento.checked : elemento.defaultValue;
    const datos = new FormData();
    datos.append('campo', campo);
    datos.append('valor', valor);

    elemento.disabled = true;
    mostrarEstadoConfiguracion('Guardando...');

    try {
        const response = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            body: datos,
            headers: {
                'X-CSRFToken': obtenerCSRFConfiguracion(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await respuestaJSONSegura(response);

        if (!response.ok || data.status !== 'ok') {
            throw new Error(data.mensaje || 'No se pudo guardar la configuración.');
        }

        if (elemento.type !== 'checkbox') {
            elemento.defaultValue = elemento.value;
        }

        if (campo === 'buffet_habilitado') {
            actualizarBotonPedidos(elemento.checked);
        }

        if (campo === 'salon_habilitado') {
            actualizarModuloSalon(elemento.checked);
        }

        mostrarEstadoConfiguracion('Guardado ✓');
    } catch (error) {
        console.error('Error guardando configuración:', error);
        mostrarEstadoConfiguracion(error.message, 'error');

        if (elemento.type === 'checkbox') {
            elemento.checked = valorAnterior;
        } else {
            elemento.value = valorAnterior;
        }
    } finally {
        elemento.disabled = false;
    }
};

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.config-sistema [data-config-campo]').forEach(input => {
        if (input.dataset.configListener === '1') return;
        input.dataset.configListener = '1';

        input.addEventListener('change', function () {
            window.guardarConfiguracion(this);
        });

        if (input.type === 'number' || input.type === 'time') {
            input.addEventListener('keydown', function (event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.blur();
                    window.guardarConfiguracion(this);
                }
            });
        }
    });

    /*
     * Fix importante:
     * En las filas que tienen porcentaje/hora + switch, el click sobre el switch
     * podía enfocar el input de número/hora en vez de activar el checkbox.
     * Por eso forzamos el toggle desde el switch visual.
     */
    document.querySelectorAll('.config-sistema .config-switch').forEach(switchVisual => {
        if (switchVisual.dataset.switchListener === '1') return;
        switchVisual.dataset.switchListener = '1';

        switchVisual.addEventListener('click', function (event) {
            const checkbox = this.previousElementSibling;

            if (!checkbox || checkbox.type !== 'checkbox' || checkbox.disabled) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        });
    });
});

function actualizarBotonPedidos(habilitado) {
    const boton = document.getElementById("btn-estado-global");
    if (!boton) return;
    boton.classList.toggle("btn-master-off", habilitado);
    boton.classList.toggle("btn-master-on", !habilitado);
    boton.textContent = habilitado ? "🔴 DESACTIVAR PEDIDOS" : "🟢 ACTIVAR PEDIDOS";
}

function actualizarModuloSalon(habilitado) {
    document.querySelectorAll("[data-requiere-salon]").forEach(elemento => {
        elemento.hidden = !habilitado;
    });
}

function cambiarEstadoAjax(event, elemento, nuevoEstado, requiereConfirmacion = false) {
    event.preventDefault();
    if (requiereConfirmacion) {
        Swal.fire({
            title: "\u00BFSeguro que quer\u00E9s cancelar?",
            text: "Esta acci\u00F3n no se puede deshacer.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#dc3545",
            cancelButtonColor: "#6c757d",
            confirmButtonText: "S\u00ED, cancelar pedido",
            background: "var(--card-bg)",
            color: "var(--text-color)"
        }).then(result => {
            if (result.isConfirmed) {
                procesarCambioEstado(elemento, nuevoEstado);
            }
        });
    }
    else {
        procesarCambioEstado(elemento, nuevoEstado);
    }
}
function procesarCambioEstado(elemento, nuevoEstado) {
    const url = elemento.getAttribute("href");
    const textoOriginal = elemento.innerHTML;
    elemento.innerHTML = "\u23F3...";
    elemento.style.pointerEvents = "none";
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } }).then(res => res.json()).then(data => {
        if (data.status === "ok") {
            const tr = elemento.closest("tr");
            tr.style.transition = "0.3s";
            const etiqueta = tr.querySelector(".badge-estado");
            const contenedorBotones = tr.querySelector("td:last-child div");
            if (nuevoEstado === "cancelado") {
                tr.style.opacity = "0.5";
                if (etiqueta) {
                    etiqueta.innerText = "Cancelado";
                    etiqueta.style.background = "var(--error, #dc3545)";
                    etiqueta.style.color = "white";
                    etiqueta.className = "badge-estado badge-cancelado";
                }
                if (contenedorBotones)
                    contenedorBotones.style.display = "none";
            }
            else if (nuevoEstado === "listo") {
                tr.style.borderLeft = "5px solid var(--verde-sanmartin, #28a745)";
                if (etiqueta) {
                    etiqueta.innerText = "\u00A1Listo!";
                    etiqueta.style.background = "var(--verde-sanmartin, #28a745)";
                    etiqueta.style.color = "white";
                    etiqueta.className = "badge-estado badge-listo";
                }
            }
            else if (nuevoEstado === "entregado") {
                tr.style.opacity = "0.5";
                tr.style.borderLeft = "5px solid var(--texto-mutado, #6c757d)";
                if (etiqueta) {
                    etiqueta.innerText = "Entregado";
                    etiqueta.style.background = "var(--texto-mutado, #6c757d)";
                    etiqueta.style.color = "white";
                    etiqueta.className = "badge-estado badge-entregado";
                }
                if (contenedorBotones)
                    contenedorBotones.style.display = "none";
            }
            else if (nuevoEstado === "demorado") {
                if (etiqueta) {
                    etiqueta.innerText = "Demorado";
                    etiqueta.style.background = "#fd7e14";
                    etiqueta.style.color = "white";
                }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = "auto";
            }
            else {
                if (etiqueta) {
                    etiqueta.innerText = "En Preparaci\u00F3n";
                    etiqueta.style.background = "var(--azul-sanmartin, #007bff)";
                    etiqueta.style.color = "white";
                    etiqueta.className = "badge-estado badge-preparacion";
                }
                elemento.innerHTML = textoOriginal;
                elemento.style.pointerEvents = "auto";
            }
        }
    }).catch(error => {
        elemento.innerHTML = textoOriginal;
        elemento.style.pointerEvents = "auto";
        Swal.fire({ icon: "error", title: "Oops...", text: "Hubo un error de conexi\u00F3n.", background: "var(--card-bg)", color: "var(--text-color)" });
    });
}
function editarPrecioAjax(event, form) {
    event.preventDefault();
    const boton = form.querySelector("button");
    const input = form.querySelector("input[name=\"precio\"]");
    const textoOriginal = boton ? boton.innerText : "OK";
    if (boton) {
        boton.disabled = true;
        boton.innerText = "...";
    }
    fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    }).then(response => {
        if (!response.ok) {
            throw new Error("No se pudo actualizar el precio.");
        }
        return response.json().catch(() => ({ status: "ok" }));
    }).then(data => {
        if (data.status && data.status !== "ok") {
            throw new Error(data.mensaje || "No se pudo actualizar el precio.");
        }
        if (boton) {
            boton.innerText = "\u2713";
            boton.style.background = "var(--verde-sanmartin)";
            boton.style.color = "#fff";
        }
        if (input) {
            input.blur();
        }
        setTimeout(() => {
            if (boton) {
                boton.innerText = textoOriginal;
                boton.style.background = "";
                boton.style.color = "";
                boton.disabled = false;
            }
        }, 900);
    }).catch(error => {
        if (boton) {
            boton.innerText = textoOriginal;
            boton.disabled = false;
        }
        Swal.fire({
            icon: "error",
            title: "No se pudo cambiar el precio",
            text: error.message,
            background: "var(--card-bg)",
            color: "var(--text-color)"
        });
    });
}
function cambiarDisponibilidadAjax(event, el) {
    event.preventDefault();
    fetch(el.href, { headers: { "X-Requested-With": "XMLHttpRequest" } }).then(res => res.json()).then(data => {
        const fila = el.closest(".fila-producto-menu") || el.closest("tr");
        if (fila) {
            fila.classList.toggle("is-pausado", !data.disponible);
            fila.style.opacity = "";
            const estado = fila.querySelector(".menu-admin-estado");
            if (estado) {
                estado.classList.toggle("is-activo", data.disponible);
                estado.classList.toggle("is-pausado", !data.disponible);
                estado.textContent = data.disponible ? "\u25CF ACTIVO" : "\u25CF PAUSADO";
            }
        }
        el.innerText = data.disponible ? "\u23F8 Pausar" : "\u25B6 Activar";
        if (el.classList.contains("menu-admin-btn")) {
            el.classList.toggle("is-pausar", data.disponible);
            el.classList.toggle("is-activar", !data.disponible);
        }
        else {
            el.className = data.disponible ? "btn-panel btn-gris" : "btn-panel btn-verde";
        }
    });
}
function eliminarProductoAjax(event, el) {
    event.preventDefault();
    Swal.fire({
        title: "\u00BFBorrar producto?",
        text: "Desaparecer\u00E1 del men\u00FA permanentemente.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#dc3545",
        cancelButtonColor: "#6c757d",
        confirmButtonText: "Borrar",
        cancelButtonText: "Cancelar",
        background: "var(--card-bg)",
        color: "var(--text-color)"
    }).then(result => {
        if (!result.isConfirmed)
            return;
        fetch(el.href, { headers: { "X-Requested-With": "XMLHttpRequest" } }).then(() => {
            const fila = el.closest(".fila-producto-menu") || el.closest("tr");
            if (!fila)
                return;
            fila.style.transition = "0.3s";
            fila.style.opacity = "0";
            setTimeout(() => {
                const categoria = fila.closest(".categoria-menu");
                fila.remove();
                if (categoria && !categoria.querySelector(".fila-producto-menu")) {
                    categoria.remove();
                }
                if (typeof aplicarFiltrosMenuAdmin === "function") {
                    aplicarFiltrosMenuAdmin();
                }
            }, 300);
        });
    });
}
function ejecutarAjax(event, el) {
    event.preventDefault();
    fetch(el.href, { headers: { "X-Requested-With": "XMLHttpRequest" } }).then(response => response.json()).then(data => {
        const estaAbierto = data.esta_abierto;
        el.innerText = estaAbierto ? "Cerrar" : "Abrir";
        el.classList.remove("btn-verde", "btn-rojo");
        el.classList.add(estaAbierto ? "btn-rojo" : "btn-verde");
        const p = el.previousElementSibling;
        p.innerText = estaAbierto ? "\uD83D\uDFE2 ABIERTO" : "\uD83D\uDD34 CERRADO";
        p.style.color = estaAbierto ? "var(--verde-sanmartin)" : "var(--error)";
    });
}
function actualizarPuestosAjax(event, form) {
    event.preventDefault();
    fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "XMLHttpRequest" } }).then(() => {
        form.style.backgroundColor = "rgba(40, 167, 69, 0.1)";
        setTimeout(() => form.style.backgroundColor = "transparent", 800);
    }).catch(error => Swal.fire({ icon: "error", title: "Oops...", text: "Hubo un error al guardar.", background: "var(--card-bg)", color: "var(--text-color)" }));
}
let deferredPrompt;
let clicsIOS = parseInt(localStorage.getItem("clicsIOS")) || 0;
window.addEventListener("beforeinstallprompt", e => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById("btn-instalar-nav").style.display = "block";
});
document.getElementById("btn-instalar-nav").addEventListener("click", async () => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt = null;
        document.getElementById("btn-instalar-nav").style.display = "none";
    }
    else if (isIOS) {
        clicsIOS++;
        localStorage.setItem("clicsIOS", clicsIOS);
        if (clicsIOS >= 1) {
            alert("Para tener el Buffet en tu inicio: Toc\u00E1 el bot\u00F3n 'Compartir' (el cuadrado con la flecha) y eleg\u00ED 'Agregar al inicio'.");
        }
    }
});
window.addEventListener("appinstalled", () => { document.getElementById("btn-instalar-nav").style.display = "none"; });

// ==========================================================================
// SELECTOR DE CATEGORÍAS BUSCABLE
// ==========================================================================

function sincronizarSelectorCategoria(select) {
    if (!select || !select._categoriaPicker)
        return;
    const opcion = select.options[select.selectedIndex];
    const texto = opcion && opcion.value ? opcion.textContent.trim() : "Eleg\u00ED una categor\u00EDa";
    select._categoriaPicker.label.textContent = texto;
    select._categoriaPicker.items.forEach(item => {
        item.classList.toggle("is-selected", String(item.dataset.value) === String(select.value));
    });
}
function inicializarSelectorCategoria(select) {
    if (!select || select.dataset.categoriaPickerInicializado === "1")
        return;
    select.dataset.categoriaPickerInicializado = "1";
    select.classList.add("categoria-select-native");
    const picker = document.createElement("div");
    picker.className = "categoria-picker";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "categoria-picker__trigger";
    trigger.innerHTML = "<span>Eleg\u00ED una categor\u00EDa</span><b>\u2304</b>";
    const panel = document.createElement("div");
    panel.className = "categoria-picker__panel";
    panel.hidden = true;
    const search = document.createElement("input");
    search.type = "search";
    search.className = "categoria-picker__search";
    search.placeholder = "Buscar categor\u00EDa...";
    search.autocomplete = "off";
    const list = document.createElement("div");
    list.className = "categoria-picker__list";
    const items = [];
    Array.from(select.options).forEach(opcion => {
        if (!opcion.value)
            return;
        const item = document.createElement("button");
        item.type = "button";
        item.className = "categoria-picker__item";
        item.dataset.value = opcion.value;
        item.dataset.busqueda = normalizarTextoMenuAdmin(opcion.textContent);
        item.textContent = opcion.textContent.trim();
        item.addEventListener("click", function () {
            select.value = item.dataset.value;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            panel.hidden = true;
            picker.classList.remove("is-open");
        });
        items.push(item);
        list.appendChild(item);
    });
    search.addEventListener("input", function () {
        const texto = normalizarTextoMenuAdmin(search.value);
        items.forEach(item => {
            item.hidden = Boolean(texto) && !item.dataset.busqueda.includes(texto);
        });
    });
    trigger.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        const abrir = panel.hidden;
        document.querySelectorAll(".categoria-picker.is-open").forEach(otro => {
            if (otro !== picker) {
                otro.classList.remove("is-open");
                const otroPanel = otro.querySelector(".categoria-picker__panel");
                if (otroPanel)
                    otroPanel.hidden = true;
            }
        });
        panel.hidden = !abrir;
        picker.classList.toggle("is-open", abrir);
        if (abrir) {
            search.value = "";
            items.forEach(item => item.hidden = false);
            window.setTimeout(() => search.focus(), 30);
        }
    });
    picker.addEventListener("click", event => event.stopPropagation());
    panel.appendChild(search);
    panel.appendChild(list);
    picker.appendChild(trigger);
    picker.appendChild(panel);
    select.insertAdjacentElement("afterend", picker);
    select._categoriaPicker = {
        picker: picker,
        panel: panel,
        label: trigger.querySelector("span"),
        search: search,
        items: items
    };
    select.addEventListener("change", function () {
        sincronizarSelectorCategoria(select);
    });
    sincronizarSelectorCategoria(select);
}
function cerrarSelectoresCategoria() {
    document.querySelectorAll(".categoria-picker.is-open").forEach(picker => {
        picker.classList.remove("is-open");
        const panel = picker.querySelector(".categoria-picker__panel");
        if (panel)
            panel.hidden = true;
    });
}
document.addEventListener("click", cerrarSelectoresCategoria);

// ==========================================================================
// MÓDULO 5B: GESTOR VISUAL DEL MENÚ
// ==========================================================================

let filtroPuestoMenuAdmin = "todos";
function normalizarTextoMenuAdmin(valor) {
    return String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
function filtrarMenu(puestoId, btnActivo) {
    filtroPuestoMenuAdmin = String(puestoId || "todos");
    document.querySelectorAll(".menu-admin-filtro").forEach(btn => {
        btn.classList.remove("is-active");
    });
    if (btnActivo) {
        btnActivo.classList.add("is-active");
    }
    aplicarFiltrosMenuAdmin();
}
function aplicarFiltrosMenuAdmin() {
    const buscador = document.getElementById("buscador-menu-admin");
    const texto = normalizarTextoMenuAdmin(buscador ? buscador.value : "");
    let totalVisibles = 0;
    document.querySelectorAll(".categoria-menu").forEach(categoria => {
        let visiblesCategoria = 0;
        categoria.querySelectorAll(".fila-producto-menu").forEach(fila => {
            const puestos = String(fila.dataset.puestos || "").split(",").map(valor => valor.trim()).filter(Boolean);
            const busqueda = normalizarTextoMenuAdmin(fila.dataset.busqueda || fila.innerText);
            const coincidePuesto = filtroPuestoMenuAdmin === "todos" || puestos.includes(filtroPuestoMenuAdmin);
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
    const sinResultados = document.getElementById("menu-admin-sin-resultados");
    if (sinResultados) {
        sinResultados.hidden = totalVisibles !== 0;
    }
}
function actualizarAvisoCategoriaSalon() {
    const select = document.getElementById("editor-categoria");
    const aviso = document.getElementById("editor-aviso-salon");
    if (!select || !aviso)
        return;
    const opcion = select.options[select.selectedIndex];
    const esSalon = opcion && normalizarTextoMenuAdmin(opcion.textContent) === "salon";
    aviso.hidden = !esSalon;
}
function actualizarPreviewEditorProducto(url) {
    const preview = document.getElementById("editor-imagen-preview");
    if (!preview)
        return;
    preview.innerHTML = "";
    if (!url) {
        const texto = document.createElement("span");
        texto.textContent = "Sin imagen";
        preview.appendChild(texto);
        return;
    }
    const imagen = document.createElement("img");
    imagen.src = url;
    imagen.alt = "Imagen actual del producto";
    preview.appendChild(imagen);
}
function abrirEditorProducto(boton) {
    const modal = document.getElementById("modal-editor-producto");
    const form = document.getElementById("form-editor-producto");
    if (!modal || !form || !boton)
        return;
    form.action = boton.dataset.url || "";
    document.getElementById("editor-nombre").value = boton.dataset.nombre || "";
    document.getElementById("editor-codigo").value = boton.dataset.codigo || "";
    const editorCategoria = document.getElementById("editor-categoria");
    editorCategoria.value = boton.dataset.categoria || "";
    editorCategoria.dispatchEvent(new Event("change", { bubbles: true }));
    document.getElementById("editor-precio").value = boton.dataset.precio || "";
    document.getElementById("editor-orden").value = boton.dataset.orden || "0";
    document.getElementById("editor-descripcion").value = boton.dataset.descripcion || "";
    document.getElementById("editor-disponible").checked = boton.dataset.disponible === "1";
    document.getElementById("editor-promo").checked = boton.dataset.promo === "1";
    document.getElementById("editor-variantes").value = boton.dataset.variantes || "";
    document.getElementById("editor-guarniciones").value = boton.dataset.guarniciones || "";
    document.getElementById("editor-coccion").value = boton.dataset.coccion || "";
    document.getElementById("editor-rellenos").value = boton.dataset.rellenos || "";
    document.getElementById("editor-salsas").value = boton.dataset.salsas || "";
    document.getElementById("editor-adicionales").value = boton.dataset.adicionales || "";
    document.getElementById("editor-hielo").value = boton.dataset.hielo || "";
    const puntosSeleccionados = String(boton.dataset.puestos || "").split(",").map(valor => valor.trim()).filter(Boolean);
    document.querySelectorAll("#editor-puntos-venta input[name=\"puntos_venta\"]").forEach(input => {
        input.checked = puntosSeleccionados.includes(String(input.value));
    });
    const inputImagen = document.getElementById("editor-imagen");
    if (inputImagen)
        inputImagen.value = "";
    actualizarPreviewEditorProducto(boton.dataset.imagen || "");
    actualizarAvisoCategoriaSalon();
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("menu-editor-abierto");
    window.setTimeout(() => {
        const nombre = document.getElementById("editor-nombre");
        if (nombre) {
            nombre.focus();
            nombre.select();
        }
    }, 60);
}
function cerrarEditorProducto() {
    const modal = document.getElementById("modal-editor-producto");
    if (!modal)
        return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("menu-editor-abierto");
}
function guardarEditorProducto(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const boton = document.getElementById("btn-guardar-editor-producto");
    const puntosMarcados = form.querySelectorAll("input[name=\"puntos_venta\"]:checked");
    if (!puntosMarcados.length) {
        Swal.fire({
            icon: "warning",
            title: "Eleg\u00ED un mostrador",
            text: "El producto tiene que estar asignado al menos a un punto de venta.",
            background: "var(--card-bg)",
            color: "var(--text-color)",
            confirmButtonColor: "var(--dorado-sanmartin)"
        });
        return;
    }
    const textoOriginal = boton ? boton.innerHTML : "";
    if (boton) {
        boton.disabled = true;
        boton.innerHTML = "\u23F3 Guardando...";
    }
    fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" }
    }).then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.mensaje || "No se pudo guardar el producto.");
        }
        return data;
    }).then(() => {
        localStorage.setItem("tabDashboardActiva", "menu");
        cerrarEditorProducto();
        return Swal.fire({
            icon: "success",
            title: "Producto actualizado",
            text: "Los cambios quedaron guardados.",
            timer: 900,
            showConfirmButton: false,
            background: "var(--card-bg)",
            color: "var(--text-color)"
        });
    }).then(() => {
        window.location.reload();
    }).catch(error => {
        Swal.fire({
            icon: "error",
            title: "No se pudo guardar",
            text: error.message || "Revis\u00E1 los datos e intent\u00E1 nuevamente.",
            background: "var(--card-bg)",
            color: "var(--text-color)",
            confirmButtonColor: "var(--dorado-sanmartin)"
        });
    }).finally(() => {
        if (boton) {
            boton.disabled = false;
            boton.innerHTML = textoOriginal;
        }
    });
}
document.addEventListener("DOMContentLoaded", function () {
    const buscador = document.getElementById("buscador-menu-admin");
    if (buscador) {
        buscador.addEventListener("input", aplicarFiltrosMenuAdmin);
    }
    const categoria = document.getElementById("editor-categoria");
    if (categoria) {
        categoria.addEventListener("change", actualizarAvisoCategoriaSalon);
    }
    const imagen = document.getElementById("editor-imagen");
    if (imagen) {
        imagen.addEventListener("change", function () {
            const archivo = imagen.files && imagen.files[0];
            if (!archivo)
                return;
            const lector = new FileReader();
            lector.onload = function () {
                actualizarPreviewEditorProducto(lector.result);
            };
            lector.readAsDataURL(archivo);
        });
    }
    const formEditor = document.getElementById("form-editor-producto");
    if (formEditor) {
        formEditor.addEventListener("submit", guardarEditorProducto);
    }
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            const modal = document.getElementById("modal-editor-producto");
            if (modal && modal.classList.contains("is-open")) {
                cerrarEditorProducto();
            }
        }
    });
    document.querySelectorAll("#id_categoria, #editor-categoria, select[data-categoria-select]").forEach(inicializarSelectorCategoria);
    aplicarFiltrosMenuAdmin();
});

// ==========================================================================
// MÓDULO 6: MODO OSCURO / CLARO
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById("theme-toggle");
    const currentTheme = localStorage.getItem("theme") || "dark";
    document.body.setAttribute("data-theme", currentTheme);
    if (themeToggle) {
        themeToggle.checked = (currentTheme === "dark");
        themeToggle.addEventListener("change", () => {
            const newTheme = themeToggle.checked ? "dark" : "light";
            document.body.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
        });
    }
});

// ==========================================================================
// MÓDULO 7: CIERRE DE CAJA Y ESTADÍSTICAS
// ==========================================================================

function abrirCierreCaja() {
    fetch("/api/resumen-ventas/").then(res => res.json()).then(data => {
        if (data.status === "ok") {
            document.getElementById("gran-total-cierre").innerText = "$" + data.gran_total.toLocaleString("es-AR", { minimumFractionDigits: 2 });
            let htmlMostradores = "";
            if (data.mostradores.length === 0) {
                htmlMostradores = "<p style=\"text-align:center; color: var(--texto-mutado);\">No hay ventas registradas en este turno.</p>";
            }
            else {
                data.mostradores.forEach(m => {
                    let htmlProductos = "";
                    if (m.productos.length > 0) {
                        m.productos.forEach(p => {
                            htmlProductos += `
                                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px; border-bottom: 1px dashed var(--borde); padding-bottom: 4px; color: var(--text-color);">
                                    <span>${p.nombre}</span> <strong>x${p.cantidad}</strong>
                                </div>`;
                        });
                    }
                    else {
                        htmlProductos = "<span style=\"color: var(--texto-mutado); font-size: 0.85rem;\">Sin productos vendidos.</span>";
                    }
                    htmlMostradores += `
                        <details class="panel-accordion" style="margin-bottom: 12px; border: 1px solid var(--borde); background: var(--bg-color); border-radius: 8px;">
                            <summary style="padding: 12px 15px; font-size: 1.05rem; border-left: 4px solid var(--dorado-sanmartin); background: transparent; cursor: pointer;">
                                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center; padding-right: 10px;">
                                    <span style="font-weight: 800;">🏪 ${m.nombre}</span>
                                    <strong style="color: var(--verde-sanmartin);">$${m.total_ventas.toLocaleString("es-AR")}</strong>
                                </div>
                            </summary>
                            <div style="padding: 15px; border-top: 1px solid var(--borde);">
                                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                                    <div style="flex: 1; text-align: center; background: var(--card-bg); padding: 10px; border-radius: 8px; border: 1px solid var(--borde);">
                                        <small style="color: var(--texto-mutado); display: block; font-size: 0.75rem; text-transform: uppercase;">Pedidos</small>
                                        <strong style="color: var(--text-color); font-size: 1.3rem;">${m.cantidad_pedidos}</strong>
                                    </div>
                                    <div style="flex: 1.5; background: var(--card-bg); padding: 10px; border-radius: 8px; border: 1px solid var(--borde); font-size: 0.85rem;">
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>💵 Efectivo:</span> <strong>$${m.efectivo.toLocaleString("es-AR")}</strong></div>
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>📱 MP:</span> <strong>$${m.mercadopago.toLocaleString("es-AR")}</strong></div>
                                        <div style="display: flex; justify-content: space-between; color: var(--text-color);"><span>💳 Débito:</span> <strong>$${m.debito.toLocaleString("es-AR")}</strong></div>
                                    </div>
                                </div>
                                <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 0.95rem; color: var(--text-color); border-bottom: 1px solid var(--borde); padding-bottom: 5px;">🍔 Desglose de Productos</h4>
                                ${htmlProductos}
                            </div>
                        </details>
                        `;
                });
            }
            document.getElementById("contenedor-mostradores").innerHTML = htmlMostradores;
            document.getElementById("modalCierre").classList.add("activo");
        }
    }).catch(error => console.error("Error al obtener cierre:", error));
}
function cerrarCierreCaja() { document.getElementById("modalCierre").classList.remove("activo"); }
function confirmarCierreYLimpiar() {
    Swal.fire({
        title: "\u00BFSeguro que quer\u00E9s cerrar el turno?",
        text: "Esto va a borrar todos los pedidos del panel para arrancar de cero ma\u00F1ana.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "var(--error)",
        cancelButtonColor: "var(--texto-mutado)",
        confirmButtonText: "S\u00ED, Cerrar Turno",
        cancelButtonText: "Cancelar",
        background: "var(--card-bg)",
        color: "var(--text-color)"
    }).then(result => { if (result.isConfirmed) {
        window.location.href = "/dashboard/eliminar-todo/";
    } });
}

// ==========================================================================
// MÓDULO 8: LÓGICA DE MESAS
// ==========================================================================

function renderizarMesas() {
    const grid = document.getElementById("grid-mesas");
    if (!grid)
        return;
    let mesas = {};
    document.querySelectorAll(".fila-pedido").forEach(fila => {
        const badge = fila.querySelector(".badge-estado");
        if (badge) {
            const estadoTexto = badge.innerText.toLowerCase();
            if (estadoTexto.includes("cancelado") || estadoTexto.includes("entregado")) {
                return;
            }
        }
        if (fila.style.display === "none" || fila.style.opacity === "0.5") {
            return;
        }
        const esEfectivo = fila.querySelector("td:first-child").innerText.toUpperCase().includes("EFECTIVO");
        if (!esEfectivo)
            return;
        const htmlDetalle = fila.querySelector(".order-details-box").innerHTML;
        const matchMesa = htmlDetalle.match(/\(Mesa\s+([^)]+)\)/i);
        if (matchMesa) {
            const numMesa = matchMesa[1].trim();
            const totalTexto = fila.querySelector("td:nth-child(3)").innerText;
            const total = parseFloat(totalTexto.replace("$", "").trim()) || 0;
            const idPedido = fila.id.replace("pedido-", "");
            if (!mesas[numMesa])
                mesas[numMesa] = { total: 0, pedidos: [] };
            mesas[numMesa].total += total;
            mesas[numMesa].pedidos.push(idPedido);
        }
    });
    grid.innerHTML = "";
    if (Object.keys(mesas).length === 0) {
        grid.innerHTML = "<div class=\"mesa-empty\">No hay mesas activas con pagos en efectivo por el momento.</div>";
        return;
    }
    for (let mesa in mesas) {
        const data = mesas[mesa];
        const cuentaSalon = obtenerCuentaSalonGuardada(mesa);
        const mozoMesa = cuentaSalon && cuentaSalon.mozo_nombre ? cuentaSalon.mozo_nombre : "Sin asignar";
        grid.innerHTML += `
            <div class="mesa-card">
                <div class="mesa-header">
                    <h3 class="mesa-titulo">🍽️ Mesa ${mesa}</h3>
                    <span class="mesa-badge">${data.pedidos.length} Pedido/s</span>
                </div>
                <div class="mesa-mozo">🧑‍🍳 ${mozoMesa}</div>
                <div class="mesa-total">$${data.total.toLocaleString("es-AR", { minimumFractionDigits: 2 })}</div>
                <div class="mesa-acciones">
                    <button onclick="dividirCuenta('${mesa}', ${data.total})" class="btn-panel btn-amarillo" style="flex: 1; padding: 12px; font-size: 1rem; border-radius: 8px;">➗ Dividir</button>
                    <button onclick="cobrarMesa('${mesa}', '${data.pedidos.join(",")}')" class="btn-panel btn-verde" style="flex: 1; padding: 12px; font-size: 1rem; border-radius: 8px;">💵 Cobrar</button>
                </div>
            </div>
        `;
    }
}
function dividirCuenta(mesa, total) {
    Swal.fire({
        title: `Mesa ${mesa} - Dividir Cuenta`,
        text: `El total de la mesa es $${total.toLocaleString("es-AR")}`,
        input: "number",
        inputAttributes: { min: 2, max: 20, step: 1 },
        inputLabel: "\u00BFEntre cu\u00E1ntas personas dividimos?",
        inputValue: 2,
        showCancelButton: true,
        confirmButtonColor: "var(--azul-sanmartin)",
        confirmButtonText: "Calcular",
        cancelButtonText: "Cancelar",
        background: "var(--card-bg)",
        color: "var(--text-color)"
    }).then(result => {
        if (result.isConfirmed && result.value) {
            const personas = parseInt(result.value);
            const porCabeza = (total / personas).toFixed(2);
            Swal.fire({ icon: "info", title: `Tienen que poner $${parseFloat(porCabeza).toLocaleString("es-AR")} c/u`, text: `(Dividido en ${personas} personas)`, confirmButtonColor: "var(--verde-sanmartin)", background: "var(--card-bg)", color: "var(--text-color)" });
        }
    });
}
function cobrarMesa(mesa, pedidosStr) {
    Swal.fire({
        title: `¿Cobrar Mesa ${mesa}?`,
        text: "Se marcar\u00E1n como Entregados y Cobrados todos los pedidos acumulados de esta mesa.",
        icon: "question",
        showCancelButton: true,
        confirmButtonColor: "var(--verde-sanmartin)",
        cancelButtonColor: "var(--texto-mutado)",
        confirmButtonText: "S\u00ED, cobrar la mesa",
        cancelButtonText: "Cancelar",
        background: "var(--card-bg)",
        color: "var(--text-color)"
    }).then(result => {
        if (result.isConfirmed) {
            Swal.fire({ title: "Cobrando mesa...", showConfirmButton: false, background: "var(--card-bg)", color: "var(--text-color)" });
            const pedidos = pedidosStr.split(",");
            let fetchPromises = pedidos.map(id => {
                const fila = document.getElementById(`pedido-${id}`);
                if (!fila)
                    return Promise.resolve();
                const aTag = fila.querySelector("td:last-child a");
                if (!aTag) {
                    fila.style.opacity = "0.5";
                    fila.style.display = "none";
                    return Promise.resolve();
                }
                let baseHref = aTag.getAttribute("href");
                let parts = baseHref.split("/");
                parts[parts.length - 2] = "entregado";
                const finalUrl = parts.join("/");
                return fetch(finalUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } }).then(res => res.json()).then(data => {
                    if (data.status === "ok") {
                        fila.style.opacity = "0.5";
                        fila.style.display = "none";
                        const badge = fila.querySelector(".badge-estado");
                        if (badge) {
                            badge.innerText = "Entregado";
                        }
                    }
                });
            });
            Promise.all(fetchPromises).then(() => {
                Swal.fire({ icon: "success", title: "\u00A1Mesa Cobrada!", text: `La mesa ${mesa} ya fue liquidada.`, confirmButtonColor: "var(--verde-sanmartin)", background: "var(--card-bg)", color: "var(--text-color)" });
                renderizarMesas();
            });
        }
    });
}

// ==========================================================================
// MÓDULO 8B: OPINIONES Y SUGERENCIAS
// ==========================================================================

function abrirModalOpinion() {
    const modal = document.getElementById("modal-opinion");
    if (!modal)
        return;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
}
function cerrarModalOpinion() {
    const modal = document.getElementById("modal-opinion");
    if (!modal)
        return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
}
function obtenerCsrfDashboard() {
    const input = document.querySelector("input[name=\"csrfmiddlewaretoken\"]");
    return input ? input.value : "";
}
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("form-opinion");
    if (!form)
        return;
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const boton = document.getElementById("btn-enviar-opinion");
        const textoOriginal = boton ? boton.innerHTML : "";
        if (boton) {
            boton.disabled = true;
            boton.innerHTML = "Enviando...";
        }
        fetch(form.action || "/opinion/enviar/", {
            method: "POST",
            body: new FormData(form),
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        }).then(async function (response) {
            const data = await response.json().catch(function () { return {}; });
            if (!response.ok || data.status !== "ok") {
                throw new Error(data.mensaje || "No se pudo enviar el comentario.");
            }
            return data;
        }).then(function () {
            form.reset();
            cerrarModalOpinion();
            Swal.fire({
                icon: "success",
                title: "\u00A1Gracias por contarnos!",
                text: "Tu comentario fue enviado de forma privada.",
                confirmButtonColor: "var(--verde-sanmartin)",
                background: "var(--card-bg)",
                color: "var(--text-color)"
            });
        }).catch(function (error) {
            Swal.fire({
                icon: "error",
                title: "No se pudo enviar",
                text: error.message,
                background: "var(--card-bg)",
                color: "var(--text-color)"
            });
        }).finally(function () {
            if (boton) {
                boton.disabled = false;
                boton.innerHTML = textoOriginal;
            }
        });
    });
});
function marcarOpinionLeida(opinionId, url) {
    fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": obtenerCsrfDashboard(),
            "X-Requested-With": "XMLHttpRequest"
        }
    }).then(function (response) { return response.json(); }).then(function (data) {
        if (data.status !== "ok")
            return;
        const tarjeta = document.getElementById("opinion-" + opinionId);
        if (!tarjeta)
            return;
        tarjeta.classList.remove("is-nueva");
        const badge = tarjeta.querySelector(".opinion-nueva-badge");
        if (badge)
            badge.remove();
        const boton = tarjeta.querySelector(".opinion-btn--leida");
        if (boton)
            boton.remove();
    });
}
function eliminarOpinion(opinionId, url) {
    Swal.fire({
        title: "\u00BFEliminar comentario?",
        text: "No se puede recuperar despu\u00E9s.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Eliminar",
        cancelButtonText: "Cancelar",
        confirmButtonColor: "var(--error)",
        background: "var(--card-bg)",
        color: "var(--text-color)"
    }).then(function (resultado) {
        if (!resultado.isConfirmed)
            return;
        fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": obtenerCsrfDashboard(),
                "X-Requested-With": "XMLHttpRequest"
            }
        }).then(function (response) { return response.json(); }).then(function (data) {
            if (data.status !== "ok")
                return;
            const tarjeta = document.getElementById("opinion-" + opinionId);
            if (tarjeta) {
                tarjeta.style.opacity = "0";
                window.setTimeout(function () { tarjeta.remove(); }, 250);
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
            precio: Number(producto.precio || 0)
        };
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
            var cantPagar = Number(item.cant_pagar || cantidad);
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
                cant_pagar: cantPagar
            };
        });
        recalcular(cuentas[clave]);
        return cuentas[clave];
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
            item.cant_pagar = Number(item.cantidad || 1);
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
    function enfocarMesaRapida() {
        window.setTimeout(function () {
            if (inputMesaRapida) {
                inputMesaRapida.value = "";
                inputMesaRapida.focus();
                inputMesaRapida.select();
            }
        }, 70);
    }
    function enfocarCantidad() {
        window.setTimeout(function () {
            if (inputCant) {
                inputCant.focus();
                inputCant.select();
            }
        }, 60);
    }
    function abrirComanda() {
        if (modalComanda) {
            modalComanda.classList.add("is-open");
        }
        if (modalOverlay) {
            modalOverlay.classList.add("is-open");
            modalOverlay.setAttribute("aria-hidden", "false");
        }
        document.body.style.overflow = "hidden";
        enfocarCantidad();
    }
    function cerrarComanda() {
        cerrarSugerencias();
        modoParcial = false;
        filaTeclado = 0;
        var cuenta = cuentaActual();
        limpiarSeleccion(cuenta);
        guardar();
        if (modalComanda) {
            modalComanda.classList.remove("is-open");
        }
        if (modalOverlay) {
            modalOverlay.classList.remove("is-open");
            modalOverlay.setAttribute("aria-hidden", "true");
        }
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
        var id = Number(mozoId || 0);
        var mozo = mozos.find(function (item) {
            return Number(item.id) === id;
        });
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
        if (cuenta.mozo_nombre || !mozos.length) {
            finalizarAperturaMesa(cuenta);
            return;
        }
        var opciones = {};
        mozos.forEach(function (mozo) {
            opciones[String(mozo.id)] = mozo.nombre;
        });
        Swal.fire({
            title: "Mesa " + mesaActual,
            text: "\u00BFQu\u00E9 mozo atiende esta mesa?",
            input: "select",
            inputOptions: opciones,
            inputPlaceholder: "Seleccion\u00E1 un mozo",
            showCancelButton: true,
            confirmButtonText: "Abrir mesa",
            cancelButtonText: "Cancelar",
            confirmButtonColor: "var(--verde-sanmartin)",
            background: "var(--card-bg)",
            color: "var(--text-color)",
            inputValidator: function (valor) {
                if (!valor)
                    return "Seleccion\u00E1 el mozo de la mesa.";
                return null;
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
    function liberarMesaActual() {
        var numeroMesa = mesaActual;
        if (numeroMesa) {
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
        }
        if (modalOverlay) {
            modalOverlay.classList.remove("is-open");
            modalOverlay.setAttribute("aria-hidden", "true");
        }
        document.body.style.overflow = "";
        enfocarMesaRapida();
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
            if (ocupada) {
                boton.innerHTML = "<span class=\"salon-pos__mesa-numero\">" + escapar(numero) + "</span>" + "<span class=\"salon-pos__mesa-total\">" + dinero(total) + "</span>" + (cuenta && cuenta.mozo_nombre ? "<span class=\"salon-pos__mesa-mozo\">\uD83E\uDDD1\u200D\uD83C\uDF73 " + escapar(cuenta.mozo_nombre) + "</span>" : "") + "<span class=\"salon-pos__mesa-items\">" + items.length + (items.length === 1 ? " producto" : " productos") + "</span>";
            }
            else {
                boton.innerHTML = "<span class=\"salon-pos__mesa-numero\">" + escapar(numero) + "</span>" + "<span class=\"salon-pos__mesa-libre\">Libre</span>";
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
                existente.cant_pagar = existente.cantidad;
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
                cant_pagar: cantidad
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
        if (!texto || texto === ".." || texto === "//" || texto === "*") {
            return [];
        }
        var exactos = [];
        var otros = [];
        productos.forEach(function (producto) {
            var codigo = String(producto.codigo).toLowerCase();
            var nombre = String(producto.nombre).toLowerCase();
            if (codigo === texto) {
                exactos.unshift(producto);
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
            var cant = Number(item.cant_pagar || item.cantidad);
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
        item.cant_pagar = item.cantidad;
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
        var cantidad = Number(item.cant_pagar || item.cantidad) + diferencia;
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
                html += "<div class=\"salon-pos__fila-cant\" data-no-toggle=\"1\">" + "<button type=\"button\" data-action=\"restar\" data-index=\"" + index + "\">\u2212</button>" + "<strong>" + item.cantidad + "</strong>" + "<button type=\"button\" data-action=\"sumar\" data-index=\"" + index + "\">+</button>" + "</div>";
                html += "<div class=\"salon-pos__fila-codigo\">" + escapar(item.codigo) + "</div>";
                html += "<div class=\"salon-pos__fila-descripcion\">" + "<strong>" + escapar(item.nombre) + "</strong>";
                if (modoParcial && item.seleccionado) {
                    html += "<div class=\"salon-pos__pago-inline\" data-no-toggle=\"1\">" + "<span>Cobrar</span>" + "<button type=\"button\" data-action=\"pagar-menos\" data-index=\"" + index + "\">\u2212</button>" + "<strong>" + item.cant_pagar + "</strong>" + "<button type=\"button\" data-action=\"pagar-mas\" data-index=\"" + index + "\">+</button>" + "<small>de " + item.cantidad + "</small>" + "</div>";
                }
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
        btnTicket.disabled = !cuenta.items.length || enviando;
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
            var cantidad = soloSeleccionados ? Number(item.cant_pagar || item.cantidad) : Number(item.cantidad);
            items.push({
                producto_id: item.producto_id,
                codigo: item.codigo,
                nombre: item.nombre,
                precio: item.precio,
                cantidad: cantidad
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
        return fetch(url, {
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
        }).finally(function () {
            enviando = false;
            if (mesaActual) {
                render();
            }
        });
    }
    function elegirMedioPago(total, titulo) {
        return Swal.fire({
            title: titulo || "Registrar cobro",
            html: "<div style=\"margin-bottom:10px;color:var(--texto-mutado);\">Total a cobrar</div>" + "<div style=\"font-size:1.55rem;font-weight:900;margin-bottom:14px;\">" + dinero(total) + "</div>",
            input: "radio",
            inputOptions: {
                efectivo: "\uD83D\uDCB5 Efectivo",
                mercadopago: "\uD83D\uDCF1 Mercado Pago",
                debito: "\uD83D\uDCB3 D\u00E9bito"
            },
            inputValidator: function (valor) {
                if (!valor)
                    return "Eleg\u00ED c\u00F3mo se pag\u00F3 la mesa.";
                return null;
            },
            showCancelButton: true,
            confirmButtonText: "Cobrar",
            cancelButtonText: "Cancelar",
            confirmButtonColor: "var(--verde-sanmartin)",
            cancelButtonColor: "var(--texto-mutado)",
            background: "var(--card-bg)",
            color: "var(--text-color)"
        });
    }
    function registrarCobroSalon(items, tipoPago, modoFiscal) {
        var cuenta = cuentaActual();
        if (!cuenta || !items.length) {
            return Promise.reject(new Error("No hay productos para cobrar."));
        }
        var url = root.getAttribute("data-charge-url");
        if (!url) {
            return Promise.reject(new Error("Falta configurar la URL de cobro del sal\u00F3n."));
        }
        enviando = true;
        render();
        return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": obtenerCsrf()
            },
            body: JSON.stringify({
                mesa: mesaActual,
                mozo: cuenta.mozo_nombre || "",
                tipo_pago: tipoPago,
                modo_fiscal: Boolean(modoFiscal),
                items: items
            })
        }).then(function (response) {
            return response.json().catch(function () { return {}; }).then(function (data) {
                if (!response.ok || data.status !== "ok") {
                    throw new Error(data.mensaje || "No se pudo registrar el cobro.");
                }
                return data;
            });
        }).finally(function () {
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
    function imprimirMesa() {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items.length || enviando) {
            return Promise.resolve();
        }
        return enviarTicket(obtenerItemsTicket(cuenta, false), "cuenta_mesa").then(function () {
            return Swal.fire({
                icon: "success",
                title: "Ticket enviado",
                timer: 900,
                showConfirmButton: false,
                background: "var(--card-bg)",
                color: "var(--text-color)"
            });
        }).catch(function (error) {
            mostrarError(error);
        });
    }
    function cobrarParcial() {
        var cuenta = cuentaActual();
        if (!cuenta)
            return;
        var resumen = resumenSeleccion(cuenta);
        var items = obtenerItemsTicket(cuenta, true);
        if (!items.length || resumen.cantidad <= 0)
            return;
        elegirMedioPago(resumen.total, "Cobro parcial \u00B7 Mesa " + mesaActual).then(function (resultado) {
            if (!resultado.isConfirmed)
                return;
            registrarCobroSalon(items, resultado.value, false).then(function () {
                cuenta.items.forEach(function (item) {
                    if (!item.seleccionado)
                        return;
                    var cantidad = Number(item.cant_pagar || item.cantidad);
                    item.cantidad -= cantidad;
                    item.seleccionado = false;
                    item.cant_pagar = item.cantidad > 0 ? item.cantidad : 0;
                });
                cuenta.items = cuenta.items.filter(function (item) {
                    return item.cantidad > 0;
                });
                recalcular(cuenta);
                guardar();
                if (!cuenta.items.length) {
                    Swal.fire({
                        icon: "success",
                        title: "Pago registrado",
                        text: "La venta ya qued\u00F3 incluida en el cierre de caja.",
                        timer: 1200,
                        showConfirmButton: false,
                        background: "var(--card-bg)",
                        color: "var(--text-color)"
                    });
                    liberarMesaActual();
                    return;
                }
                filaTeclado = Math.min(filaTeclado, cuenta.items.length - 1);
                actualizarMesas();
                render();
                Swal.fire({
                    icon: "success",
                    title: "Pago parcial registrado",
                    text: "Ya suma al cierre de caja.",
                    timer: 1100,
                    showConfirmButton: false,
                    background: "var(--card-bg)",
                    color: "var(--text-color)"
                });
            }).catch(mostrarError);
        });
    }
    function cobrarMesa(modoFiscal) {
        var cuenta = cuentaActual();
        modoFiscal = Boolean(modoFiscal);
        if (!cuenta || !cuenta.items.length)
            return;
        var numeroMesa = mesaActual;
        var items = obtenerItemsTicket(cuenta, false);
        var titulo = modoFiscal ? "Cierre fiscal · Mesa " + numeroMesa : "Cobrar Mesa " + numeroMesa;
        elegirMedioPago(cuenta.total, titulo).then(function (resultado) {
            if (!resultado.isConfirmed)
                return;
            registrarCobroSalon(items, resultado.value, modoFiscal).then(function () {
                Swal.fire({
                    icon: "success",
                    title: modoFiscal ? "Cierre fiscal registrado" : "Mesa cobrada",
                    text: modoFiscal ? "La venta quedó marcada para facturación fiscal real." : "La venta quedó registrada en el cierre de caja.",
                    timer: 1400,
                    showConfirmButton: false,
                    background: "var(--card-bg)",
                    color: "var(--text-color)"
                });
                liberarMesaActual();
            }).catch(mostrarError);
        });
    }

    function cobrarMesaFiscal() {
        var cuenta = cuentaActual();
        if (!cuenta || !cuenta.items.length)
            return;
        Swal.fire({
            icon: "warning",
            title: "Cierre fiscal",
            text: "Se va a cerrar la mesa como factura/ticket fiscal real.",
            showCancelButton: true,
            confirmButtonText: "Continuar",
            cancelButtonText: "Cancelar",
            confirmButtonColor: "var(--naranja-sterak)",
            background: "var(--card-bg)",
            color: "var(--text-color)"
        }).then(function (resultado) {
            if (resultado.isConfirmed) {
                cobrarMesa(true);
            }
        });
    }
    botonesMesa.forEach(function (boton) {
        boton.addEventListener("click", function () {
            seleccionarMesa(boton.getAttribute("data-mesa"));
        });
    });
    if (inputMesaRapida) {
        inputMesaRapida.addEventListener("keydown", function (event) {
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            seleccionarMesa(inputMesaRapida.value);
        });
    }
    if (inputCant) {
        inputCant.addEventListener("keydown", function (event) {
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            var cantidad = parseInt(inputCant.value, 10);
            if (!cantidad || cantidad < 1) {
                inputCant.value = 1;
            }
            if (buscador) {
                buscador.focus();
                buscador.select();
            }
        });
    }
    if (buscador) {
        buscador.addEventListener("input", function () {
            if (String(buscador.value || "").trim() === "..") {
                cerrarSugerencias();
                return;
            }
            sugerencias = buscarProductos(buscador.value);
            sugerenciaActiva = sugerencias.length ? 0 : -1;
            pintarSugerencias();
        });
        buscador.addEventListener("keydown", function (event) {
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
                cerrarSugerencias();
                return;
            }
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            var valor = String(buscador.value || "").trim();
            if (valor === "..") {
                buscador.value = "";
                cerrarSugerencias();
                imprimirMesa();
                enfocarCantidad();
                return;
            }
            if (valor === "//") {
                buscador.value = "";
                cerrarSugerencias();
                cobrarMesa(false);
                enfocarCantidad();
                return;
            }
            if (valor === "*") {
                buscador.value = "";
                cerrarSugerencias();
                cobrarMesaFiscal();
                enfocarCantidad();
                return;
            }
            if (sugerencias.length) {
                var index = sugerenciaActiva >= 0 ? sugerenciaActiva : 0;
                agregarProducto(sugerencias[index]);
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
    enfocarMesaRapida();
})();

// ==========================================================================
// MODAL DE BIENVENIDA DEL MENÚ PÚBLICO
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modal-bienvenida-menu");
    const botonCerrar = document.getElementById("btn-cerrar-bienvenida-menu");
    if (!modal || !botonCerrar) {
        return;
    }
    const fondo = modal.querySelector("[data-bienvenida-cerrar]");
    const claveSesion = "bienvenidaBuffetMostradaV1";
    let yaMostrada = false;
    try {
        yaMostrada = sessionStorage.getItem(claveSesion) === "1";
    }
    catch (error) {
        yaMostrada = false;
    }
    function abrirBienvenida() {
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("bienvenida-menu-abierta");
        try {
            sessionStorage.setItem(claveSesion, "1");
        }
        catch (error) {
            // Si el navegador bloquea sessionStorage, el modal igual funciona.
        }
        window.setTimeout(function () {
            botonCerrar.focus();
        }, 180);
    }
    function cerrarBienvenida() {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("bienvenida-menu-abierta");
    }
    botonCerrar.addEventListener("click", cerrarBienvenida);
    if (fondo) {
        fondo.addEventListener("click", cerrarBienvenida);
    }
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && modal.classList.contains("is-open")) {
            cerrarBienvenida();
        }
    });
    if (!yaMostrada) {
        window.addEventListener("load", function () {
            window.setTimeout(abrirBienvenida, 900);
        }, { once: true });
    }
});


// ==========================================================================
// AYUDA VISUAL DE ATAJOS SALÓN POS
// ==========================================================================
document.addEventListener("DOMContentLoaded", function () {
    var root = document.getElementById("salon-pos");
    var buscador = document.getElementById("buscador");
    if (!root || !buscador) {
        return;
    }

    buscador.placeholder = "Código o producto · .. ticket · // cobrar · * fiscal";

    var campoBuscador = buscador.closest(".salon-pos__field--buscador") || buscador.closest(".salon-pos__field") || buscador.parentElement;
    if (campoBuscador && !document.getElementById("salon-atajos-rapidos")) {
        campoBuscador.insertAdjacentHTML(
            "afterend",
            '<div id="salon-atajos-rapidos" class="salon-pos__atajos">' +
            '<span><b>..</b> imprimir ticket</span>' +
            '<span><b>//</b> cobrar normal</span>' +
            '<span><b>*</b> cierre fiscal</span>' +
            '</div>'
        );
    }
});


// ==========================================================================
// FIX ENCABEZADO COMANDA POS
// ==========================================================================
document.addEventListener("DOMContentLoaded", function () {
    var head = document.querySelector(".salon-pos__lista-head");
    if (!head || head.dataset.headFix === "1") {
        return;
    }

    head.dataset.headFix = "1";
    head.innerHTML =
        '<span class="col-cant">Cant.</span>' +
        '<span class="col-codigo">Código</span>' +
        '<span class="col-desc">Descripción</span>' +
        '<span class="col-unitario">Unitario</span>' +
        '<span class="col-total">Total</span>';
});


// ==========================================================================
// FIX FUERTE ENCABEZADO COMANDA POS
// Ejecuta ahora, en DOMContentLoaded y luego de renderizar.
(function () {
    function arreglarEncabezadoComandaPOS() {
        document.querySelectorAll(".salon-pos__lista-head").forEach(function (head) {
            head.classList.add("salon-pos__lista-head--fix");
            head.innerHTML =
                '<span class="col-cant">Cant.</span>' +
                '<span class="col-codigo">Código</span>' +
                '<span class="col-desc">Descripción</span>' +
                '<span class="col-unitario">Unitario</span>' +
                '<span class="col-total">Total</span>';
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", arreglarEncabezadoComandaPOS);
    } else {
        arreglarEncabezadoComandaPOS();
    }

    window.addEventListener("load", arreglarEncabezadoComandaPOS);
    window.setTimeout(arreglarEncabezadoComandaPOS, 250);
    window.setTimeout(arreglarEncabezadoComandaPOS, 900);

    document.addEventListener("click", function (event) {
        if (
            event.target.closest(".salon-pos__mesa") ||
            event.target.closest("#btn-imprimir-mesa") ||
            event.target.closest("#btn-accion-principal")
        ) {
            window.setTimeout(arreglarEncabezadoComandaPOS, 80);
        }
    });
})();


// ==========================================================================
// FIX DEFINITIVO COLUMNAS COMANDA POS
// Cant. | Cód. | Descripción | Unitario | Total
(function () {
    function columnasComandaPOS() {
        document.querySelectorAll(".salon-pos__lista-head").forEach(function (head) {
            head.className = "salon-pos__lista-head salon-pos__lista-head--columnas-fijas";
            head.innerHTML =
                '<span class="pos-col pos-col-cant">Cant.</span>' +
                '<span class="pos-col pos-col-codigo">Cód.</span>' +
                '<span class="pos-col pos-col-desc">Descripción</span>' +
                '<span class="pos-col pos-col-unitario">Unitario</span>' +
                '<span class="pos-col pos-col-total">Total</span>';
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", columnasComandaPOS);
    } else {
        columnasComandaPOS();
    }

    window.addEventListener("load", columnasComandaPOS);
    window.setTimeout(columnasComandaPOS, 150);
    window.setTimeout(columnasComandaPOS, 600);
    window.setTimeout(columnasComandaPOS, 1200);

    document.addEventListener("click", function (event) {
        if (
            event.target.closest(".salon-pos__mesa") ||
            event.target.closest("#btn-imprimir-mesa") ||
            event.target.closest("#btn-accion-principal") ||
            event.target.closest(".salon-pos__fila-pos")
        ) {
            window.setTimeout(columnasComandaPOS, 60);
        }
    });
})();


// ==========================================================================
// FIX INLINE COLUMNAS COMANDA POS
// Cant. | Cód. | Descripción | Unitario | Total
(function () {
    var GRID = "150px 110px minmax(260px, 1fr) 140px 140px";

    function aplicarEstiloHeader(head) {
        if (!head) return;

        head.innerHTML =
            '<span data-pos-head="cant">Cant.</span>' +
            '<span data-pos-head="codigo">Cód.</span>' +
            '<span data-pos-head="desc">Descripción</span>' +
            '<span data-pos-head="unitario">Unitario</span>' +
            '<span data-pos-head="total">Total</span>';

        head.style.setProperty("display", "grid", "important");
        head.style.setProperty("grid-template-columns", GRID, "important");
        head.style.setProperty("column-gap", "16px", "important");
        head.style.setProperty("align-items", "center", "important");
        head.style.setProperty("width", "100%", "important");
        head.style.setProperty("box-sizing", "border-box", "important");
        head.style.setProperty("padding", "0 12px", "important");
        head.style.setProperty("min-height", "38px", "important");
        head.style.setProperty("white-space", "nowrap", "important");

        var hijos = Array.prototype.slice.call(head.children);
        hijos.forEach(function (span, index) {
            span.style.setProperty("display", "block", "important");
            span.style.setProperty("min-width", "0", "important");
            span.style.setProperty("overflow", "hidden", "important");
            span.style.setProperty("text-overflow", "ellipsis", "important");
            span.style.setProperty("white-space", "nowrap", "important");
            span.style.setProperty("grid-column", String(index + 1), "important");
            span.style.setProperty("text-align", index >= 3 ? "right" : (index === 0 ? "center" : "left"), "important");
        });
    }

    function aplicarEstiloCelda(elemento, columna, alineacion) {
        if (!elemento) return;
        elemento.style.setProperty("grid-column", String(columna), "important");
        elemento.style.setProperty("min-width", "0", "important");
        elemento.style.setProperty("text-align", alineacion || "left", "important");
        if (columna >= 4) {
            elemento.style.setProperty("white-space", "nowrap", "important");
            elemento.style.setProperty("font-weight", "950", "important");
        }
    }

    function aplicarEstiloFila(fila) {
        if (!fila) return;

        fila.style.setProperty("display", "grid", "important");
        fila.style.setProperty("grid-template-columns", GRID, "important");
        fila.style.setProperty("column-gap", "16px", "important");
        fila.style.setProperty("align-items", "center", "important");
        fila.style.setProperty("width", "100%", "important");
        fila.style.setProperty("box-sizing", "border-box", "important");
        fila.style.setProperty("padding", "8px 12px", "important");

        aplicarEstiloCelda(fila.querySelector(".salon-pos__fila-cant"), 1, "center");
        aplicarEstiloCelda(fila.querySelector(".salon-pos__fila-codigo"), 2, "left");
        aplicarEstiloCelda(fila.querySelector(".salon-pos__fila-descripcion"), 3, "left");
        aplicarEstiloCelda(fila.querySelector(".salon-pos__fila-unitario"), 4, "right");
        aplicarEstiloCelda(fila.querySelector(".salon-pos__fila-total"), 5, "right");

        var descStrong = fila.querySelector(".salon-pos__fila-descripcion > strong");
        if (descStrong) {
            descStrong.style.setProperty("white-space", "normal", "important");
            descStrong.style.setProperty("overflow", "visible", "important");
            descStrong.style.setProperty("text-overflow", "clip", "important");
        }
    }

    function arreglarColumnasComanda() {
        document.querySelectorAll(".salon-pos__lista-head").forEach(aplicarEstiloHeader);
        document.querySelectorAll(".salon-pos__fila-pos").forEach(aplicarEstiloFila);
    }

    function observarComanda() {
        var lista = document.getElementById("lista-comanda") || document.querySelector(".salon-pos__lista-pos");
        if (!lista || lista.dataset.columnasObserver === "1") return;

        lista.dataset.columnasObserver = "1";
        var observer = new MutationObserver(function () {
            arreglarColumnasComanda();
        });

        observer.observe(lista, {
            childList: true,
            subtree: true
        });
    }

    function iniciarFix() {
        arreglarColumnasComanda();
        observarComanda();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciarFix);
    } else {
        iniciarFix();
    }

    window.addEventListener("load", iniciarFix);

    [100, 300, 700, 1200, 2000].forEach(function (tiempo) {
        window.setTimeout(iniciarFix, tiempo);
    });

    document.addEventListener("click", function (event) {
        if (
            event.target.closest(".salon-pos__mesa") ||
            event.target.closest(".salon-pos__fila-pos") ||
            event.target.closest("#btn-imprimir-mesa") ||
            event.target.closest("#btn-accion-principal") ||
            event.target.closest("[data-action]")
        ) {
            window.setTimeout(iniciarFix, 50);
            window.setTimeout(iniciarFix, 180);
        }
    });

    document.addEventListener("input", function (event) {
        if (event.target && event.target.id === "buscador") {
            window.setTimeout(iniciarFix, 80);
        }
    });
})();


// ==========================================================================
// FIX HEADER NUEVO COMANDA POS
// Oculta la cabecera vieja y crea una nueva alineada con la fila real.
(function () {
    var labels = [
        { key: "cant", text: "Cant.", selector: ".salon-pos__fila-cant", align: "center" },
        { key: "codigo", text: "Cód.", selector: ".salon-pos__fila-codigo", align: "left" },
        { key: "desc", text: "Descripción", selector: ".salon-pos__fila-descripcion", align: "left" },
        { key: "unitario", text: "Unitario", selector: ".salon-pos__fila-unitario", align: "right" },
        { key: "total", text: "Total", selector: ".salon-pos__fila-total", align: "right" }
    ];

    function ocultarCabecerasViejas(modal) {
        Array.prototype.slice.call(modal.querySelectorAll(".salon-pos__lista-head, .salon-pos__lista-head--fix, .salon-pos__lista-head--real, .salon-pos__lista-head--columnas-fijas")).forEach(function (head) {
            if (head.id !== "comanda-header-nuevo") {
                head.style.setProperty("display", "none", "important");
                head.style.setProperty("height", "0", "important");
                head.style.setProperty("min-height", "0", "important");
                head.style.setProperty("padding", "0", "important");
                head.style.setProperty("overflow", "hidden", "important");
            }
        });

        // Por si la cabecera vieja no tenía clase exacta, ocultamos el bloque que solo diga esos títulos.
        Array.prototype.slice.call(modal.querySelectorAll("div, section, header")).forEach(function (el) {
            if (el.id === "comanda-header-nuevo") return;
            if (el.querySelector("button,input,select,textarea,.salon-pos__fila-pos")) return;

            var texto = String(el.textContent || "").toLowerCase().replace(/\s+/g, "");
            var pareceHeader = texto.indexOf("cant") !== -1 && texto.indexOf("codigo") !== -1 && texto.indexOf("descripcion") !== -1 && texto.length < 90;

            if (pareceHeader) {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("min-height", "0", "important");
                el.style.setProperty("padding", "0", "important");
                el.style.setProperty("overflow", "hidden", "important");
            }
        });
    }

    function crearHeader(modal) {
        var header = document.getElementById("comanda-header-nuevo");
        if (header) return header;

        var lista = document.getElementById("lista-comanda") || modal.querySelector(".salon-pos__lista-pos");
        if (!lista) return null;

        header = document.createElement("div");
        header.id = "comanda-header-nuevo";
        header.className = "comanda-header-nuevo";

        header.innerHTML = labels.map(function (item) {
            return '<span data-col="' + item.key + '">' + item.text + '</span>';
        }).join("");

        lista.parentNode.insertBefore(header, lista);
        return header;
    }

    function fallback(header) {
        var width = header.clientWidth || 1000;
        var posiciones = [
            { key: "cant", left: 0, width: 150, align: "center" },
            { key: "codigo", left: 165, width: 100, align: "left" },
            { key: "desc", left: 280, width: Math.max(260, width - 600), align: "left" },
            { key: "unitario", left: Math.max(0, width - 295), width: 130, align: "right" },
            { key: "total", left: Math.max(0, width - 145), width: 130, align: "right" }
        ];

        posiciones.forEach(function (p) {
            posicionar(header, p.key, p.left, p.width, p.align);
        });
    }

    function posicionar(header, key, left, width, align) {
        var span = header.querySelector('[data-col="' + key + '"]');
        if (!span) return;

        span.style.setProperty("position", "absolute", "important");
        span.style.setProperty("left", Math.max(0, Math.round(left)) + "px", "important");
        span.style.setProperty("top", "50%", "important");
        span.style.setProperty("transform", "translateY(-50%)", "important");
        span.style.setProperty("width", Math.max(45, Math.round(width)) + "px", "important");
        span.style.setProperty("text-align", align, "important");
        span.style.setProperty("white-space", "nowrap", "important");
        span.style.setProperty("overflow", "hidden", "important");
        span.style.setProperty("text-overflow", "ellipsis", "important");
    }

    function alinearHeader(modal, header) {
        var row = modal.querySelector(".salon-pos__fila-pos");
        if (!row) {
            fallback(header);
            return;
        }

        var headerRect = header.getBoundingClientRect();

        labels.forEach(function (item) {
            var cell = row.querySelector(item.selector);
            if (!cell) return;

            var rect = cell.getBoundingClientRect();
            posicionar(header, item.key, rect.left - headerRect.left, rect.width, item.align);
        });
    }

    function arreglar() {
        var modal = document.getElementById("salon-comanda-modal") || document.body;
        if (!modal) return;

        ocultarCabecerasViejas(modal);

        var header = crearHeader(modal);
        if (!header) return;

        header.style.setProperty("display", "block", "important");
        alinearHeader(modal, header);
    }

    function observar() {
        var modal = document.getElementById("salon-comanda-modal") || document.body;
        if (!modal || modal.dataset.headerNuevoObserver === "1") return;

        modal.dataset.headerNuevoObserver = "1";
        var observer = new MutationObserver(function () {
            window.requestAnimationFrame(arreglar);
        });

        observer.observe(modal, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    function iniciar() {
        arreglar();
        observar();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }

    window.addEventListener("load", iniciar);
    window.addEventListener("resize", arreglar);

    [80, 200, 500, 900, 1600, 2500].forEach(function (t) {
        window.setTimeout(iniciar, t);
    });

    document.addEventListener("click", function () {
        window.setTimeout(arreglar, 50);
        window.setTimeout(arreglar, 220);
    });

    document.addEventListener("input", function () {
        window.setTimeout(arreglar, 80);
    });
})();


// ==========================================================================
// FIX OCULTAR LINEA VIEJA CABECERA COMANDA
// Oculta cualquier cabecera antigua que haya quedado arriba del header nuevo.
(function () {
    function normalizar(texto) {
        return String(texto || "")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, "")
            .trim();
    }

    function ocultarElemento(el) {
        if (!el || el.id === "comanda-header-nuevo") return;
        el.classList.add("comanda-header-viejo-oculto");
        el.style.setProperty("display", "none", "important");
        el.style.setProperty("height", "0", "important");
        el.style.setProperty("min-height", "0", "important");
        el.style.setProperty("max-height", "0", "important");
        el.style.setProperty("padding", "0", "important");
        el.style.setProperty("margin", "0", "important");
        el.style.setProperty("border", "0", "important");
        el.style.setProperty("overflow", "hidden", "important");
        el.style.setProperty("opacity", "0", "important");
        el.style.setProperty("visibility", "hidden", "important");
    }

    function ocultarLineaVieja() {
        var modal = document.getElementById("salon-comanda-modal") || document;
        var nuevo = document.getElementById("comanda-header-nuevo");

        modal.querySelectorAll(".salon-pos__lista-head, .salon-pos__lista-head--fix, .salon-pos__lista-head--real, .salon-pos__lista-head--columnas-fijas").forEach(function (el) {
            ocultarElemento(el);
        });

        // Si quedó una línea de texto suelta arriba del header nuevo, la detectamos por contenido.
        modal.querySelectorAll("div, section, header, p, span").forEach(function (el) {
            if (!el || el.id === "comanda-header-nuevo") return;
            if (nuevo && nuevo.contains(el)) return;
            if (el.querySelector("button,input,select,textarea")) return;
            if (el.querySelector("#comanda-header-nuevo")) return;
            if (el.querySelector(".salon-pos__fila-pos")) return;

            var texto = normalizar(el.textContent);
            if (!texto) return;

            var pareceCabecera =
                texto === "cant.codigo.descripcionunitariototal" ||
                texto === "cant.cod.descripcionunitariototal" ||
                texto === "cant.cod.descripcionunitario" ||
                texto === "cant.codigodescripcionunitario" ||
                (
                    texto.indexOf("cant") !== -1 &&
                    texto.indexOf("codigo") !== -1 &&
                    texto.indexOf("descripcion") !== -1 &&
                    texto.length <= 55
                );

            if (pareceCabecera) {
                ocultarElemento(el);
            }
        });
    }

    function iniciarOcultador() {
        ocultarLineaVieja();

        var modal = document.getElementById("salon-comanda-modal") || document.body;
        if (modal && modal.dataset.ocultarHeaderViejoObserver !== "1") {
            modal.dataset.ocultarHeaderViejoObserver = "1";
            new MutationObserver(function () {
                window.requestAnimationFrame(ocultarLineaVieja);
            }).observe(modal, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciarOcultador);
    } else {
        iniciarOcultador();
    }

    window.addEventListener("load", iniciarOcultador);
    [100, 300, 800, 1500, 2500].forEach(function (t) {
        window.setTimeout(iniciarOcultador, t);
    });

    document.addEventListener("click", function () {
        window.setTimeout(ocultarLineaVieja, 60);
        window.setTimeout(ocultarLineaVieja, 250);
    });
})();


// ==========================================================================
// FIX MESA VACÍA COMANDA POS
// Oculta la cabecera cuando no hay productos y centra "Mesa vacía".
(function () {
    function tieneProductosComanda(lista) {
        if (!lista) return false;

        if (lista.querySelector(".salon-pos__fila-pos")) return true;
        if (lista.querySelector("tr")) return true;

        return String(lista.textContent || "").trim().length > 0;
    }

    function arreglarMesaVaciaComanda() {
        var lista = document.getElementById("lista-comanda");
        var vacia = document.getElementById("salon-lista-vacia");
        var headerNuevo = document.getElementById("comanda-header-nuevo");
        var wrap = lista ? lista.closest(".salon-pos__tabla-wrap") : null;

        var hayProductos = tieneProductosComanda(lista);

        if (wrap) {
            wrap.classList.toggle("is-empty", !hayProductos);
            wrap.classList.toggle("has-products", hayProductos);
        }

        if (headerNuevo) {
            headerNuevo.style.setProperty("display", hayProductos ? "block" : "none", "important");
            headerNuevo.style.setProperty("height", hayProductos ? "38px" : "0", "important");
            headerNuevo.style.setProperty("min-height", hayProductos ? "38px" : "0", "important");
            headerNuevo.style.setProperty("margin", hayProductos ? "8px 0 0" : "0", "important");
            headerNuevo.style.setProperty("padding", hayProductos ? "0 12px" : "0", "important");
            headerNuevo.style.setProperty("overflow", "hidden", "important");
            headerNuevo.style.setProperty("visibility", hayProductos ? "visible" : "hidden", "important");
            headerNuevo.style.setProperty("opacity", hayProductos ? "1" : "0", "important");
        }

        if (vacia) {
            if (hayProductos) {
                vacia.hidden = true;
                vacia.style.setProperty("display", "none", "important");
            } else {
                vacia.hidden = false;
                vacia.style.setProperty("display", "flex", "important");
                vacia.style.setProperty("position", "relative", "important");
                vacia.style.setProperty("inset", "auto", "important");
                vacia.style.setProperty("transform", "none", "important");
                vacia.style.setProperty("width", "100%", "important");
                vacia.style.setProperty("min-height", "96px", "important");
                vacia.style.setProperty("align-items", "center", "important");
                vacia.style.setProperty("justify-content", "center", "important");
                vacia.style.setProperty("flex-direction", "column", "important");
                vacia.style.setProperty("text-align", "center", "important");
                vacia.style.setProperty("margin", "8px 0 0", "important");
                vacia.style.setProperty("pointer-events", "none", "important");
            }
        }
    }

    function iniciarFixMesaVacia() {
        arreglarMesaVaciaComanda();

        var modal = document.getElementById("salon-comanda-modal") || document.body;
        if (modal && modal.dataset.mesaVaciaObserver !== "1") {
            modal.dataset.mesaVaciaObserver = "1";

            new MutationObserver(function () {
                window.requestAnimationFrame(arreglarMesaVaciaComanda);
                window.setTimeout(arreglarMesaVaciaComanda, 80);
            }).observe(modal, {
                childList: true,
                subtree: true,
                characterData: true,
                attributes: true
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciarFixMesaVacia);
    } else {
        iniciarFixMesaVacia();
    }

    window.addEventListener("load", iniciarFixMesaVacia);
    window.addEventListener("resize", arreglarMesaVaciaComanda);

    [80, 200, 500, 1000, 1800, 3000].forEach(function (t) {
        window.setTimeout(iniciarFixMesaVacia, t);
    });

    document.addEventListener("click", function () {
        window.setTimeout(arreglarMesaVaciaComanda, 50);
        window.setTimeout(arreglarMesaVaciaComanda, 180);
        window.setTimeout(arreglarMesaVaciaComanda, 500);
    });

    document.addEventListener("input", function () {
        window.setTimeout(arreglarMesaVaciaComanda, 80);
        window.setTimeout(arreglarMesaVaciaComanda, 220);
    });
})();

