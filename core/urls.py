from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('', views.home, name='home'), 
    path('complejo/<int:complejo_id>/', views.complejo_detalle, name='complejo_detalle_simple'),
    path('complejo/<int:complejo_id>/<slug:slug>/', views.complejo_detalle, name='complejo_detalle'),
    path('explorar_complejos/', views.explorar_complejos, name='explorar_complejos'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('reserva/<int:reserva_id>/', views.reserva_detalle, name='reserva_detalle'),
    path('reserva/<int:reserva_id>/cambiar-estado/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('cookies/', views.cookies, name='cookies'),
    path('contacto/', views.contacto, name='contacto'),
    path('notificaciones/', views.notificaciones, name='notificaciones')
]