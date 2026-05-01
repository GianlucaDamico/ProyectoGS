from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count, Q, Case, When, Value, IntegerField, F
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone

# Importes de modelos locales
from venues.models import Complex, Court, Sport, Surface, Review
from bookings.models import Booking

# --- VISTAS GENERALES ---

def home(request):
    return render(request, 'core/home.html')

def terminos(request):
    return render(request, 'core/terminos.html')

def privacidad(request):
    return render(request, 'core/privacidad.html')

def cookies(request):
    return render(request, 'core/cookies.html')

def contacto(request):
    return render(request, 'core/contacto.html')

# --- VISTAS DE COMPLEJOS ---

def complejo_detalle(request, complejo_id, slug=None):
    """Vista de detalle de un complejo deportivo."""
    complejo = get_object_or_404(
        Complex.objects.select_related('owner').prefetch_related(
            'amenities',
            'courts__bookings'
        ),
        id=complejo_id
    )
    
    filtro_deporte = request.GET.get('deporte', '')
    filtro_superficie = request.GET.get('superficie', '')
    
    canchas = complejo.courts.all()
    
    if filtro_deporte:
        canchas = canchas.filter(sport=filtro_deporte)
    
    if filtro_superficie:
        canchas = canchas.filter(surface=filtro_superficie)
    
    deportes_disponibles = complejo.courts.values_list('sport', flat=True).distinct()
    superficies_disponibles = complejo.courts.values_list('surface', flat=True).distinct()
    
    # Obtenemos las reseñas asociadas a este complejo específico
    resenas = Review.objects.filter(complex=complejo).select_related('user').order_by('-created_at')
    
    # Calculamos el promedio
    promedio_data = resenas.aggregate(promedio=Avg('rating'))
    promedio_calificacion = promedio_data['promedio'] or 0
    cantidad_resenas = resenas.count() # Útil para el texto del link

    # 👇 LÓGICA DE NOTIFICACIONES AÑADIDA AQUÍ 👇
    resenas_pendientes = None
    if request.user.is_authenticated:
        resenas_pendientes = (
            Booking.objects
            .filter(user=request.user)
            .filter(
                Q(status=Booking.Status.FINISHED) | Q(end__lt=timezone.now())
            )
            .exclude(status=Booking.Status.CANCELLED)
            .exclude(review__isnull=False)
            .select_related('court__complex')
            .order_by('-end')
        )

    context = {
        'complejo': complejo,
        'canchas': canchas,
        'filtro_deporte': filtro_deporte,
        'filtro_superficie': filtro_superficie,
        'deportes_disponibles': deportes_disponibles,
        'superficies_disponibles': superficies_disponibles,
        'sport_choices': Sport.choices,
        'surface_choices': Surface.choices,
        'resenas': resenas,
        'promedio_calificacion': promedio_calificacion,
        'cantidad_resenas': cantidad_resenas,
        'resenas_pendientes': resenas_pendientes, # ← PASADO AL CONTEXTO
    }
    
    return render(request, 'core/complejo_detalle.html', context)

@login_required(login_url='cuentas:login')
def explorar_complejos(request):
    """Vista de exploración de complejos con filtros, búsqueda y notificaciones."""
    query = request.GET.get('q', '')
    ciudad = request.GET.get('ciudad', '')
    deporte = request.GET.get('deporte', '')
    orden = request.GET.get('orden', 'nombre')
    
    complejos = Complex.objects.select_related('owner').prefetch_related(
        'courts', 'amenities'
    ).annotate(
        # distinct=True es vital aquí para que no se mezclen las canchas con las reseñas
        num_courts=Count('courts', distinct=True), 
        cantidad_resenas=Count('reviews', distinct=True),
        promedio_calificacion=Avg('reviews__rating')
    ).filter(
        num_courts__gt=0
    )
    
    if query:
        complejos = complejos.filter(
            Q(name__icontains=query) | Q(city__icontains=query)
        )
    
    if ciudad:
        complejos = complejos.filter(city__iexact=ciudad)
    
    if deporte:
        complejos = complejos.filter(courts__sport=deporte).distinct()
    
    if orden == 'nombre':
        complejos = complejos.order_by('name')
    elif orden == 'ciudad':
        complejos = complejos.order_by('city', 'name')
    elif orden == 'canchas':
        complejos = complejos.order_by('-num_courts', 'name')
    elif orden == 'calificacion':
        complejos = complejos.order_by(F('promedio_calificacion').desc(nulls_last=True), 'name')
    
    ciudades_disponibles = Complex.objects.values_list('city', flat=True).distinct().order_by('city')
    
    paginator = Paginator(complejos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Lógica de NOTIFICACIONES (Reseñas pendientes) para la navbar
    resenas_pendientes = None
    if request.user.is_authenticated:
        resenas_pendientes = (
            Booking.objects
            .filter(user=request.user)
            .filter(
                Q(status=Booking.Status.FINISHED) | Q(end__lt=timezone.now())
            )
            .exclude(status=Booking.Status.CANCELLED)
            .exclude(review__isnull=False)
            .select_related('court__complex')
            .order_by('-end')
        )
    
    context = {
        'page_obj': page_obj,
        'complejos': page_obj.object_list,
        'total_complejos': paginator.count,
        'query': query,
        'ciudad_filtro': ciudad,
        'deporte_filtro': deporte,
        'orden_actual': orden,
        'ciudades_disponibles': ciudades_disponibles,
        'sport_choices': Sport.choices,
        'resenas_pendientes': resenas_pendientes,
    }
    
    return render(request, 'core/explorar_complejos.html', context)

# --- VISTAS DE RESERVAS ---

@login_required(login_url='cuentas:login')
def mis_reservas(request):
    """Muestra las reservas del usuario actual actualizando estados caducados."""
    reservas = Booking.objects.filter(user=request.user)
    
    # Actualización lógica de estados por tiempo
    for reserva in reservas:
        if reserva.status == Booking.Status.PENDING_PAYMENT and reserva.is_past():
            reserva.status = Booking.Status.CANCELLED
            reserva.save()
        elif reserva.status == Booking.Status.CONFIRMED and reserva.is_past():
            reserva.status = Booking.Status.FINISHED
            reserva.save()
        elif reserva.status == Booking.Status.CONFIRMED and reserva.is_active():
            reserva.status = Booking.Status.IN_PROGRESS
            reserva.save()
        elif reserva.status == Booking.Status.IN_PROGRESS and reserva.is_past():
            reserva.status = Booking.Status.FINISHED
            reserva.save()

    # Verificar si se solicita ver el historial
    mostrar_historial = request.GET.get('historial', 'false').lower() == 'true'
    
    # Re-consulta con ordenamiento específico
    if mostrar_historial:
        # Mostrar solo reservas finalizadas y canceladas
        reservas = Booking.objects.filter(
            user=request.user,
            status__in=[Booking.Status.FINISHED, Booking.Status.CANCELLED]
        ).select_related(
            'court', 'court__complex'
        ).annotate(
            status_order=Case(
                When(status=Booking.Status.FINISHED, then=Value(1)),
                When(status=Booking.Status.CANCELLED, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('status_order', '-start')
        
        # Para el historial, mostrar todos los estados (FINISHED y CANCELLED)
        allowed_statuses = [
            Booking.Status.FINISHED,
            Booking.Status.CANCELLED,
        ]
    else:
        # Mostrar solo reservas confirmadas, pendientes de pago e en curso
        reservas = Booking.objects.filter(
            user=request.user,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING_PAYMENT, Booking.Status.IN_PROGRESS]
        ).select_related(
            'court', 'court__complex'
        ).annotate(
            status_order=Case(
                When(status=Booking.Status.IN_PROGRESS, then=Value(1)),
                When(status=Booking.Status.PENDING_PAYMENT, then=Value(2)),
                When(status=Booking.Status.CONFIRMED, then=Value(3)),
                When(status=Booking.Status.FINISHED, then=Value(4)),
                When(status=Booking.Status.CANCELLED, then=Value(5)),
                default=Value(6),
                output_field=IntegerField(),
            )
        ).order_by('status_order', '-start')
        
        # Para la vista normal, solo mostrar estados activos
        allowed_statuses = [
            Booking.Status.PENDING_PAYMENT,
            Booking.Status.CONFIRMED,
            Booking.Status.IN_PROGRESS,
        ]
    
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        reservas = reservas.filter(status=estado_filtro)
        
    resenas_pendientes = (
        Booking.objects
        .filter(user=request.user)
        .filter(
            Q(status=Booking.Status.FINISHED) | Q(end__lt=timezone.now())
        )
        .exclude(status=Booking.Status.CANCELLED)
        .exclude(review__isnull=False)
        .select_related('court__complex')
        .order_by('-end')
    )
    
    # Filtrar status_choices para solo mostrar los estados permitidos
    status_choices = [
        (status, label)
        for status, label in Booking.Status.choices
        if status in allowed_statuses
    ]
    
    context = {
        'reservas': reservas,
        'estado_filtro': estado_filtro,
        'status_choices': status_choices,
        'resenas_pendientes': resenas_pendientes,
        'mostrar_historial': mostrar_historial,
    }
    
    return render(request, 'core/mis_reservas.html', context)

@login_required(login_url='cuentas:login')
def reserva_detalle(request, reserva_id):
    """Detalle de una reserva con permisos y lógica de acciones."""
    reserva = get_object_or_404(
        Booking.objects.select_related('user', 'court', 'court__complex'),
        id=reserva_id
    )
    
    if not (request.user == reserva.user or request.user.is_staff):
        return render(request, 'core/error.html', {'message': 'No tienes permiso para ver esta reserva'}, status=403)
    
    # Actualización de estado según tiempo
    if reserva.status == Booking.Status.PENDING_PAYMENT and reserva.is_past():
        reserva.status = Booking.Status.CANCELLED
        reserva.save()
    elif reserva.status == Booking.Status.CONFIRMED and reserva.is_past():
        reserva.status = Booking.Status.FINISHED
        reserva.save()
    elif reserva.status == Booking.Status.CONFIRMED and reserva.is_active():
        reserva.status = Booking.Status.IN_PROGRESS
        reserva.save()
    elif reserva.status == Booking.Status.IN_PROGRESS and reserva.is_past():
        reserva.status = Booking.Status.FINISHED
        reserva.save()

    es_propietario = request.user == reserva.user
    es_admin = request.user.is_staff
    
    puede_confirmar_pago = es_propietario and reserva.status == Booking.Status.PENDING_PAYMENT and not reserva.is_past()
    puede_cancelar = es_propietario and reserva.can_be_cancelled()
    
    puede_cambiar_estado = es_admin
    todas_las_transiciones = [
        ('confirmed', 'Confirmar'),
        ('in_progress', 'En curso'),
        ('finished', 'Finalizada'),
        ('cancelled', 'Cancelada'),
    ] if puede_cambiar_estado else []
    
    context = {
        'reserva': reserva,
        'es_propietario': es_propietario,
        'es_admin': es_admin,
        'puede_confirmar_pago': puede_confirmar_pago,
        'puede_cancelar': puede_cancelar,
        'puede_cambiar_estado': puede_cambiar_estado,
        'transiciones_disponibles': todas_las_transiciones,
    }
    
    return render(request, 'core/reserva_detalle.html', context)

@login_required(login_url='cuentas:login')
@require_POST
def cambiar_estado_reserva(request, reserva_id):
    """Procesa el cambio de estado de una reserva vía POST o AJAX."""
    reserva = get_object_or_404(Booking, id=reserva_id)
    
    if not (request.user == reserva.user or request.user.is_staff):
        return JsonResponse({'error': 'No tienes permiso para modificar esta reserva'}, status=403)
    
    nuevo_estado = request.POST.get('nuevo_estado')
    estados_validos = [choice[0] for choice in Booking.Status.choices]
    
    if nuevo_estado not in estados_validos:
        return JsonResponse({'error': 'Estado no válido'}, status=400)
    
    es_propetario = request.user == reserva.user
    es_admin = request.user.is_staff

    if es_propetario and not es_admin:
        if nuevo_estado == Booking.Status.CONFIRMED and reserva.status == Booking.Status.PENDING_PAYMENT:
            reserva.status = Booking.Status.CONFIRMED
        elif nuevo_estado == Booking.Status.CANCELLED and reserva.can_be_cancelled():
            reserva.status = Booking.Status.CANCELLED
        else:
            return JsonResponse({'error': f'No puedes cambiar el estado a {nuevo_estado}'}, status=403)
    elif es_admin:
        reserva.status = nuevo_estado
    else:
        return JsonResponse({'error': 'No tienes permiso'}, status=403)
    
    reserva.save()

    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect('core:mis_reservas')
    
    return JsonResponse({
        'success': 'Estado actualizado', 
        'nuevo_estado': reserva.get_status_display(),
        'nuevo_estado_code': reserva.status,
        'mensaje': f'La reserva ha sido actualizada a {reserva.get_status_display()}'
    })

@login_required(login_url='cuentas:login')
def notificaciones(request):
    """Vista de notificaciones del usuario (placeholder)."""

    reservas = Booking.objects.filter(user=request.user)
    
    # Actualización lógica de estados por tiempo
    for reserva in reservas:
        if reserva.status == Booking.Status.PENDING_PAYMENT and reserva.is_past():
            reserva.status = Booking.Status.CANCELLED
            reserva.save()
        elif reserva.status == Booking.Status.CONFIRMED and reserva.is_past():
            reserva.status = Booking.Status.FINISHED
            reserva.save()
        elif reserva.status == Booking.Status.CONFIRMED and reserva.is_active():
            reserva.status = Booking.Status.IN_PROGRESS
            reserva.save()
        elif reserva.status == Booking.Status.IN_PROGRESS and reserva.is_past():
            reserva.status = Booking.Status.FINISHED
            reserva.save()

    now = timezone.now()
    fechas_cercanas = now + timezone.timedelta(days=2)

    notificaciones = Booking.objects.filter(
        user = request.user
    ).filter(
        Q(status=Booking.Status.CONFIRMED, start__lte=fechas_cercanas) |
        Q(status=Booking.Status.PENDING_PAYMENT)
    ). select_related('court', 'court__complex').order_by('start')

    context = {
        'notificaciones': notificaciones,
        'now': now,
    }

    return render(request, 'core/notificaciones.html', context)