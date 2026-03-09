from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Booking
from venues.models import Court


class BookingService:
    """
    Servicio que encapsula la lógica de negocio de las reservas.
    
    Este patrón separa la lógica de negocio de las vistas,
    haciéndola más testeable y reutilizable.
    """
    
    @staticmethod
    def calculate_price(court, start, end, lighting=False):
        """
        Calcula el precio total de una reserva.
        
        Considera:
        - Precio base de la cancha por hora
        - Duración del bloque
        - Recargo por iluminación si aplica
        
        Args:
            court: Instancia de Court
            start: datetime de inicio
            end: datetime de fin
            lighting: bool, si se usará iluminación
            
        Returns:
            Decimal: precio total calculado
        """
        # Calculamos la duración en horas (como decimal)
        duration_seconds = (end - start).total_seconds()
        duration_hours = Decimal(str(duration_seconds / 3600))
        
        # Precio base
        total = court.base_price_per_hour * duration_hours
        
        # Recargo por iluminación si aplica
        if lighting and court.has_lighting:
            total += court.lighting_extra_per_hour * duration_hours
        
        # Redondeamos a 2 decimales
        return total.quantize(Decimal('0.01'))
    
    @staticmethod
    def check_availability(court, start, end, exclude_booking_id=None):
        """
        Verifica si una cancha está disponible en un rango de tiempo.
        
        Una cancha NO está disponible si existe alguna reserva:
        - En estado PENDING_PAYMENT, CONFIRMED o IN_PROGRESS
        - Que solape con el rango de tiempo solicitado
        
        Args:
            court: Instancia de Court
            start: datetime de inicio
            end: datetime de fin
            exclude_booking_id: ID de reserva a excluir (útil para actualizaciones)
            
        Returns:
            tuple: (is_available: bool, conflicting_bookings: QuerySet)
        """
        # Estados que bloquean la disponibilidad
        blocking_statuses = [
            Booking.Status.PENDING_PAYMENT,
            Booking.Status.CONFIRMED,
            Booking.Status.IN_PROGRESS,
        ]
        
        # Buscamos reservas que solapen
        # Dos intervalos [A,B] y [C,D] se solapan si: A < D y B > C
        conflicting = Booking.objects.filter(
            court=court,
            status__in=blocking_statuses,
        ).filter(
            start__lt=end,  # La reserva existente empieza antes de que termine la nuestra
            end__gt=start,  # La reserva existente termina después de que empiece la nuestra
        )
        
        # Excluimos la reserva actual si estamos actualizando
        if exclude_booking_id:
            conflicting = conflicting.exclude(id=exclude_booking_id)
        
        is_available = not conflicting.exists()
        
        return is_available, conflicting
    
    @staticmethod
    @transaction.atomic
    def create_booking(user, court, start, end, lighting=False):
        """
        Crea una nueva reserva con toda la lógica de negocio.
        
        Este método:
        1. Verifica disponibilidad
        2. Calcula el precio automáticamente
        3. Crea la reserva en una transacción atómica
        4. Retorna la reserva creada o lanza una excepción
        
        Args:
            user: Usuario que hace la reserva
            court: Cancha a reservar
            start: Fecha/hora de inicio
            end: Fecha/hora de fin
            lighting: Si usará iluminación
            
        Returns:
            Booking: La reserva creada
            
        Raises:
            ValidationError: Si hay algún problema
        """
        # Verificamos disponibilidad
        is_available, conflicting = BookingService.check_availability(court, start, end)
        
        if not is_available:
            raise ValidationError(
                f"La cancha no está disponible en ese horario. "
                f"Hay {conflicting.count()} reserva(s) que solapan."
            )
        
        # Calculamos el precio automáticamente
        total_price = BookingService.calculate_price(court, start, end, lighting)
        
        # Creamos la reserva
        booking = Booking(
            user=user,
            court=court,
            start=start,
            end=end,
            lighting=lighting,
            total_price=total_price,
            status=Booking.Status.PENDING_PAYMENT
        )
        
        # Validamos usando el método clean del modelo
        booking.full_clean()
        
        # Guardamos
        booking.save()
        
        return booking
    
    @staticmethod
    def cancel_booking(booking):
        """
        Cancela una reserva verificando que sea válido hacerlo.
        
        Args:
            booking: Instancia de Booking a cancelar
            
        Returns:
            Booking: La reserva cancelada
            
        Raises:
            ValidationError: Si no se puede cancelar
        """
        if not booking.can_be_cancelled():
            raise ValidationError(
                "Esta reserva no puede ser cancelada. "
                "Puede que ya haya comenzado, finalizado o esté cancelada."
            )
        
        booking.status = Booking.Status.CANCELLED
        booking.save()
        
        return booking