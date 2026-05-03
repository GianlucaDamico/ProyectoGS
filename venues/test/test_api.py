from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from venues.models import Complex, Court, Amenity, Sport, Surface

User = get_user_model()

class PublicComplexAPITest(APITestCase):
    """
    Tests para endpoints públicos de Complex (sin autenticación).
    
    Estos endpoints son de solo lectura y accesibles para todos.
    """

    def setUp(self):
        """
        Crea datos de prueba.
        """
        self.owner = User.objects.create_user(
            username='owner1',
            password='testpass123'
        )

        self.amenity1 = Amenity.objects.create(name="Parking")
        self.amenity2 = Amenity.objects.create(name="Vestuarios")

        self.complex1 = Complex.objects.create(
            owner=self.owner,
            name="Centro Deportivo Madrid",
            city="Madrid",
        )
        self.complex1.amenities.add(self.amenity1, self.amenity2)

        self.complex2 = Complex.objects.create(
            owner=self.owner,
            name="Polideportivo Barcelona",
            city="Barcelona",
        )

        self.court1 = Court.objects.create(
            complex=self.complex1,
            name="Cancha 1",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            has_lighting=True,
            base_price_per_hour=Decimal("30.00")
        )

    def test_list_complexes_public(self):
        """
        Test: cualquiera puede listar complejos sin autenticarse.
        """
        url = '/api/complexes/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_complex_public(self):
        """
        Test: cualquiera puede ver detalles de un complejo.
        """
        url = f'/api/complexes/{self.complex1.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['name'], "Centro Deportivo Madrid")
        self.assertEqual(response.data['city'], "Madrid")

        self.assertEqual(len(response.data['amenities']), 2)

        self.assertEqual(len(response.data['courts']), 1)

    def test_filter_complexes_by_city(self):
        """
        Test: filtrar complejos por ciudad.
        """
        url = '/api/complexes/?city=Madrid'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['city'], "Madrid")

    def test_search_complexes(self):
        """
        Test: búsqueda por nombre.
        """
        url = '/api/complexes/?search=Barcelona'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn("Barcelona", response.data['results'][0]['name'])

    def test_cannot_create_complex_without_auth(self):
        """
        Test: NO se puede crear complejo sin autenticación.
        """
        url = '/api/complexes/'
        data = {
            'name': 'Nuevo Complejo',
            'city': 'Valencia'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class PublicCourtAPITest(APITestCase):
    """
    Tests para endpoints públicos de Court.
    """

    def setUp(self):
        """
        Crea canchas de prueba.
        """
        self.owner = User.objects.create_user(username='owner1', password='test')

        self.complex = Complex.objects.create(
            owner=self.owner,
            name="Centro Deportivo",
            city="Madrid"
        )

        self.court_padel = Court.objects.create(
            complex=self.complex,
            name="Pádel 1",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            has_lighting=True,
            base_price_per_hour=Decimal("30.00")
        )

        self.court_tennis = Court.objects.create(
            complex=self.complex,
            name="Tenis 1",
            sport=Sport.TENIS,
            surface=Surface.CEMENTO,
            has_lighting=False,
            base_price_per_hour=Decimal("25.00")
        )

    def test_list_courts(self):
        """
        Test: listar todas las canchas.
        """
        url = '/api/courts/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_courts_by_sport(self):
        """
        Test: filtrar canchas por deporte.
        """
        url = '/api/courts/?sport=padel'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['sport'], 'padel')

    def test_filter_courts_with_lighting(self):
        """
        Test: filtrar canchas que tienen iluminación.
        """
        url = '/api/courts/?has_lighting=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['has_lighting'])

    def test_order_courts_by_price(self):
        """
        Test: ordenar canchas por precio.
        """
        url = '/api/courts/?ordering=base_price_per_hour'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prices = [Decimal(c['base_price_per_hour']) for c in response.data['results']]
        self.assertEqual(prices, sorted(prices))

    def test_search_courts_by_name(self):
        """
        Test: buscar canchas por nombre.
        """
        url = '/api/courts/?search=Pádel'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class CourtAvailabilityAPITest(APITestCase):
    """
    Tests para el endpoint de verificación de disponibilidad.
    """

    def setUp(self):
        """
        Crea datos de prueba.
        """
        from django.utils import timezone
        from datetime import timedelta
        from bookings.models import Booking

        self.user = User.objects.create_user(username='player1', password='test')
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

        tomorrow = timezone.now() + timedelta(days=1)
        start = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)

        self.existing_booking = Booking.objects.create(
            user=self.user,
            court=self.court,
            start=start,
            end=start + timedelta(minutes=90),
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("45.00")
        )

    def test_check_availability_free_slot(self):
        """
        Test: verificar disponibilidad en horario libre.
        """
        from django.utils import timezone
        from datetime import timedelta

        tomorrow = timezone.now() + timedelta(days=1)
        start = tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=90)

        url = f'/api/courts/{self.court.id}/check_availability/'
        params = {
            'start': start.isoformat(),
            'end': end.isoformat(),
            'lighting': 'false'
        }

        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
        self.assertEqual(response.data['estimated_price'], '45.00')

    def test_check_availability_occupied_slot(self):
        """
        Test: verificar disponibilidad en horario ocupado.
        """

        start = self.existing_booking.start
        end = self.existing_booking.end

        url = f'/api/courts/{self.court.id}/check_availability/'
        params = {
            'start': start.isoformat(),
            'end': end.isoformat()
        }

        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['available'])
        self.assertIn('conflicting_bookings', response.data)

class ComplexStatsAPITest(APITestCase):
    """
    Tests para el endpoint de estadísticas del complejo.
    """

    def setUp(self):
        """
        Crea propietario con complejo.
        """
        from django.utils import timezone
        from datetime import timedelta
        from bookings.models import Booking

        self.owner = User.objects.create_user(username='owner1', password='test')
        self.player = User.objects.create_user(username='player1', password='test')

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
            base_price_per_hour=Decimal("30.00")
        )

        for i in range(3):
            start = timezone.now() + timedelta(days=i)
            Booking.objects.create(
                user=self.player,
                court=self.court,
                start=start,
                end=start + timedelta(minutes=90),
                status=Booking.Status.CONFIRMED,
                total_price=Decimal("45.00")
            )

    def test_owner_can_access_own_complex_stats(self):
        """
        Test: propietario puede ver estadísticas de SU complejo.
        """
        self.client.force_authenticate(user=self.owner)

        url = f'/api/complexes/{self.complex.id}/stats/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('total_bookings', response.data)
        self.assertIn('confirmed_bookings', response.data)
        self.assertIn('total_revenue', response.data)
        self.assertEqual(response.data['total_bookings'], 3)

    def test_other_user_cannot_access_complex_stats(self):
        """
        Test CRÍTICO: otro usuario NO puede ver estadísticas del complejo.
        """
        other_user = User.objects.create_user(username='other', password='test')
        self.client.force_authenticate(user=other_user)

        url = f'/api/complexes/{self.complex.id}/stats/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)