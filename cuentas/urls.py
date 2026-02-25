from django.urls import path
from . import views

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('register/jugador', views.register_jugador, name='register_jugador'),
    path('register/propietario', views.register_propietario, name='register_propietario'),
]