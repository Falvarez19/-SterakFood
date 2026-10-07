# STERAKFOOD: formularios de administración de productos
from django import forms
from .models import Producto
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'codigo_rapido',
            'categoria',
            'puntos_venta',
            'precio',
            'orden',
            'imagen',
            'descripcion',
            'disponible',
            'en_promocion',
            'variantes',
            'guarniciones',
            'puntos_coccion',
            'rellenos',
            'salsas',
            'adicionales',
            'opcion_hielo',
        ]
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'codigo_rapido': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;',
                    'placeholder': 'Ej: 114, 216...'
                }
            ),
            'precio': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;',
                    'step': '0.01'
                }
            ),
            'orden': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'disponible': forms.CheckboxInput(
                attrs={
                    'style': 'width: 20px; height: 20px;'
                }
            ),
            'en_promocion': forms.CheckboxInput(
                attrs={
                    'style': 'width: 22px; height: 22px; cursor: pointer;'
                }
            ),
            'variantes': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'guarniciones': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'puntos_coccion': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'rellenos': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'salsas': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'adicionales': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
            'opcion_hielo': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px;'
                }
            ),
        }
