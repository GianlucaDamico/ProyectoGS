from django.contrib import admin
from .models import Amenity, Complex, Court, Review


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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Reviews (Reseñas).
    """
    list_display = ['get_user_name', 'complex', 'rating', 'created_at']
    list_filter = ['rating', 'complex', 'created_at']
    search_fields = ['user__first_name', 'user__username', 'complex__name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Información de la Reseña', {
            'fields': ('booking', 'complex', 'user', 'rating', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_name(self, obj):
        """Mostrar el nombre del usuario en lugar del ID"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    get_user_name.short_description = 'Usuario'
    
    def get_queryset(self, request):
        """
        Los superusuarios ven todo, los propietarios solo ven reseñas de sus complejos.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Mostrar solo reseñas de complejos que posee
        return qs.filter(complex__owner=request.user)