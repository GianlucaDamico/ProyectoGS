from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
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

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # redirigir según perfil o a home
            return redirect('core:home')
        else:
            messages.error(request, 'Credenciales inválidas.')
            return render(request, 'cuentas/login.html')

def register(request):
    return render(request, 'cuentas/register.html')

def register_jugador(request):
    if request.method == 'GET':
       return render(request, 'cuentas/register_jugador.html')
    
    elif request.method == 'POST':
        # extraer datos del formulario
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        deporte = request.POST.get('deporte', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # valida mínimo
        if not all([nombre, apellido, username, email, telefono, password, confirm_password]):
            messages.error(request, 'Por favor completa todos los campos.')
            return render(request, 'cuentas/register_jugador.html')

        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'cuentas/register_jugador.html')

        # crear user (username debe ser único)
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'cuentas/register_jugador.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        # opcional: llenar firstname/lastname
        user.first_name = nombre
        user.last_name = apellido
        user.save()

        # crear perfil de jugador
        from .models import Jugador
        Jugador.objects.create(
            user=user,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            deporte_preferido=deporte,
        )

        messages.success(request, 'Registro completado. Ya puedes iniciar sesión.')
        return redirect('cuentas:login.html')

def register_propietario(request):
    if request.method == 'GET':
       return render(request, 'cuentas/register_propietario.html')
    
    elif request.method == 'POST':
        # recogemos los datos (hay muchos, no olvidemos los pasos anteriores)
        username = request.POST.get('usuario_complejo', '').strip()
        password = request.POST.get('contraseña')
        confirm_password = request.POST.get('confirmar_contraseña')

        # Paso 1
        nombre_responsable = request.POST.get('nombre_responsable', '').strip()
        apellido_responsable = request.POST.get('apellido_responsable', '').strip()
        dni_nie = request.POST.get('dni_nie', '').strip()
        cargo = request.POST.get('cargo', '').strip()
        telefono_responsable = request.POST.get('telefono_responsable', '').strip()
        fecha_nacimiento = request.POST.get('fecha_nacimiento')

        # Paso 2
        nombre_legal = request.POST.get('nombre_legal', '').strip()
        nombre_complejo = request.POST.get('nombre_complejo', '').strip()
        id_fiscal = request.POST.get('id_fiscal', '').strip()
        categoria_fiscal = request.POST.get('categoria_fiscal', '').strip()

        # Paso 3
        calle = request.POST.get('calle', '').strip()
        altura = request.POST.get('altura', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        barrio = request.POST.get('barrio', '').strip()
        telefono_comercial = request.POST.get('telefono_comercial', '').strip()
        email_comercial = request.POST.get('email_comercial', '').strip()

        # simple validaciones básicas
        missing = []
        for field_name, value in [
            ('usuario', username),
            ('contraseña', password),
            ('nombre responsable', nombre_responsable),
            ('apellido responsable', apellido_responsable),
            ('DNI/NIE', dni_nie),
            ('cargo', cargo),
            ('tel. responsable', telefono_responsable),
            ('fecha nacimiento', fecha_nacimiento),
            ('nombre legal', nombre_legal),
            ('nombre complejo', nombre_complejo),
            ('ID fiscal', id_fiscal),
            ('categoría fiscal', categoria_fiscal),
            ('calle', calle),
            ('altura', altura),
            ('ciudad', ciudad),
            ('barrio', barrio),
            ('tel. comercial', telefono_comercial),
            ('email comercial', email_comercial),
        ]:
            if not value:
                missing.append(field_name)

        if missing:
            messages.error(request, f'Faltan campos: {", ".join(missing)}')
            return render(request, 'cuentas/register_propietario.html')

        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'cuentas/register_propietario.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'cuentas/register_propietario.html')

        # crear usuario
        user = User.objects.create_user(username=username, password=password)

        # crear perfil propietario
        from .models import Propietario
        Propietario.objects.create(
            user=user,
            nombre_responsable=nombre_responsable,
            apellido_responsable=apellido_responsable,
            dni_nie=dni_nie,
            cargo=cargo,
            telefono_responsable=telefono_responsable,
            fecha_nacimiento=fecha_nacimiento,
            nombre_legal=nombre_legal,
            nombre_complejo=nombre_complejo,
            id_fiscal=id_fiscal,
            categoria_fiscal=categoria_fiscal,
            calle=calle,
            altura=altura,
            ciudad=ciudad,
            barrio=barrio,
            telefono_comercial=telefono_comercial,
            email_comercial=email_comercial,
        )

        messages.success(request, 'Registro de propietario completado. Puedes iniciar sesión.')
        return redirect('cuentas:login')
