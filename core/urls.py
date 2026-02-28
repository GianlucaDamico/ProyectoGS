from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # El primer argumento vacío '' significa la raíz de esta app
    path('', views.home, name='home'), 
]