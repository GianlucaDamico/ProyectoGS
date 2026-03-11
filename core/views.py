from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'core/home.html')

def terminos(request):
    return render(request, 'core/terminos.html')

def contacto(request):
    # Por ahora solo renderiza la página, puedes añadir lógica de formulario luego
    return render(request, 'core/contacto.html')