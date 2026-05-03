from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from venues.models import Complex, Court, Amenity, Sport, Surface

User = get_user_model()

class AmenityModelTest(TestCase):
    """
    Tests para el modelo Amenity.
    """

    def test_create_amenity(self):
        """
        Test básico: crear un amenity.
        """
        amenity = Amenity.objects.create(name="Vestuarios")

        self.assertEqual(amenity.name, "Vestuarios")
        self.assertEqual(str(amenity), "Vestuarios")

    def test_amenity_unique_name(self):
        """
        Test que el nombre de amenity sea único.
        """
        Amenity.objects.create(name="Vestuarios")

        with self.assertRaises(Exception):
            Amenity.objects.create(name="Vestuarios")

class ComplexModelTest(TestCase):
    """
    Tests para el modelo Complex.
    """

    def setUp(self):
        """
        setUp se ejecuta ANTES de cada test.
        Aquí creamos datos que necesitamos en múltiples tests.
        """
        self.user = User.objects.create_user(
            username='owner1',
            password='testpass123'
        )
        self.amenity1 = Amenity.objects.create(name="Parking")
        self.amenity2 = Amenity.objects.create(name="Cafetería")

    def test_create_complex(self):
        """
        Test crear un complejo básico.
        """
        complex = Complex.objects.create(
            owner=self.user,
            name="Centro Deportivo",
            city="Madrid",
            calle="Calle Test 123"
        )

        self.assertEqual(complex.name, "Centro Deportivo")
        self.assertEqual(complex.owner, self.user)
        self.assertEqual(str(complex), "Centro Deportivo (Madrid)")

    def test_complex_with_amenities(self):
        """
        Test que un complejo puede tener múltiples amenities.
        """
        complex = Complex.objects.create(
            owner=self.user,
            name="Centro Deportivo",
            city="Madrid"
        )

        complex.amenities.add(self.amenity1, self.amenity2)

        self.assertEqual(complex.amenities.count(), 2)
        self.assertIn(self.amenity1, complex.amenities.all())
        self.assertIn(self.amenity2, complex.amenities.all())

    def test_complex_owner_relationship(self):
        """
        Test la relación inversa: un owner puede tener múltiples complejos.
        """
        complex1 = Complex.objects.create(
            owner=self.user,
            name="Complejo 1",
            city="Madrid"
        )
        complex2 = Complex.objects.create(
            owner=self.user,
            name="Complejo 2",
            city="Barcelona"
        )

        user_complexes = self.user.owned_complexes.all()

        self.assertEqual(user_complexes.count(), 2)
        self.assertIn(complex1, user_complexes)
        self.assertIn(complex2, user_complexes)

class CourtModelTest(TestCase):
    """
    Tests para el modelo Court.
    """

    def setUp(self):
        """
        Datos comunes para los tests de Court.
        """
        self.user = User.objects.create_user(
            username='owner1',
            password='testpass123'
        )
        self.complex = Complex.objects.create(
            owner=self.user,
            name="Centro Deportivo",
            city="Madrid"
        )

    def test_create_court(self):
        """
        Test crear una cancha básica.
        """
        court = Court.objects.create(
            complex=self.complex,
            name="Cancha 1",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            has_lighting=True,
            base_price_per_hour=25.00,
            lighting_extra_per_hour=5.00
        )

        self.assertEqual(court.name, "Cancha 1")
        self.assertEqual(court.sport, Sport.PADEL)
        self.assertEqual(court.complex, self.complex)
        self.assertTrue(court.has_lighting)

    def test_court_display_methods(self):
        """
        Test que los métodos get_X_display() funcionan correctamente.
        """
        court = Court.objects.create(
            complex=self.complex,
            name="Cancha 1",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            base_price_per_hour=25.00
        )

        self.assertEqual(court.get_sport_display(), "Pádel")
        self.assertEqual(court.get_surface_display(), "Césped sintético")

    def test_court_str_representation(self):
        """
        Test la representación en string de Court.
        """
        court = Court.objects.create(
            complex=self.complex,
            name="Cancha Principal",
            sport=Sport.FUTBOL_SALA,
            surface=Surface.PARQUET,
            base_price_per_hour=30.00
        )

        expected = f"{self.complex.name} - Cancha Principal (Fútbol sala)"
        self.assertEqual(str(court), expected)

    def test_complex_courts_relationship(self):
        """
        Test la relación inversa: un complejo puede tener múltiples canchas.
        """
        court1 = Court.objects.create(
            complex=self.complex,
            name="Cancha 1",
            sport=Sport.PADEL,
            surface=Surface.CESPED_SINTETICO,
            base_price_per_hour=25.00
        )
        court2 = Court.objects.create(
            complex=self.complex,
            name="Cancha 2",
            sport=Sport.TENIS,
            surface=Surface.CEMENTO,
            base_price_per_hour=20.00
        )

        complex_courts = self.complex.courts.all()

        self.assertEqual(complex_courts.count(), 2)
        self.assertIn(court1, complex_courts)
        self.assertIn(court2, complex_courts)