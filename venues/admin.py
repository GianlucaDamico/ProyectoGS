from django.contrib import admin
from .models import Amenity, Complex, Court


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Amenities.
    """
    list_display = ['name']  # Columnas que se muestran en la lista
    search_fields = ['name']  # Permite buscar por nombre


@admin.register(Complex)
class ComplexAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Complexes.
    """
    list_display = ['name', 'city', 'owner']
    list_filter = ['city']  # Filtros laterales
    search_fields = ['name', 'city']
    filter_horizontal = ['amenities']  # Widget mejor para ManyToMany
    
    def get_queryset(self, request):
        """
        Los superusuarios ven todo, los usuarios normales solo ven sus complejos.
        Este es un preview de cómo haremos el aislamiento por propietario.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Courts.
    """
    list_display = ['name', 'complex', 'sport', 'surface', 'has_lighting', 'base_price_per_hour']
    list_filter = ['sport', 'surface', 'has_lighting']
    search_fields = ['name', 'complex__name']