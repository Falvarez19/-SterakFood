/* Vista previa en tiempo real: no guarda datos sin pulsar Guardar. */
(() => {
 'use strict';
 const form=document.getElementById('sf-marca-form');
 const preview=document.getElementById('sf6a-preview');
 if(!form||!preview)return;
 const fonts={original:'inherit',moderna:'"Trebuchet MS", "Segoe UI", Arial, sans-serif',clasica:'Georgia,serif',elegante:'"Palatino Linotype",Georgia,serif',cursiva:'"Segoe Script","Brush Script MT",cursive',suave:'"Segoe UI",sans-serif'};
 let bgUrl=null,heroUrl=null;
 const field=(name)=>form.elements.namedItem(name);
 const setVar=(name,value)=>preview.style.setProperty(name,value);
 const render=()=>{
   const font=field('menu_fuente')?.value||'original';
   setVar('--sf6a-font',fonts[font]||'inherit');
   for(const [name,variable] of [['menu_titulo_px','--sf6a-title'],['menu_producto_px','--sf6a-product'],['menu_descripcion_px','--sf6a-description'],['menu_precio_px','--sf6a-price'],['menu_borde_px','--sf6a-radius']]){
     const val=field(name)?.value;
     if(val)setVar(variable,`${val}px`);
   }
   const color=field('menu_color_boton')?.value||'#ff6600';setVar('--sf6a-button',color);
   const btn=field('menu_boton_estilo')?.value;
   const radius=btn==='redondo'?'999px':btn==='recto'?'3px':(field('menu_borde_px')?.value||12)+'px';
   setVar('--sf6a-button-radius',radius);
   setVar('--sf6a-shadow',field('menu_sombra_tarjetas')?.checked?'0 8px 24px rgba(0,0,0,.25)':'none');
   const overlay=Number(field('menu_oscurecer')?.value||0)/100;setVar('--sf6a-overlay',Math.min(.85,Math.max(0,overlay)));
   preview.style.backgroundColor=field('menu_color_fondo')?.value||'#121212';
   for(const input of form.querySelectorAll('[data-sf6a-output]')){
     const output=document.getElementById(input.dataset.sf6aOutput);
     if(output)output.textContent=input.value+(input.name==='menu_oscurecer'?'%':' px');
   }
 };
 for(const e of form.querySelectorAll('[name^="menu_"]'))e.addEventListener('input',render);
 const currentBackground=preview.dataset.sf6aBackground;
 if(currentBackground)preview.style.backgroundImage=`url("${currentBackground}")`;
 const background=field('archivo_fondo_menu');
 const media=field('archivo_portada_menu');
 const hero=document.getElementById('sf6a-image-preview');
 function urlFromFile(input,oldUrl){if(oldUrl)URL.revokeObjectURL(oldUrl);const f=input?.files?.[0];return f?URL.createObjectURL(f):null;}
 background?.addEventListener('change',()=>{bgUrl=urlFromFile(background,bgUrl);if(bgUrl){preview.style.backgroundImage=`url("${bgUrl}")`;}render();});
 media?.addEventListener('change',()=>{heroUrl=urlFromFile(media,heroUrl);if(hero&&heroUrl)hero.src=heroUrl;render();});
 window.addEventListener('beforeunload',()=>{if(bgUrl)URL.revokeObjectURL(bgUrl);if(heroUrl)URL.revokeObjectURL(heroUrl);});
 render();
})();
