from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('home', views.home_usuario, name='home_usuario'),
    path('dashboard/control/', views.home_propietario, name='home_propietario'),
    path('dashboard/agenda/', views.agenda, name='agenda'),
    path('dashboard/configuration/', views.configuration, name='configuration'),
    path('dashboard/gestion/', views.gestion, name='gestion'),
    path('dashboard/resenas/', views.resenas, name='resenas'),
    path('logout', views.logout_usuario, name='logout_usuario'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('register/jugador', views.register_jugador, name='register_jugador'),
    path('register/propietario', views.register_propietario, name='register_propietario'),
]