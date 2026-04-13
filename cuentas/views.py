from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from bookings.models import Booking
from venues.models import Sport, Complex

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
            return redirect('core:explorar_complejos')
        else:
            messages.error(request, 'Credenciales inválidas.')
            return render(request, 'cuentas/login.html')


@login_required
def logout_usuario(request):
    if request.method == 'POST':
        auth_logout(request)
        return redirect('core:home')
    return redirect('cuentas:home_usuario')


@login_required
def home_usuario(request):
    user = request.user
    perfil_jugador = getattr(user, 'perfil_jugador', None)

    nombre = user.first_name or user.username
    if perfil_jugador and perfil_jugador.nombre:
        nombre = perfil_jugador.nombre

    nombre_complejo = request.GET.get('nombre', '').strip()
    deporte = request.GET.get('deporte', '').strip()
    ciudad = request.GET.get('ciudad', '').strip()

    partidos_proximos = (
        Booking.objects
        .filter(user=user, start__gte=timezone.now())
        .exclude(status=Booking.Status.CANCELLED)
        .select_related('court__complex')
        .order_by('start')[:6]
    )

    reservas_pendientes = Booking.objects.filter(
        user=user,
        start__gte=timezone.now(),
        status__in=[Booking.Status.PENDING_PAYMENT, Booking.Status.CONFIRMED],
    ).count()

    reservas_historial = Booking.objects.filter(
        user=user,
        start__lt=timezone.now(),
    ).count()

    context = {
        'nombre': nombre,
        'deportes': Sport.choices,
        'filtros': {
            'nombre': nombre_complejo,
            'deporte': deporte,
            'ciudad': ciudad,
        },
        'reservas_pendientes': reservas_pendientes,
        'reservas_historial': reservas_historial,
        'notificaciones_count': 0,
        'partidos_proximos': partidos_proximos,
    }
    return render(request, 'cuentas/home_usuario.html', context)

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
        return redirect('cuentas:login')

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
        email_responsable = request.POST.get('email_responsable', '').strip()
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
        if not email_comercial:
            email_comercial = email_responsable

        # simple validaciones básicas
        missing = []
        for field_name, value in [
            ('usuario', username),
            ('contraseña', password),
            ('nombre responsable', nombre_responsable),
            ('apellido responsable', apellido_responsable),
            ('email responsable', email_responsable),
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

        # crear usuario (nombre/apellido del responsable en auth_user)
        user = User.objects.create_user(username=username, password=password)
        user.first_name = nombre_responsable
        user.last_name = apellido_responsable
        user.email = email_responsable
        user.save()

        complex_obj = Complex.objects.create(
            owner=user,
            nombre_legal=nombre_legal,
            name=nombre_complejo,
            id_fiscal=id_fiscal,
            categoria_fiscal=categoria_fiscal,
            calle=calle,
            altura=altura,
            city=ciudad,
            barrio=barrio,
            telefono_comercial=telefono_comercial,
            email_comercial=email_comercial,
        )

        # crear perfil propietario
        from .models import Propietario
        Propietario.objects.create(
            user=user,
            complex=complex_obj,
            dni_nie=dni_nie,
            cargo=cargo,
            telefono_responsable=telefono_responsable,
            fecha_nacimiento=fecha_nacimiento,
        )

        messages.success(request, 'Registro de propietario completado. Puedes iniciar sesión.')
        return redirect('cuentas:login')
