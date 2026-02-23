from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def login(request):
    return render(request, 'cuentas/login.html')