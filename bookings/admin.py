from django.contrib import admin
from django.utils.html import format_html
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Configuración avanzada del admin para Bookings.
    
    Incluye visualización personalizada, filtros y métodos personalizados
    para hacer que la gestión de reservas sea más eficiente.
    """
    
    # Campos que se muestran en la lista
    list_display = [
        'id',
        'court',
        'user',
        'start',
        'end',
        'duration_display',
        'status_badge',
        'total_price',
        'lighting',
        'created_at'
    ]
    
    # Filtros laterales
    list_filter = [
        'status',
        'lighting',
        'created_at',
        'start',
        'court__sport',  # Podemos filtrar por el deporte de la cancha
        'court__complex',  # O por el complejo
    ]
    
    # Campos por los que se puede buscar
    search_fields = [
        'user__username',
        'user__email',
        'court__name',
        'court__complex__name'
    ]
    
    # Campos de solo lectura (no se pueden editar en el admin)
    # created_at y updated_at son automáticos, no tiene sentido editarlos
    readonly_fields = ['created_at', 'updated_at']
    
    # Campos que se agrupan en el formulario de edición
    fieldsets = (
        ('Información de la reserva', {
            'fields': ('user', 'court', 'status')
        }),
        ('Horario', {
            'fields': ('start', 'end')
        }),
        ('Detalles de precio', {
            'fields': ('total_price', 'lighting')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Este fieldset aparece colapsado por defecto
        }),
    )

    add_fieldsets = (
        ('Información de la reserva', {
            'fields': ('user', 'court', 'status')
        }),
        ('Horario', {
            'fields': ('start', 'end')
        }),
        ('Detalles de precio', {
            'fields': ('total_price', 'lighting')
        })
    )
    
    def duration_display(self, obj):
        """
        Muestra la duración de la reserva de forma legible.
        
        Args:
            obj: La instancia de Booking
            
        Returns:
            str: Duración en formato "X minutos"
        """
        return f"{obj.get_duration_minutes()} minutos"
    
    # Etiqueta que aparecerá en la columna
    duration_display.short_description = 'Duración'
    
    def status_badge(self, obj):
        """
        Muestra el estado con un badge de color.
        
        Esto hace que sea más fácil visualmente identificar
        el estado de cada reserva en la lista.
        
        Args:
            obj: La instancia de Booking
            
        Returns:
            str: HTML con el badge coloreado
        """
        # Definimos colores según el estado
        # Estos son colores CSS estándar
        colors = {
            'pending_payment': '#FFA500',  # Naranja
            'confirmed': '#28A745',        # Verde
            'in_progress': '#007BFF',      # Azul
            'finished': '#6C757D',         # Gris
            'cancelled': '#DC3545',        # Rojo
        }
        
        color = colors.get(obj.status, '#6C757D')
        
        # format_html es importante para prevenir XSS
        # Nunca uses f-strings directamente con HTML en Django admin
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    # Etiqueta para la columna
    status_badge.short_description = 'Estado'
    
    def get_queryset(self, request):
        """
        Personaliza el queryset base.
        
        Aquí aplicamos optimizaciones y filtrado por permisos.
        """
        qs = super().get_queryset(request)
        
        # Optimización: hacemos select_related para evitar N+1 queries
        # Esto le dice a Django que traiga los objetos relacionados
        # en la misma query SQL en lugar de hacer queries adicionales
        qs = qs.select_related('user', 'court', 'court__complex')
        
        # Si no eres superusuario, solo ves reservas de tus propios complejos
        # Este es el patrón de "aislamiento por propietario" que menciona el documento
        if not request.user.is_superuser:
            qs = qs.filter(court__complex__owner=request.user)
        
        return qs
