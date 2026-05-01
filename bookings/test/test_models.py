from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from bookings.models import Booking
from venues.models import Complex, Court, Sport, Surface

User = get_user_model()


class BookingModelTest(TestCase):
    """
    Tests para el modelo Booking.
    """
    
    def setUp(self):
        """
        Crea datos necesarios para los tests de reservas.
        """
        # Usuarios
        self.player = User.objects.create_user(
            username='player1',
            password='testpass123'
        )
        self.owner = User.objects.create_user(
            username='owner1',
            password='testpass123'
        )
        
        # Complejo y cancha
        self.complex = Complex.objects.create(
            owner=self.owner,
            name="Centro Deportivo",
            city="Madrid"
        )
        self.court = Court.objects.create(
            complex=self.complex,
            name="Cancha 1",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            has_lighting=True,
            base_price_per_hour=Decimal("30.00"),
            lighting_extra_per_hour=Decimal("5.00")
        )
        
        # Fecha/hora de referencia (mañana a las 18:00)
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.start_time = self.tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
        self.end_time_90min = self.start_time + timedelta(minutes=90)
    
    def test_create_booking_basic(self):
        """
        Test crear una reserva básica.
        """
        booking = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.end_time_90min,
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("45.00"),
            lighting=False
        )
        
        self.assertEqual(booking.user, self.player)
        self.assertEqual(booking.court, self.court)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.get_duration_minutes(), 90)
    
    def test_booking_duration_calculation(self):
        """
        Test que el método get_duration_minutes() calcula correctamente.
        """
        # 60 minutos
        booking_60 = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.start_time + timedelta(minutes=60),
            total_price=Decimal("30.00")
        )
        self.assertEqual(booking_60.get_duration_minutes(), 60)
        
        # 90 minutos
        booking_90 = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.start_time + timedelta(minutes=90),
            total_price=Decimal("45.00")
        )
        self.assertEqual(booking_90.get_duration_minutes(), 90)
        
        # 120 minutos
        booking_120 = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.start_time + timedelta(minutes=120),
            total_price=Decimal("60.00")
        )
        self.assertEqual(booking_120.get_duration_minutes(), 120)
    
    def test_booking_is_past(self):
        """
        Test el método is_past().
        """
        # Reserva en el pasado
        past_start = timezone.now() - timedelta(days=2)
        past_end = past_start + timedelta(hours=1)
        past_booking = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=past_start,
            end=past_end,
            total_price=Decimal("30.00")
        )
        self.assertTrue(past_booking.is_past())
        
        # Reserva en el futuro
        future_booking = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.end_time_90min,
            total_price=Decimal("45.00")
        )
        self.assertFalse(future_booking.is_past())
    
    def test_booking_is_active(self):
        """
        Test el método is_active() - reserva en curso.
        """
        # Reserva que está ocurriendo ahora
        now = timezone.now()
        active_start = now - timedelta(minutes=30)
        active_end = now + timedelta(minutes=30)
        
        active_booking = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=active_start,
            end=active_end,
            total_price=Decimal("30.00")
        )
        self.assertTrue(active_booking.is_active())
    
    def test_booking_can_be_cancelled(self):
        """
        Test el método can_be_cancelled() con diferentes estados.
        """
        # Confirmada - SÍ se puede cancelar
        confirmed_booking = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.end_time_90min,
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("45.00")
        )
        self.assertTrue(confirmed_booking.can_be_cancelled())
        
        # Finalizada - NO se puede cancelar
        finished_booking = Booking.objects.create(
            user=self.player,
            court=self.court,
            start=self.start_time,
            end=self.end_time_90min,
            status=Booking.Status.FINISHED,
            total_price=Decimal("45.00")
        )
        self.assertFalse(finished_booking.can_be_cancelled())