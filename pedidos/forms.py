from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # Traemos todos los campos de tu modelo
        fields = ['nombre', 'categoria', 'puntos_venta', 'precio', 'orden', 'imagen', 
                  'descripcion', 'disponible', 'variantes', 'guarniciones', 
                  'puntos_coccion', 'rellenos', 'salsas', 'adicionales', 'opcion_hielo']
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width: 100%; padding: 8px;'}),
            # Las opciones de personalización
            'variantes': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'guarniciones': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'puntos_coccion': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'rellenos': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'salsas': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'adicionales': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
            'opcion_hielo': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%; padding: 8px;'}),
        }