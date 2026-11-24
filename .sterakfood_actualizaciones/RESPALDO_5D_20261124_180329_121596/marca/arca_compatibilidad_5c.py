"""Compatibilidad fiscal declarativa; no genera comprobantes.

No atribuir disponibilidad de Factura C hasta que el WSFEv1, las reglas
fiscales, el modelo, impresión y homologación estén implementados.
"""


def resumen_fiscal_5c(condicion):
    if condicion == 'ri':
        return {
            'regimen': 'Responsable inscripto',
            'comprobante': 'Factura B (código ARCA 6)',
            'estado': 'Motor parcial existente',
            'detalle': 'Solo consumidor final con conceptos íntegramente gravados al 21 %. Requiere autorización y homologación antes de producción.',
            'soportado': True,
        }
    if condicion == 'monotributo':
        return {
            'regimen': 'Monotributista',
            'comprobante': 'Factura C (código ARCA 11)',
            'estado': 'Pendiente de desarrollar',
            'detalle': 'Factura C requiere una solicitud fiscal distinta y validaciones de receptor. No está habilitada aún para emitir.',
            'soportado': False,
        }
    if condicion == 'exento':
        return {
            'regimen': 'Exento',
            'comprobante': 'Según operación y condición fiscal',
            'estado': 'Pendiente de desarrollar',
            'detalle': 'No activar sin determinar tipo de comprobante y tratamiento impositivo aplicables.',
            'soportado': False,
        }
    return {
        'regimen': 'Otra condición',
        'comprobante': 'Por determinar',
        'estado': 'Pendiente de desarrollar',
        'detalle': 'Revisar la categoría fiscal antes de habilitar la emisión.',
        'soportado': False,
    }
