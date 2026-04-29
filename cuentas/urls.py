from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('home', views.home_usuario, name='home_usuario'),
    path('dashboard/control/', views.home_propietario, name='home_propietario'),
    path('dashboard/agenda/', views.agenda, name='agenda'),
    path('dashboard/configuration/', views.configuration, name='configuration'),
    path('api/complex/<int:complex_id>/update-description/', views.update_description, name='update_description'),
    path('api/complex/<int:complex_id>/update-contact/', views.update_contact, name='update_contact'),
    path('api/complex/<int:complex_id>/add-amenity/', views.add_amenity, name='add_amenity'),
    path('api/complex/<int:complex_id>/remove-amenity/', views.remove_amenity, name='remove_amenity'),
    path('api/complex/<int:complex_id>/update-image/', views.update_image, name='update_image'),
    path('api/court/<int:court_id>/edit/', views.update_court_api, name='update_court_api'),
    path('api/user/update-avatar/', views.update_avatar, name='update_avatar'),
    path('dashboard/gestion/', views.gestion, name='gestion'),
    path('dashboard/resenas/', views.resenas, name='resenas'),
    path('logout', views.logout_usuario, name='logout_usuario'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('register/jugador', views.register_jugador, name='register_jugador'),
    path('register/propietario', views.register_propietario, name='register_propietario'),
]