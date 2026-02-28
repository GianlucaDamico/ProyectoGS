from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Jugador(models.Model):
	"""Perfil de jugador asociado a un usuario de Django.

	El nombre de usuario, la contraseña y el email se guardan en el
	modelo principal ``User``. Este modelo contiene los campos
	específicos que el formulario de registro de jugador recoge.
	"""

	user = models.OneToOneField(
		User,
		on_delete=models.CASCADE,
		related_name='perfil_jugador',
	)
	nombre = models.CharField(max_length=100)
	apellido = models.CharField(max_length=100)
	telefono = models.CharField(max_length=20, blank=True)
	deporte_preferido = models.CharField(max_length=50, blank=True)

	def __str__(self):
		return f"{self.nombre} {self.apellido} ({self.user.username})"


class Propietario(models.Model):
	"""Perfil de propietario (complejo deportivo) asociado a un usuario.

	Este modelo agrupa todos los datos recogidos en los cuatro pasos del
	formulario de registro de propietario.
	"""

	user = models.OneToOneField(
		User,
		on_delete=models.CASCADE,
		related_name='perfil_propietario',
	)

	# Paso 1 - responsable
	nombre_responsable = models.CharField(max_length=100)
	apellido_responsable = models.CharField(max_length=100)
	dni_nie = models.CharField(max_length=20)
	cargo = models.CharField(max_length=100)
	telefono_responsable = models.CharField(max_length=20)
	fecha_nacimiento = models.DateField()

	# Paso 2 - legal y fiscal
	nombre_legal = models.CharField(max_length=200)
	nombre_complejo = models.CharField(max_length=200)
	id_fiscal = models.CharField(max_length=50)
	categoria_fiscal = models.CharField(max_length=50)

	# Paso 3 - ubicación y contacto
	calle = models.CharField(max_length=200)
	altura = models.CharField(max_length=20)
	ciudad = models.CharField(max_length=100)
	barrio = models.CharField(max_length=100)
	telefono_comercial = models.CharField(max_length=20)
	email_comercial = models.EmailField()

	def __str__(self):
		return f"{self.nombre_complejo} ({self.user.username})"


# Create your models here.
