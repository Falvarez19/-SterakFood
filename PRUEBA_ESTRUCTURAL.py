import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parent
for f in ROOT.rglob('*.py'):
    if '__pycache__' in f.parts: continue
    ast.parse(f.read_text(encoding='utf-8-sig'), filename=str(f))
print('OK: sintaxis Python en todos los archivos')

views=(ROOT/'pedidos/views.py').read_text(encoding='utf8')
assert "secrets.compare_digest" in views and "settings.PANEL_PIN" in views
assert "'5968'" not in views
assert (ROOT/'pedidos/arca_wsfe.py').exists()
assert (ROOT/'pedidos/migrations/0025_facturas_reales.py').exists()
assert "ARCA_FISCAL_ENABLED=0" in (ROOT/'.env.example').read_text()
print('OK: controles básicos de integración y emisión desactivada')
