from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
import json
from bookings.models import Booking
from venues.models import Sport, Complex, Court, Review, Surface
from venues.forms import CourtForm
from .models import Jugador, Propietario

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
            # Redirigir según el tipo de usuario
            if hasattr(user, 'perfil_jugador'):
                return redirect('core:explorar_complejos')
            elif hasattr(user, 'perfil_propietario'):
                return redirect('cuentas:home_propietario')
            else:
                return redirect('core:home')
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

    # Obtener reservas que pueden ser reseñadas (sin reseña)
    # Dos casos: 1) Status FINISHED (marcadas manualmente) 2) Hora de fin ya pasó (automático)
    resenas_pendientes = (
        Booking.objects
        .filter(user=user)
        .filter(
            # O bien está marcada como FINISHED, O bien la hora de fin ya pasó
            models.Q(status=Booking.Status.FINISHED) | models.Q(end__lt=timezone.now())
        )
        .exclude(status=Booking.Status.CANCELLED)  # Excluir canceladas
        .exclude(review__isnull=False)  # Excluir las que ya tienen reseña
        .select_related('court__complex')
        .order_by('-end')
    )

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
        'resenas_pendientes': resenas_pendientes,
        'notificaciones_count': resenas_pendientes.count(),
        'partidos_proximos': partidos_proximos,
    }
    return render(request, 'cuentas/home_usuario.html', context)


@login_required
def home_propietario(request):
    user = request.user
    perfil_propietario = getattr(user, 'perfil_propietario', None)
    nombre = user.first_name or user.username

    if perfil_propietario and perfil_propietario.complex:
        complex = perfil_propietario.complex
        today = timezone.now().date()
        current_year = today.year
        current_month_start = today.replace(day=1)
        
        if current_month_start.month == 12:
            next_month_start = current_month_start.replace(year=current_year + 1, month=1)
        else:
            next_month_start = current_month_start.replace(month=current_month_start.month + 1)

        # 1. Métricas Básicas
        canchas_activas = complex.courts.count()
        reservas_dia = Booking.objects.filter(court__complex=complex, start__date=today).count()
        ingresos_dia = Booking.objects.filter(
            court__complex=complex, start__date=today,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        reservas_mes = Booking.objects.filter(court__complex=complex, start__gte=current_month_start, start__lt=next_month_start).count()
        ingresos_mes = Booking.objects.filter(
            court__complex=complex, start__gte=current_month_start, start__lt=next_month_start,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        reservas_pendientes = Booking.objects.filter(court__complex=complex, start__gte=today, status=Booking.Status.PENDING_PAYMENT).count()

        # 2. Comparativa Mes Anterior (Para el indicador +%)
        last_month_start = (current_month_start - datetime.timedelta(days=1)).replace(day=1)
        ingresos_mes_pasado = Booking.objects.filter(
            court__complex=complex, start__gte=last_month_start, start__lt=current_month_start,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        crecimiento_ingresos = 0
        if ingresos_mes_pasado > 0:
            crecimiento_ingresos = ((float(ingresos_mes) - float(ingresos_mes_pasado)) / float(ingresos_mes_pasado)) * 100

        # 3. Gráfica Principal: Ingresos Mensuales
        ingresos_por_mes = Booking.objects.filter(
            court__complex=complex, start__year=current_year,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.FINISHED]
        ).annotate(month=TruncMonth('start')).values('month').annotate(total=Sum('total_price')).order_by('month')

        meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        datos_grafica = [0] * 12
        for item in ingresos_por_mes:
            if item['month']:
                mes_index = item['month'].month - 1
                datos_grafica[mes_index] = float(item['total'])

        # 4. Gráfica Secundaria: Reservas por Deporte
        reservas_por_deporte = Booking.objects.filter(
            court__complex=complex, start__gte=current_month_start, start__lt=next_month_start
        ).values('court__sport').annotate(total=Count('id'))

        nombres_deportes = [item['court__sport'] for item in reservas_por_deporte]
        datos_deportes = [item['total'] for item in reservas_por_deporte]

        # 5. Próximas Reservas
        proximas_reservas = Booking.objects.filter(
            court__complex=complex,
            start__gte=timezone.now(),
            status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING_PAYMENT]
        ).order_by('start')[:5]

        context = {
            'nombre': nombre,
            'complex': complex,
            'canchas_activas': canchas_activas,
            'reservas_dia': reservas_dia,
            'ingresos_dia': ingresos_dia,
            'reservas_mes': reservas_mes,
            'ingresos_mes': ingresos_mes,
            'reservas_pendientes': reservas_pendientes,
            'crecimiento_ingresos': round(crecimiento_ingresos, 1),
            'chart_labels': json.dumps(meses_nombres),
            'chart_data': json.dumps(datos_grafica),
            'sports_labels': json.dumps(nombres_deportes),
            'sports_data': json.dumps(datos_deportes),
            'current_year': current_year,
            'proximas_reservas': proximas_reservas,
        }
    else:
        context = {'nombre': nombre, 'complex': None}
    return render(request, 'cuentas/home_propietario.html', context)


@login_required
def agenda(request):
    user = request.user
    perfil_propietario = getattr(user, 'perfil_propietario', None)

    if not perfil_propietario or not perfil_propietario.complex:
        # Si no tiene complejo, redirigir o mostrar error
        messages.error(request, 'No tienes un complejo asignado.')
        return redirect('cuentas:home_propietario')

    complex = perfil_propietario.complex

    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.datetime.fromisoformat(selected_date_str).date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Obtener courts del complex
    courts = complex.courts.all()

    # Para cada court, obtener bookings en selected_date
    agenda_data = []
    for court in courts:
        bookings = Booking.objects.filter(
            court=court,
            start__date=selected_date,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.IN_PROGRESS]
        ).select_related('user__perfil_jugador').order_by('start')

        court_data = {
            'court': court,
            'bookings': []
        }

        for booking in bookings:
            user_name = booking.user.get_full_name() or booking.user.username
            telefono = getattr(booking.user.perfil_jugador, 'telefono', '') if hasattr(booking.user, 'perfil_jugador') else ''
            court_data['bookings'].append({
                'hora': booking.start.strftime('%H:%M'),
                'usuario': user_name,
                'telefono': telefono,
            })

        agenda_data.append(court_data)

    nombre = user.first_name or user.username
    context = {
        'nombre': nombre,
        'page': 'Agenda',
        'selected_date': selected_date,
        'agenda_data': agenda_data,
    }
    return render(request, 'cuentas/agenda.html', context)


@login_required
def configuration(request):
    user = request.user
    perfil_propietario = getattr(user, 'perfil_propietario', None)

    if not perfil_propietario or not perfil_propietario.complex:
        messages.error(request, 'No tienes un complejo asignado.')
        return redirect('cuentas:home_propietario')

    complex = perfil_propietario.complex

    nombre = user.first_name or user.username
    context = {
        'nombre': nombre,
        'page': 'Configuración',
        'complejo': complex,
    }
    return render(request, 'cuentas/configuration.html', context)


@login_required
def gestion(request):
    user = request.user
    perfil_propietario = getattr(user, 'perfil_propietario', None)

    if not perfil_propietario or not perfil_propietario.complex:
        messages.error(request, 'No tienes un complejo asignado.')
        return redirect('cuentas:home_propietario')

    complex = perfil_propietario.complex

    if request.method == 'POST':
        if 'add_court' in request.POST:
            form = CourtForm(request.POST)
            if form.is_valid():
                court = form.save(commit=False)
                court.complex = complex
                court.save()
                messages.success(request, 'Cancha agregada exitosamente.')
                return redirect('cuentas:gestion')
        elif 'delete_court' in request.POST:
            court_id = request.POST.get('court_id')
            try:
                court = Court.objects.get(id=court_id, complex=complex)
                court.delete()
                messages.success(request, 'Cancha eliminada exitosamente.')
            except Court.DoesNotExist:
                messages.error(request, 'Cancha no encontrada.')
            return redirect('cuentas:gestion')
    else:
        form = CourtForm()

    courts = complex.courts.all()

    nombre = user.first_name or user.username
    context = {
        'nombre': nombre,
        'page': 'Gestión',
        'courts': courts,
        'form': form,
        'sport_choices': Sport.choices,
        'surface_choices': Surface.choices,
    }
    return render(request, 'cuentas/gestion.html', context)


@login_required
def resenas(request):
    from django.db.models import Avg
    user = request.user
    perfil_propietario = getattr(user, 'perfil_propietario', None)

    nombre = user.first_name or user.username
    
    # Obtener las reseñas del complejo del propietario
    resenas = []
    promedio_calificacion = 0
    if perfil_propietario and perfil_propietario.complex:
        resenas = Review.objects.filter(
            complex=perfil_propietario.complex
        ).select_related('user').order_by('-created_at')
        
        # Calcular el promedio de calificación
        promedio_data = Review.objects.filter(
            complex=perfil_propietario.complex
        ).aggregate(promedio=Avg('rating'))
        promedio_calificacion = promedio_data['promedio'] or 0
    
    context = {
        'nombre': nombre,
        'page': 'Reseñas',
        'resenas': resenas,
        'promedio_calificacion': promedio_calificacion,
    }
    return render(request, 'cuentas/resenas.html', context)


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


@login_required
@csrf_exempt
def update_description(request, complex_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        descripcion = data.get('descripcion', '')
        try:
            complex = request.user.perfil_propietario.complex
            if complex.id != complex_id:
                return JsonResponse({'success': False, 'error': 'No autorizado'})
            complex.descripcion = descripcion
            complex.save()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})


@login_required
@csrf_exempt
def update_contact(request, complex_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        telefono = data.get('telefono_comercial', '')
        email = data.get('email_comercial', '')
        try:
            complex = request.user.perfil_propietario.complex
            if complex.id != complex_id:
                return JsonResponse({'success': False, 'error': 'No autorizado'})
            complex.telefono_comercial = telefono
            complex.email_comercial = email
            complex.save()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})


@login_required
@csrf_exempt
def add_amenity(request, complex_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False})
        try:
            complex = request.user.perfil_propietario.complex
            if complex.id != complex_id:
                return JsonResponse({'success': False, 'error': 'No autorizado'})
            from venues.models import Amenity
            amenity, created = Amenity.objects.get_or_create(name=name)
            complex.amenities.add(amenity)
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})


@login_required
@csrf_exempt
def remove_amenity(request, complex_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        amenity_id = data.get('amenity_id')
        try:
            complex = request.user.perfil_propietario.complex
            if complex.id != complex_id:
                return JsonResponse({'success': False, 'error': 'No autorizado'})
            from venues.models import Amenity
            amenity = Amenity.objects.get(id=amenity_id)
            complex.amenities.remove(amenity)
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

@login_required
@csrf_exempt
def update_image(request, complex_id):
    if request.method == 'POST':
        user = request.user
        perfil_propietario = getattr(user, 'perfil_propietario', None)

        # 1. Seguridad: Verificar que el usuario sea el dueño de este complejo exacto
        if not perfil_propietario or not perfil_propietario.complex or perfil_propietario.complex.id != complex_id:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        complex = perfil_propietario.complex

        # 2. Capturar y guardar la imagen
        # Nota: Los archivos no vienen en request.POST, vienen en request.FILES
        if 'imagen' in request.FILES:
            complex.imagen = request.FILES['imagen']
            complex.save()
            return JsonResponse({'success': True, 'message': 'Imagen actualizada'})
        else:
            return JsonResponse({'error': 'No se envió ninguna imagen'}, status=400)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)

from django.http import JsonResponse
from venues.models import Court

@login_required
def update_court_api(request, court_id):
    if request.method == 'POST':
        try:
            # 1. Obtener la cancha y verificar que pertenezca al complejo del usuario
            court = Court.objects.get(id=court_id)
            if court.complex.owner != request.user:
                return JsonResponse({'error': 'No tienes permiso'}, status=403)

            # 2. Actualizar campos de texto y números
            court.name = request.POST.get('name')
            court.sport = request.POST.get('sport')
            court.surface = request.POST.get('surface')
            court.has_lighting = request.POST.get('has_lighting') == 'on'
            court.base_price_per_hour = request.POST.get('base_price_per_hour')
            court.lighting_extra_per_hour = request.POST.get('lighting_extra_per_hour')

            # 3. Actualizar imagen solo si se subió una nueva
            if 'imagen' in request.FILES:
                court.imagen = request.FILES['imagen']

            court.save()
            return JsonResponse({'success': True})

        except Court.DoesNotExist:
            return JsonResponse({'error': 'Cancha no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)