/*
 * STERAKFOOD / Dashboard: navegación de secciones.
 *
 * Por qué existe: los accesos administrativos antes ocupaban la misma barra que
 * Salón, Pedidos y Cuentas. Este módulo mantiene los IDs históricos y la función
 * global abrirTab(), pero aísla la navegación del script del menú público.
 * No hace llamadas al servidor ni interviene en ventas, pagos o pedidos.
 */
(function () {
    'use strict';

    var nav = document.getElementById('sf-panel-nav');
    if (!nav) return;

    var panel = document.querySelector('.sf-dash-panel');
    var more = document.getElementById('sf-panel-nav-more');
    var toggle = document.getElementById('sf-panel-nav-toggle');
    var menu = document.getElementById('sf-panel-nav-menu');
    var STORAGE_KEY = 'tabDashboardActiva';  // Compatibilidad con enlaces de Salón.

    function cerrarMenu(devolverFoco) {
        menu.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
        if (devolverFoco) toggle.focus();
    }

    function abrirMenu() {
        menu.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
    }

    function existeTab(nombre) {
        var tab = document.getElementById('tab-' + nombre);
        return Boolean(tab && panel.contains(tab));
    }

    // Es público porque los enlaces y acciones existentes llaman a abrirTab().
    // Si un parámetro ?tab= está mal, no escondemos todas las secciones.
    window.sterakPanelNavAbrir = function (nombre) {
        if (!existeTab(nombre)) return false;

        panel.querySelectorAll('.tab-content').forEach(function (tab) {
            tab.style.display = tab.id === 'tab-' + nombre ? 'block' : 'none';
        });
        nav.querySelectorAll('.panel-tab-btn, .sf-panel-nav__subitem').forEach(function (item) {
            var activa = item.id === 'btn-tab-' + nombre;
            item.classList.toggle('active', activa);
            if (item.tagName === 'BUTTON') item.setAttribute('aria-current', activa ? 'page' : 'false');
        });

        var actual = document.getElementById('btn-tab-' + nombre);
        toggle.classList.toggle('is-section-active', Boolean(actual && menu.contains(actual)));
        cerrarMenu(false);
        try { window.localStorage.setItem(STORAGE_KEY, nombre); }
        catch (error) { /* Navegar debe seguir funcionando con almacenamiento bloqueado. */ }
        return true;
    };

    toggle.addEventListener('click', function () {
        if (menu.hidden) abrirMenu();
        else cerrarMenu(false);
    });

    document.addEventListener('click', function (event) {
        if (!more.contains(event.target)) cerrarMenu(false);
    });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !menu.hidden) cerrarMenu(true);
    });

    // Prioridades: enlace ?tab= (desde Salón) > pestaña recordada > Inicio.
    var urlTab = new URLSearchParams(window.location.search).get('tab');
    var recordada = null;
    try { recordada = window.localStorage.getItem(STORAGE_KEY); }
    catch (error) { /* Navegación normal sin almacenamiento. */ }
    var inicial = existeTab(urlTab) ? urlTab : (existeTab(recordada) ? recordada : 'inicio');
    // Reutilizamos el nombre usado por los accesos existentes sin modificar
    // el script global de la web pública (miles de líneas con otras funciones).
    // Solo se reemplaza en la página del Dashboard.
    window.abrirTab = window.sterakPanelNavAbrir;
    window.sterakPanelNavAbrir(inicial);
})();
