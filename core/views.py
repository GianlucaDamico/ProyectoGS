from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'core/home.html')

def terminos(request):
    return render(request, 'core/terminos.html')

def privacidad(request):
    return render(request, 'core/privacidad.html')

def contacto(request):
    return render(request, 'core/contacto.html')