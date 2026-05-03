from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status

from bookings.models import Booking
from venues.models import Complex, Court, Sport, Surface

User = get_user_model()


class BookingAPIAuthenticationTest(APITestCase):
    """
    Tests para verificar que se requiere autenticación.
    """
    
    def test_list_bookings_requires_auth(self):
        """
        Test: NO se puede listar reservas sin autenticación.
        """
        url = '/api/bookings/'
        response = self.client.get(url)
        
        # Debe requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_booking_requires_auth(self):
        """
        Test: NO se puede crear reserva sin autenticación.
        """
        url = '/api/bookings/'
        data = {'court': 1, 'start': '2024-12-31T18:00:00Z', 'end': '2024-12-31T19:30:00Z'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BookingAPINormalUserTest(APITestCase):
    """
    Tests para usuario NORMAL (jugador).
    
    Un usuario normal:
    - Solo ve SUS propias reservas
    - NO ve reservas de otros usuarios
    - Puede crear reservas para sí mismo
    - Puede cancelar sus propias reservas
    - NO puede modificar reservas de otros
    """
    
    def setUp(self):
        """
        Crea usuarios y datos de prueba.
        """
        # Usuario 1 (el que va a hacer las peticiones)
        self.user1 = User.objects.create_user(
            username='player1',
            password='testpass123'
        )
        
        # Usuario 2 (otro jugador)
        self.user2 = User.objects.create_user(
            username='player2',
            password='testpass123'
        )
        
        # Propietario y complejo
        self.owner = User.objects.create_user(
            username='owner1',
            password='testpass123'
        )
        
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
        
        # Fecha de referencia
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.start = self.tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
        self.end = self.start + timedelta(minutes=90)
        
        # Reserva del usuario 1
        self.booking_user1 = Booking.objects.create(
            user=self.user1,
            court=self.court,
            start=self.start,
            end=self.end,
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("45.00")
        )
        
        # Reserva del usuario 2
        self.booking_user2 = Booking.objects.create(
            user=self.user2,
            court=self.court,
            start=self.start + timedelta(hours=2),
            end=self.end + timedelta(hours=2),
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("45.00")
        )
        
        # IMPORTANTE: Autenticamos como user1
        self.client.force_authenticate(user=self.user1)
    
    def test_list_bookings_only_own(self):
        """
        Test: usuario normal solo ve SUS propias reservas.
        """
        url = '/api/bookings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Solo debe ver 1 reserva (la suya)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.booking_user1.id)
        
        # NO debe ver la reserva del user2
        booking_ids = [b['id'] for b in response.data['results']]
        self.assertNotIn(self.booking_user2.id, booking_ids)
    
    def test_retrieve_own_booking(self):
        """
        Test: puede ver detalles de SU propia reserva.
        """
        url = f'/api/bookings/{self.booking_user1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.booking_user1.id)
    
    def test_cannot_retrieve_other_user_booking(self):
        """
        Test CRÍTICO: NO puede ver reserva de otro usuario.
        """
        url = f'/api/bookings/{self.booking_user2.id}/'
        response = self.client.get(url)
        
        # Debe devolver 404 (como si no existiera)
        # porque el queryset está filtrado por usuario
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_booking_success(self):
        """
        Test: puede crear reserva para sí mismo.
        """
        url = '/api/bookings/'
        
        # Nueva reserva (diferente horario)
        new_start = self.start + timedelta(days=1)
        new_end = new_start + timedelta(minutes=60)
        
        data = {
            'court': self.court.id,
            'start': new_start.isoformat(),
            'end': new_end.isoformat(),
            'lighting': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # El usuario debe ser asignado automáticamente
        self.assertEqual(response.data['user'], self.user1.id)
        
        # El precio debe calcularse automáticamente
        # 60 min = 1h * 30.00 = 30.00
        self.assertEqual(Decimal(response.data['total_price']), Decimal("30.00"))
    
    def test_create_booking_with_lighting(self):
        """
        Test: crear reserva con iluminación calcula precio correcto.
        """
        url = '/api/bookings/'
        
        new_start = self.start + timedelta(days=1)
        new_end = new_start + timedelta(minutes=90)
        
        data = {
            'court': self.court.id,
            'start': new_start.isoformat(),
            'end': new_end.isoformat(),
            'lighting': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 90 min = 1.5h * (30 + 5) = 52.50
        self.assertEqual(Decimal(response.data['total_price']), Decimal("52.50"))
        self.assertTrue(response.data['lighting'])
    
    def test_cannot_create_overlapping_booking(self):
        """
        Test: NO puede crear reserva que solapa con otra existente.
        """
        url = '/api/bookings/'
        
        # Intenta crear en horario que solapa con booking_user1
        data = {
            'court': self.court.id,
            'start': (self.start + timedelta(minutes=30)).isoformat(),
            'end': (self.end + timedelta(minutes=30)).isoformat(),
            'lighting': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Debe fallar
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no está disponible', str(response.data))
    
    def test_cancel_own_booking(self):
        """
        Test: puede cancelar SU propia reserva.
        """
        url = f'/api/bookings/{self.booking_user1.id}/cancel/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el estado cambió
        self.booking_user1.refresh_from_db()
        self.assertEqual(self.booking_user1.status, Booking.Status.CANCELLED)
    
    def test_cannot_cancel_other_user_booking(self):
        """
        Test CRÍTICO: NO puede cancelar reserva de otro usuario.
        """
        url = f'/api/bookings/{self.booking_user2.id}/cancel/'
        response = self.client.post(url)
        
        # Debe devolver 404 porque no tiene acceso
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_my_bookings_endpoint(self):
        """
        Test: endpoint /api/bookings/my_bookings/ funciona.
        """
        url = '/api/bookings/my_bookings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_disponibilidad_includes_other_users_reservations(self):
        """
        Test: la disponibilidad debe reflejar reservas de todos los usuarios.
        """
        fecha = self.start.date().isoformat()
        url = f'/api/bookings/disponibilidad/?court_id={self.court.id}&fecha={fecha}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ocupados', response.data)

        # Debe incluir la reserva propia a las 18:00 y la reserva del otro usuario a las 20:00
        self.assertIn('18:00', response.data['ocupados'])
        self.assertIn('20:00', response.data['ocupados'])
    
    def test_my_bookings_future_filter(self):
        """
        Test: filtrar solo reservas futuras.
        """
        # Crear una reserva en el pasado
        past_start = timezone.now() - timedelta(days=2)
        past_end = past_start + timedelta(minutes=90)
        
        Booking.objects.create(
            user=self.user1,
            court=self.court,
            start=past_start,
            end=past_end,
            status=Booking.Status.FINISHED,
            total_price=Decimal("45.00")
        )
        
        url = '/api/bookings/my_bookings/?future=true'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Solo debe devolver la reserva futura
        self.assertEqual(len(response.data['results']), 1)