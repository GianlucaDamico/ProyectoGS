from django.db import models
from django.conf import settings

# Definimos los tipos de deportes como choices
# Esto es similar a un enum en otros lenguajes
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
        # Esto define cómo se mostrará en plural en el admin
        verbose_name_plural = "Amenities"
    
    def __str__(self):
        # Este método define cómo se representa el objeto como string
        # Muy útil en el admin y en el shell de Django
        return self.name
    

class Complex(models.Model):
    """
    Representa un complejo deportivo completo.
    Un complejo pertenece a un propietario (owner) y puede tener
    múltiples canchas (courts) y servicios (amenities).
    """
    # ForeignKey crea una relación muchos-a-uno
    # Muchos complejos pueden pertenecer a un mismo owner
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Referencia al modelo de usuario
        on_delete=models.CASCADE,   # Si se borra el usuario, se borran sus complejos
        related_name="owned_complexes"  # Permite hacer user.owned_complexes.all()
    )

    # Datos legales/comerciales del complejo
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
    
    
    # ManyToManyField crea una relación muchos-a-muchos
    # Un complejo puede tener muchas amenities, una amenity puede estar en muchos complejos
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,  # Es opcional, un complejo puede no tener amenities
        related_name="complexes"  # Permite hacer amenity.complexes.all()
    )
    
    class Meta:
        verbose_name_plural = "Complexes"
    
    def __str__(self):
        return f"{self.name} ({self.city})"
    
class Court(models.Model):
    """
    Representa una cancha individual dentro de un complejo.
    Cada cancha tiene sus propias características y precio base.
    """
    # Relación con el complejo al que pertenece
    complex = models.ForeignKey(
        Complex,
        on_delete=models.CASCADE,
        related_name="courts"  # Permite hacer complex.courts.all()
    )
    
    name = models.CharField(max_length=120)
    
    # Usamos los choices que definimos arriba
    sport = models.CharField(max_length=20, choices=Sport.choices)
    surface = models.CharField(max_length=30, choices=Surface.choices)
    
    has_lighting = models.BooleanField(default=False)
    
    # DecimalField es crucial para dinero
    # Nunca uses FloatField para precios por problemas de precisión
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
    
    def __str__(self):
        return f"{self.complex.name} - {self.name} ({self.get_sport_display()})"