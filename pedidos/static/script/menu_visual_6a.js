/* Solo menú público: foto o GIF de portada elegido desde Mi negocio. */
(() => {
 'use strict';
 document.body.classList.add('sf6a-menu');
 const script=document.currentScript;
 const portada=script?.getAttribute('data-portada');
 const logo=script?.getAttribute('data-logo');
 if (!portada) return;
 const img=document.querySelector('.hero-foto-principal, .hero-foto-side img:not(.hero-logo-flotante), .portada-menu img, .hero-image img, img.hero-foto, img.hero-imagen');
 if(img){img.src=portada;img.decoding='async';}
 const logoImg=document.querySelector('.hero-logo-flotante');
 if(logoImg && logo)logoImg.src=logo;
})();
