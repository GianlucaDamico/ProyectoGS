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
]