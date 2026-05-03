from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from bookings.models import Booking
from venues.models import Complex, Court, Sport, Surface

User = get_user_model()

class BookingValidationTest(TestCase):
    """
    Tests para las validaciones del modelo Booking.
    """

    def setUp(self):
        """
        Datos para tests de validación.
        """
        self.player = User.objects.create_user(username='player1', password='test')
        self.owner = User.objects.create_user(username='owner1', password='test')

        self.complex = Complex.objects.create(
            owner=self.owner,
            name="Centro Deportivo",
            city="Madrid"
        )

        self.court_with_light = Court.objects.create(
            complex=self.complex,
            name="Cancha con luz",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            has_lighting=True,
            base_price_per_hour=Decimal("30.00")
        )

        self.court_without_light = Court.objects.create(
            complex=self.complex,
            name="Cancha sin luz",
            sport=Sport.FUTBOL_SALA,
            surface=Surface.PARQUET,
            has_lighting=False,
            base_price_per_hour=Decimal("25.00")
        )

        self.tomorrow = timezone.now() + timedelta(days=1)
        self.start_time = self.tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)

    def test_validation_end_before_start(self):
        """
        Test que falla si end <= start.
        """
        booking = Booking(
            user=self.player,
            court=self.court_with_light,
            start=self.start_time,
            end=self.start_time - timedelta(minutes=30),
            total_price=Decimal("30.00")
        )

        with self.assertRaises(ValidationError) as context:
            booking.clean()

        self.assertIn('end', context.exception.message_dict)

    def test_validation_invalid_duration(self):
        """
        Test que falla si la duración no es 60, 90 o 120 minutos.
        """

        booking_45 = Booking(
            user=self.player,
            court=self.court_with_light,
            start=self.start_time,
            end=self.start_time + timedelta(minutes=45),
            total_price=Decimal("30.00")
        )

        with self.assertRaises(ValidationError) as context:
            booking_45.clean()

        self.assertIn('60, 90 o 120 minutos', str(context.exception))

    def test_validation_valid_durations(self):
        """
        Test que PASA validación con duraciones válidas.
        """
        for minutes in [60, 90, 120]:
            booking = Booking(
                user=self.player,
                court=self.court_with_light,
                start=self.start_time,
                end=self.start_time + timedelta(minutes=minutes),
                total_price=Decimal("30.00")
            )
            try:
                booking.clean()
            except ValidationError:
                self.fail(f"{minutes} minutos debería ser válido")

    def test_validation_lighting_without_availability(self):
        """
        Test que falla si pide iluminación pero la cancha no la tiene.
        """
        booking = Booking(
            user=self.player,
            court=self.court_without_light,
            start=self.start_time,
            end=self.start_time + timedelta(minutes=90),
            lighting=True,
            total_price=Decimal("45.00")
        )

        with self.assertRaises(ValidationError) as context:
            booking.clean()

        self.assertIn('lighting', context.exception.message_dict)
        self.assertIn('no tiene iluminación', str(context.exception))