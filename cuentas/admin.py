from django.contrib import admin
from .models import Jugador, Propietario

class JugadorAdmin(admin.ModelAdmin):
	"""Admin para gestionar jugadores."""

	list_display = ('nombre', 'apellido', 'usuario', 'deporte_preferido', 'telefono')
	list_filter = ('deporte_preferido', 'user__date_joined')
	search_fields = ('nombre', 'apellido', 'user__username', 'user__email', 'telefono')
	readonly_fields = ('avatar',)

	fieldsets = (
		('Información de Usuario', {
			'fields': ('user',)
		}),
		('Datos Personales', {
			'fields': ('nombre', 'apellido', 'telefono')
		}),
		('Preferencias', {
			'fields': ('deporte_preferido', 'avatar')
		}),
	)

	def usuario(self, obj):
		"""Muestra el nombre de usuario."""
		return obj.user.username
	usuario.short_description = 'Usuario'

class PropietarioAdmin(admin.ModelAdmin):
	"""Admin para gestionar propietarios."""

	list_display = ('usuario', 'complejo', 'cargo', 'telefono_responsable', 'fecha_nacimiento')
	list_filter = ('cargo', 'user__date_joined', 'fecha_nacimiento')
	search_fields = ('user__username', 'user__email', 'dni_nie', 'complex__name', 'cargo', 'telefono_responsable')

	fieldsets = (
		('Información de Usuario', {
			'fields': ('user',)
		}),
		('Datos del Propietario', {
			'fields': ('dni_nie', 'cargo', 'telefono_responsable', 'fecha_nacimiento')
		}),
		('Complejo Asociado', {
			'fields': ('complex',)
		}),
	)

	def usuario(self, obj):
		"""Muestra el nombre de usuario."""
		return obj.user.username
	usuario.short_description = 'Usuario'

	def complejo(self, obj):
		"""Muestra el nombre del complejo asociado."""
		return obj.complex.name if obj.complex else '-'
	complejo.short_description = 'Complejo'

admin.site.register(Jugador, JugadorAdmin)
admin.site.register(Propietario, PropietarioAdmin)
