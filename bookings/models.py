from datetime import timedelta
from django.db import models
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from venues.models import Court

class Booking(models.Model):
    """
    Representa una reserva de cancha.
    
    Una reserva tiene un ciclo de vida que pasa por diferentes estados:
    1. PENDING_PAYMENT: El usuario ha solicitado la reserva pero aún no ha pagado
    2. CONFIRMED: El pago se ha confirmado, la reserva está garantizada
    3. IN_PROGRESS: El partido está ocurriendo en este momento
    4. FINISHED: El partido terminó normalmente
    5. CANCELLED: La reserva fue cancelada (por usuario o propietario)
    """

    class Status(models.TextChoices):
        """
        Estados posibles de una reserva.
        Usamos TextChoices igual que hicimos con Sport y Surface.
        Esto nos da validación automática y representación legible.
        """
        PENDING_PAYMENT = "pending_payment", "Pendiente de pago"
        CONFIRMED = "confirmed", "Confirmada"
        IN_PROGRESS = "in_progress", "En curso"
        FINISHED = "finished", "Finalizada"
        CANCELLED = "cancelled", "Cancelada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        help_text="Usuario que realizó la reserva"
    )

    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name="bookings",
        help_text="Cancha reservada"
    )

    start = models.DateTimeField(
        help_text="Fecha y hora de inicio de la reserva"
    )

    end = models.DateTimeField(
        help_text="Fecha y hora de finalización de la reserva"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        help_text="Estado actual de la reserva"
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio total a pagar por esta reserva"
    )

    lighting = models.BooleanField(
        default=False,
        help_text="¿Se usará iluminación artificial?"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se creó la reserva"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última modificación"
    )

    class Meta:

        ordering = ['-start']

        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    def __str__(self):
        """
        Representación legible de la reserva.
        Mostrará algo como: "Cancha Central - 2024-03-15 18:00 (Confirmada)"
        """
        return f"{self.court.name} - {self.start.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"

    def clean(self):
        """
        Validaciones personalizadas a nivel de modelo.
        
        Django llama a este método cuando se valida el objeto
        (por ejemplo, en formularios o cuando se llama a full_clean()).
        
        Es importante entender que clean() NO se llama automáticamente
        en save(). Si creas objetos directamente con Booking.objects.create()
        sin pasar por formularios, estas validaciones no se ejecutarán
        a menos que llames explícitamente a full_clean() antes.
        """

        super().clean()

        if self.end <= self.start:
            raise ValidationError({
                'end': 'La hora de finalización debe ser posterior a la hora de inicio.'
            })

        duration = (self.end - self.start).total_seconds() / 60

        valid_durations = [60, 90, 120]

        if not any(abs(duration - valid) < 1 for valid in valid_durations):
            raise ValidationError({
                'end': f'La duración de la reserva debe ser de 60, 90 o 120 minutos. '
                       f'Duración actual: {int(duration)} minutos.'
            })

        if self.lighting and not self.court.has_lighting:
            raise ValidationError({
                'lighting': 'Esta cancha no tiene iluminación disponible.'
            })

    def get_duration_minutes(self):
        """
        Calcula y retorna la duración de la reserva en minutos.
        
        Este es un método de conveniencia que encapsula el cálculo
        para no tener que repetir esta lógica en otros lugares.
        """
        return int((self.end - self.start).total_seconds() / 60)

    def is_past(self):
        """
        Verifica si la reserva ya pasó.
        
        Returns:
            bool: True si la fecha de fin ya pasó, False en caso contrario
        """

        return self.end < timezone.now() + timedelta(hours=2)

    def is_active(self):
        """
        Verifica si la reserva está actualmente en curso.
        
        Returns:
            bool: True si estamos entre start y end, False en caso contrario
        """
        now = timezone.now() + timedelta(hours=2)
        return self.start <= now < self.end

    def can_be_cancelled(self):
        """
        Determina si esta reserva puede ser cancelada.
        
        Lógica de negocio: solo se pueden cancelar reservas que estén
        en estado PENDING_PAYMENT o CONFIRMED, y que aún no hayan comenzado.
        
        Returns:
            bool: True si la reserva puede cancelarse, False en caso contrario
        """

        if self.status not in [self.Status.PENDING_PAYMENT, self.Status.CONFIRMED]:
            return False

        if self.is_past() or self.is_active():
            return False

        return True