"""Importa codigos DTMax para uso exclusivo del POS de Salon.

Nunca asigna puntos de venta publicos, ni toca productos de otras categorias.
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from django.db import transaction
from .models import Categoria, Producto


class ErrorCatalogoSalon(ValueError):
    pass


def leer_catalogo_salon(contenido):
    if len(contenido) > 2 * 1024 * 1024:
        raise ErrorCatalogoSalon('El archivo supera el limite de 2 MB.')
    try:
        texto = contenido.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            texto = contenido.decode('cp1252')
        except UnicodeDecodeError:
            raise ErrorCatalogoSalon('El CSV debe estar codificado en UTF-8 o Windows-1252.')

    # El archivo provisto por DTMax usa ; como separador.
    lector = csv.DictReader(io.StringIO(texto), delimiter=';')
    encabezados = [(col or '').lstrip('\ufeff').strip() for col in (lector.fieldnames or [])]
    requeridos = {'Codigo', 'Producto', 'Precio', 'Activo'}
    if not requeridos.issubset(set(encabezados)):
        raise ErrorCatalogoSalon('Faltan columnas: Codigo, Producto, Precio y Activo (separadas por ;).')

    filas = []
    codigos = set()
    for numero, fila in enumerate(lector, start=2):
        fila = {str(clave or '').strip(): str(valor or '').strip() for clave, valor in fila.items() if clave is not None}
        codigo = fila.get('Codigo', '')
        nombre = fila.get('Producto', '')
        precio_original = fila.get('Precio', '')
        activo_original = fila.get('Activo', '')
        # DTMax exporta filas vacias al final; ignorarlas.
        if not any((codigo, nombre, precio_original, activo_original)):
            continue
        if not codigo.isdecimal() or int(codigo) <= 0 or len(codigo) > 20:
            raise ErrorCatalogoSalon(f'Fila {numero}: codigo numerico invalido.')
        if not nombre or len(nombre) > 200:
            raise ErrorCatalogoSalon(f'Fila {numero}: nombre vacio o demasiado largo.')
        if activo_original not in ('0', '1'):
            raise ErrorCatalogoSalon(f'Fila {numero}: Activo debe ser 0 o 1.')
        try:
            precio = Decimal(precio_original.replace(',', '.'))
        except InvalidOperation:
            raise ErrorCatalogoSalon(f'Fila {numero}: precio invalido.')
        if not precio.is_finite() or precio < 0 or precio > Decimal('99999999.99'):
            raise ErrorCatalogoSalon(f'Fila {numero}: precio fuera del rango permitido.')
        if codigo in codigos:
            raise ErrorCatalogoSalon(f'Fila {numero}: codigo {codigo} duplicado en CSV.')
        codigos.add(codigo)
        filas.append({'codigo': codigo, 'nombre': nombre, 'precio': precio, 'activo': activo_original == '1'})
    if not filas:
        raise ErrorCatalogoSalon('El archivo no contiene productos.')
    return filas


@transaction.atomic
def importar_catalogo_salon(filas):
    # El menu web excluye por nombre la categoria exacta 'Salon'.
    categoria = Categoria.objects.filter(nombre='Salon').order_by('id').first()
    if categoria is None:
        categoria = Categoria.objects.create(nombre='Salon')

    codigos = [fila['codigo'] for fila in filas]
    existentes = set(Producto.objects.filter(
        categoria=categoria, codigo_rapido__in=codigos,
    ).values_list('codigo_rapido', flat=True))
    nuevas = []
    inactivas = 0
    for fila in filas:
        # Un codigo ya existente en Salon no se duplica ni se sobrescribe.
        if fila['codigo'] in existentes:
            continue
        if not fila['activo']:
            inactivas += 1
            continue
        nuevas.append(Producto(
            categoria=categoria,
            nombre=fila['nombre'],
            codigo_rapido=fila['codigo'],
            precio=fila['precio'],
            descripcion='', disponible=True, en_promocion=False,
            orden=0,
        ))
    Producto.objects.bulk_create(nuevas, batch_size=200)
    # Sin M2M puntos_venta: no pertenecen a ningun mostrador publico.
    return {
        'creados': len(nuevas),
        'existentes': sum(1 for fila in filas if fila['codigo'] in existentes),
        'inactivos': inactivas,
        'procesados': len(filas),
    }
