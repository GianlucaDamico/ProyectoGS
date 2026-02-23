from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.

def login(request):
    
    if request.method == 'GET':
        return render(request, 'cuentas/login.html')
    
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Validar que ambos campos estén completos
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'cuentas/login.html')
        
        # FALTA CREAR USUARIOS EN LA BASE DE DATOS PARA PROBAR ESTA FUNCIONALIDAD

def register(request):
    return render(request, 'cuentas/register.html')