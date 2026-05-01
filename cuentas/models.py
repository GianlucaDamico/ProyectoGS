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
	avatar = models.ImageField(
        upload_to='usuarios/avatars/', 
        default='usuarios/avatars/default_avatar.png',
        null=True, 
        blank=True
    )

	def __str__(self):
		return f"{self.nombre} {self.apellido} ({self.user.username})"


class Propietario(models.Model):
	"""Perfil de propietario (complejo deportivo) asociado a un usuario.

	Este modelo guarda los datos personales del responsable. Los datos
	legales/comerciales del complejo se guardan en venues.Complex.
	"""

	user = models.OneToOneField(
		User,
		on_delete=models.CASCADE,
		related_name='perfil_propietario',
	)
	complex = models.OneToOneField(
		'venues.Complex',
		on_delete=models.CASCADE,
		related_name='propietario',
		null=True,
		blank=True,
	)

	# Paso 1 - responsable (nombre/apellido quedan en auth_user)
	dni_nie = models.CharField(max_length=20)
	cargo = models.CharField(max_length=100)
	telefono_responsable = models.CharField(max_length=20)
	fecha_nacimiento = models.DateField()

	def __str__(self):
		if self.complex:
			return f"{self.complex.nombre_complejo} ({self.user.username})"
		return self.user.username


# Create your models here.
