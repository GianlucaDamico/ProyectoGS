from django.urls import path
from . import views

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
]