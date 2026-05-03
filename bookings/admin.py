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

    list_filter = [
        'status',
        'lighting',
        'created_at',
        'start',
        'court__sport',
        'court__complex',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'court__name',
        'court__complex__name'
    ]

    readonly_fields = ['created_at', 'updated_at']

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
            'classes': ('collapse',)
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

        colors = {
            'pending_payment': '#FFA500',
            'confirmed': '#28A745',
            'in_progress': '#007BFF',
            'finished': '#6C757D',
            'cancelled': '#DC3545',
        }

        color = colors.get(obj.status, '#6C757D')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Estado'

    def get_queryset(self, request):
        """
        Personaliza el queryset base.
        
        Aquí aplicamos optimizaciones y filtrado por permisos.
        """
        qs = super().get_queryset(request)

        qs = qs.select_related('user', 'court', 'court__complex')

        if not request.user.is_superuser:
            qs = qs.filter(court__complex__owner=request.user)

        return qs
