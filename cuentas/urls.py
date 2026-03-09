from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('home', views.home_usuario, name='home_usuario'),
    path('logout', views.logout_usuario, name='logout_usuario'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('register/jugador', views.register_jugador, name='register_jugador'),
    path('register/propietario', views.register_propietario, name='register_propietario'),
]