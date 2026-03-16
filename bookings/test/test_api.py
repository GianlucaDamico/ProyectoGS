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