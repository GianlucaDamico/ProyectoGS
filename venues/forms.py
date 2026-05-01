from django import forms
from .models import Court, Sport, Surface

class CourtForm(forms.ModelForm):
    class Meta:
        model = Court
        fields = ['name', 'sport', 'surface', 'has_lighting', 'base_price_per_hour', 'lighting_extra_per_hour']

        labels = {
            'name': 'Nombre',
            'sport': 'Deporte',
            'surface': 'Superficie',
            'has_lighting': '¿Tiene iluminación?',
            'base_price_per_hour': 'Precio base/hora (€)',
            'lighting_extra_per_hour': 'Extra luz/hora (€)',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sport': forms.Select(attrs={'class': 'form-control'}),
            'surface': forms.Select(attrs={'class': 'form-control'}),
            'has_lighting': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'base_price_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lighting_extra_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }