(function(){'use strict';
  async function pedirReceptor(){
    if(!window.Swal){alert('Falta el componente de confirmación fiscal.');return null;}
    const html='<div class="sf5j-form" style="text-align:left;display:grid;gap:10px">'
      +'<label>Receptor<select id="sf5j-cond" class="swal2-input" style="margin:4px 0;width:100%"><option value="consumidor_final">Consumidor Final</option><option value="responsable_inscripto">Responsable inscripto</option><option value="monotributo">Monotributista</option></select></label>'
      +'<label>DNI o CUIT (obligatorio para empresa)<input id="sf5j-doc" class="swal2-input" style="margin:4px 0;width:100%" placeholder="Sin guiones" autocomplete="off"></label>'
      +'<label>Nombre / razón social<input id="sf5j-nombre" class="swal2-input" style="margin:4px 0;width:100%" autocomplete="off" maxlength="150"></label>'
      +'<label style="display:flex;align-items:center;gap:8px"><input type="checkbox" id="sf5j-iva"> Confirmo que todos los ítems gravados llevan IVA 21 % (si emisor RI)</label>'
      +'</div>';
    const result=await Swal.fire({title:'Datos del comprobante',html,showCancelButton:true,
      confirmButtonText:'Continuar con ARCA',cancelButtonText:'Cancelar',
      background:'var(--card-bg)',color:'var(--text-color)',
      preConfirm:()=>({condicion_receptor:document.getElementById('sf5j-cond').value,
        numero_documento:document.getElementById('sf5j-doc').value.trim(),
        nombre_receptor:document.getElementById('sf5j-nombre').value.trim(),
        iva_21_confirmado:document.getElementById('sf5j-iva').checked})});
    return result.isConfirmed?result.value:null;
  }
  window.SterakFiscal5J={pedirReceptor};
})();
