from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

class Sport(models.TextChoices):
    """
    Tipos de deportes disponibles en la plataforma.
    TextChoices nos da dos valores: el valor en BD (ej: 'futsal')
    y el label legible (ej: 'Fútbol sala')
    """
    FUTBOL_SALA = "futsal", "Fútbol sala"
    FUTBOL_7 = "futbol7", "Fútbol 7"
    FUTBOL_11 = "futbol11", "Fútbol 11"
    PADEL = "padel", "Pádel"
    TENIS = "tenis", "Tenis"
    WATERPOLO = "waterpolo", "Waterpolo"
    PELOTA_VASCA = "pelota", "Pelota vasca"
    PISCINA = "piscina", "Piscina"
    TIRO_CON_ARCO = "arco", "Tiro con arco"
    BALONCESTO = "baloncesto", "Baloncesto"
    VOLEIBOL = "voleibol", "Voleibol"

class Surface(models.TextChoices):
    """
    Tipos de superficie para las canchas.
    """
    CESPED_SINTETICO = "cesped_sintetico", "Césped sintético"
    CESPED_NATURAL = "cesped_natural", "Césped natural"
    CEMENTO = "cemento", "Cemento"
    PARQUET = "parquet", "Parquet"

class Amenity(models.Model):
    """
    Servicios adicionales que puede ofrecer un complejo.
    Ejemplos: vestuarios, parking, zona de parrillas, cafetería, etc..
    """
    name = models.CharField(max_length=80, unique=True)

    class Meta:

        verbose_name_plural = "Amenities"

    def __str__(self):

        return self.name

class Complex(models.Model):
    """
    Representa un complejo deportivo completo.
    Un complejo pertenece a un propietario (owner) y puede tener
    múltiples canchas (courts) y servicios (amenities).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_complexes"
    )

    nombre_legal = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200, blank=True)
    id_fiscal = models.CharField(max_length=50, blank=True)
    categoria_fiscal = models.CharField(max_length=50, blank=True)
    calle = models.CharField(max_length=200, blank=True)
    altura = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    barrio = models.CharField(max_length=100, blank=True)
    telefono_comercial = models.CharField(max_length=20, blank=True)
    email_comercial = models.EmailField(blank=True)
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(max_length=200, blank=True, unique=True, null = True)
    imagen = models.ImageField(
        upload_to='complejos/',
        default='complejos/default_complejo.png',
        null=True,
        blank=True
    )

    @property
    def address(self):
        return ' '.join(part for part in [self.calle, self.altura] if part)

    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name="complexes"
    )

    class Meta:
        verbose_name_plural = "Complexes"

    def __str__(self):
        return f"{self.name} ({self.city})"

    def save(self, *args, **kwargs):
        "Genera el slsug automatico si no existe"
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('core:complejo_detalle', kwargs={'complejo_id': self.id, 'slug': self.slug})

class Court(models.Model):
    """
    Representa una cancha individual dentro de un complejo.
    Cada cancha tiene sus propias características y precio base.
    """

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="courts"
    )

    name = models.CharField(max_length=120)

    sport = models.CharField(max_length=20, choices=Sport.choices)
    surface = models.CharField(max_length=30, choices=Surface.choices)

    has_lighting = models.BooleanField(default=False)

    base_price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    lighting_extra_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    imagen = models.ImageField(
        upload_to='courts/',
        default='courts/default_court.png',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.complex.name} - {self.name} ({self.get_sport_display()})"

class Review(models.Model):
    """
    Representa una reseña/valoración de un complejo deportivo.
    Los usuarios pueden dejar una reseña después de completar una reserva.
    """

    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review',
        help_text="Reserva asociada a esta reseña"
    )

    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text="Complejo que está siendo reseñado"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text="Usuario que escribió la reseña"
    )

    rating = models.IntegerField(
        choices=[(i, f"{i} Estrellas") for i in range(1, 6)],
        help_text="Calificación de 1 a 5 estrellas"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Comentario detallado sobre la experiencia"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación de la reseña"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"

    def __str__(self):
        return f"Reseña de {self.user.first_name} para {self.complex.name} - {self.rating}★"