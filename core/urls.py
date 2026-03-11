from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('cookies/', views.cookies, name='cookies'),
    path('contacto/', views.contacto, name='contacto'),
]