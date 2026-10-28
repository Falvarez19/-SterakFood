"""Importacion por consola del catalogo DTMax para Salon POS (no menu publico)."""
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from pedidos.salon_csv import leer_catalogo_salon, importar_catalogo_salon, ErrorCatalogoSalon


class Command(BaseCommand):
    help = 'Previsualiza o importa productos del CSV DTMax exclusivamente para Salon POS.'

    def add_arguments(self, parser):
        defecto = Path(__file__).resolve().parents[2] / 'data' / 'productos_dtmax_salon.csv'
        parser.add_argument('--archivo', default=str(defecto), help='Ruta al CSV con separador ;')
        parser.add_argument('--aplicar', action='store_true', help='Guardar los productos en la base de datos.')

    def handle(self, *args, **options):
        archivo = Path(options['archivo'])
        try:
            filas = leer_catalogo_salon(archivo.read_bytes())
        except OSError as exc:
            raise CommandError(f'No se pudo abrir {archivo}: {exc}')
        except ErrorCatalogoSalon as exc:
            raise CommandError(str(exc))
        self.stdout.write(f'CSV valido: {len(filas)} codigos. Muestra: ' + ', '.join(
            f"{f['codigo']}={f['nombre']}" for f in filas[:3]
        ))
        if not options['aplicar']:
            self.stdout.write(self.style.WARNING('PREVISUALIZACION: no se modifico ningun dato. Usar --aplicar para importar.'))
            return
        resultado = importar_catalogo_salon(filas)
        self.stdout.write(self.style.SUCCESS(
            f"Importados: {resultado['creados']}; ya existentes (sin cambios): {resultado['existentes']}; "
            f"inactivos omitidos: {resultado['inactivos']}. Solo Salon POS."
        ))
