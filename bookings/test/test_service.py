from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from bookings.models import Booking
from bookings.services import BookingService
from venues.models import Complex, Court, Sport, Surface

User = get_user_model()

class BookingServiceCreateTest(TestCase):
    """
    Tests para BookingService.create_booking()
    """
    
    def setUp(self):
        """
        Datos para tests de creación.
        """
        self.player = User.objects.create_user(username='player1', password='test')
        self.owner = User.objects.create_user(username='owner1', password='test')
        
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
        
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.start = self.tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
        self.end = self.start + timedelta(minutes=90)
    
    def test_create_booking_success(self):
        """
        Test crear una reserva exitosamente.
        """
        booking = BookingService.create_booking(
            user=self.player,
            court=self.court,
            start=self.start,
            end=self.end,
            lighting=False
        )
        
        self.assertIsNotNone(booking.id)
        self.assertEqual(booking.user, self.player)
        self.assertEqual(booking.status, Booking.Status.PENDING_PAYMENT)
        # Precio calculado automáticamente
        self.assertEqual(booking.total_price, Decimal("45.00"))
    
    def test_create_booking_with_lighting(self):
        """
        Test que el precio incluye recargo por iluminación.
        """
        booking = BookingService.create_booking(
            user=self.player,
            court=self.court,
            start=self.start,
            end=self.end,
            lighting=True
        )
        
        # 1.5h * (30 + 5) = 52.50
        self.assertEqual(booking.total_price, Decimal("52.50"))
        self.assertTrue(booking.lighting)
    
    def test_create_booking_fails_when_overlapping(self):
        """
        Test que falla al intentar crear reserva solapada.
        """
        # Primera reserva
        BookingService.create_booking(
            user=self.player,
            court=self.court,
            start=self.start,
            end=self.end,
            lighting=False
        )
        
        # Segunda reserva solapada debe fallar
        with self.assertRaises(ValidationError) as context:
            BookingService.create_booking(
                user=self.player,
                court=self.court,
                start=self.start + timedelta(minutes=30),
                end=self.end + timedelta(minutes=30),
                lighting=False
            )
        
        self.assertIn('no está disponible', str(context.exception))

    
class BookingServiceCalculatePriceTest(TestCase):
    """
    Tests para BookingService.calculate_price()
    """
    
    def setUp(self):
        """
        Crea una cancha para calcular precios.
        """
        self.owner = User.objects.create_user(username='owner1', password='test')
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
        
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.start = self.tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
    
    def test_calculate_price_60_minutes_no_lighting(self):
        """
        Test cálculo de precio para 60 minutos sin iluminación.
        """
        end = self.start + timedelta(minutes=60)
        
        price = BookingService.calculate_price(
            court=self.court,
            start=self.start,
            end=end,
            lighting=False
        )
        
        # 1 hora * 30.00 = 30.00
        expected = Decimal("30.00")
        self.assertEqual(price, expected)
    
    def test_calculate_price_90_minutes_no_lighting(self):
        """
        Test cálculo para 90 minutos sin iluminación.
        """
        end = self.start + timedelta(minutes=90)
        
        price = BookingService.calculate_price(
            court=self.court,
            start=self.start,
            end=end,
            lighting=False
        )
        
        # 1.5 horas * 30.00 = 45.00
        expected = Decimal("45.00")
        self.assertEqual(price, expected)
    
    def test_calculate_price_with_lighting(self):
        """
        Test que añade el recargo por iluminación correctamente.
        """
        end = self.start + timedelta(minutes=90)
        
        price = BookingService.calculate_price(
            court=self.court,
            start=self.start,
            end=end,
            lighting=True
        )
        
        # 1.5 horas * (30.00 + 5.00) = 52.50
        expected = Decimal("52.50")
        self.assertEqual(price, expected)
    
    def test_calculate_price_precision(self):
        """
        Test que el precio se redondea a 2 decimales.
        """
        end = self.start + timedelta(minutes=90)
        
        price = BookingService.calculate_price(
            court=self.court,
            start=self.start,
            end=end,
            lighting=True
        )
        
        # Verificamos exactamente 2 decimales
        self.assertEqual(price.as_tuple().exponent, -2)    


class BookingServiceAvailabilityTest(TestCase):
    """
    Tests para BookingService.check_availability()
    """
    
    def setUp(self):
        """
        Datos para tests de disponibilidad.
        """
        self.player1 = User.objects.create_user(username='player1', password='test')
        self.player2 = User.objects.create_user(username='player2', password='test')
        self.owner = User.objects.create_user(username='owner1', password='test')
        
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
            base_price_per_hour=Decimal("30.00")
        )
        
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.base_start = self.tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
    
    def test_availability_empty_schedule(self):
        """
        Test que una cancha sin reservas está disponible.
        """
        start = self.base_start
        end = start + timedelta(minutes=90)
        
        is_available, conflicting = BookingService.check_availability(
            court=self.court,
            start=start,
            end=end
        )
        
        self.assertTrue(is_available)
        self.assertEqual(conflicting.count(), 0)
    
    def test_availability_with_overlapping_booking(self):
        """
        Test que detecta solapamiento.
        """
        # Reserva existente: 18:00 - 19:30
        Booking.objects.create(
            user=self.player1,
            court=self.court,
            start=self.base_start,
            end=self.base_start + timedelta(minutes=90),
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("45.00")
        )
        
        # Nueva reserva: 19:00 - 20:30 (SÍ solapa)
        new_start = self.base_start + timedelta(hours=1)
        new_end = new_start + timedelta(minutes=90)
        
        is_available, conflicting = BookingService.check_availability(
            court=self.court,
            start=new_start,
            end=new_end
        )
        
        self.assertFalse(is_available)
        self.assertEqual(conflicting.count(), 1)
    
    def test_availability_ignores_cancelled_bookings(self):
        """
        Test que reservas CANCELADAS no bloquean disponibilidad.
        """
        # Reserva cancelada
        Booking.objects.create(
            user=self.player1,
            court=self.court,
            start=self.base_start,
            end=self.base_start + timedelta(minutes=90),
            status=Booking.Status.CANCELLED,
            total_price=Decimal("45.00")
        )
        
        # Intentamos reservar el mismo horario
        is_available, conflicting = BookingService.check_availability(
            court=self.court,
            start=self.base_start,
            end=self.base_start + timedelta(minutes=90)
        )
        
        self.assertTrue(is_available)