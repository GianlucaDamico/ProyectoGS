from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, Case, When, Value, IntegerField
from venues.models import Complex, Court, Amenity, Sport, Surface
from bookings.models import Booking
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your views here.
from django.http import HttpResponse

def home(request):
    return render(request, 'core/home.html')


def complejo_detalle(request, complejo_id, slug=None):
    """
    Vista de detalle de un complejo deportivo.
    
    Muestra toda la información del complejo y sus canchas.
    Permite filtrar las canchas por deporte y superficie.
    
    Args:
        complejo_id: ID del complejo
        slug: Slug del nombre (opcional, para URLs amigables)
    """
    # Obtener el complejo con optimizaciones
    complejo = get_object_or_404(
        Complex.objects.select_related('owner').prefetch_related(
            'amenities',
            'courts__bookings'  # Para verificar disponibilidad en el futuro
        ),
        id=complejo_id
    )
    
    # Obtener parámetros de filtrado desde la URL
    # Ejemplo: /complejo/1/?deporte=padel&superficie=cesped_sintetico
    filtro_deporte = request.GET.get('deporte', '')
    filtro_superficie = request.GET.get('superficie', '')
    
    # Empezar con todas las canchas del complejo
    canchas = complejo.courts.all()
    
    # Aplicar filtros si existen
    if filtro_deporte:
        canchas = canchas.filter(sport=filtro_deporte)
    
    if filtro_superficie:
        canchas = canchas.filter(surface=filtro_superficie)
    
    # Obtener listas únicas de deportes y superficies para los filtros
    # Esto nos permite mostrar solo las opciones disponibles en este complejo
    deportes_disponibles = complejo.courts.values_list('sport', flat=True).distinct()
    superficies_disponibles = complejo.courts.values_list('surface', flat=True).distinct()
    
    context = {
        'complejo': complejo,
        'canchas': canchas,
        'filtro_deporte': filtro_deporte,
        'filtro_superficie': filtro_superficie,
        # Choices para los filtros (desde el modelo)
        'deportes_disponibles': deportes_disponibles,
        'superficies_disponibles': superficies_disponibles,
        'sport_choices': Sport.choices,
        'surface_choices': Surface.choices,
    }
    
    return render(request, 'core/complejo_detalle.html', context)

def explorar_complejos(request):
    """
    Vista de exploración de complejos.
    
    Muestra todos los complejos con filtros y búsqueda.
    Permite ordenar y paginar los resultados.
    """
    # Obtener parámetros de búsqueda y filtrado
    query = request.GET.get('q', '')  # Búsqueda por nombre
    ciudad = request.GET.get('ciudad', '')  # Filtro por ciudad
    deporte = request.GET.get('deporte', '')  # Filtro por deporte
    orden = request.GET.get('orden', 'nombre')  # Ordenamiento
    
    # Empezar con todos los complejos que tienen canchas
    complejos = Complex.objects.select_related('owner').prefetch_related(
        'courts', 'amenities'
    ).annotate(
        num_courts=Count('courts')
    ).filter(
        num_courts__gt=0  # Solo complejos con al menos 1 cancha
    )
    
    # Aplicar búsqueda por nombre si existe
    if query:
        complejos = complejos.filter(
            Q(name__icontains=query) | Q(city__icontains=query)
        )
    
    # Aplicar filtro por ciudad si existe
    if ciudad:
        complejos = complejos.filter(city__iexact=ciudad)
    
    # Aplicar filtro por deporte si existe
    if deporte:
        complejos = complejos.filter(courts__sport=deporte).distinct()
    
    # Aplicar ordenamiento
    if orden == 'nombre':
        complejos = complejos.order_by('name')
    elif orden == 'ciudad':
        complejos = complejos.order_by('city', 'name')
    elif orden == 'canchas':
        complejos = complejos.order_by('-num_courts', 'name')
    
    # Obtener listas para los filtros
    ciudades_disponibles = Complex.objects.values_list('city', flat=True).distinct().order_by('city')
    
    # Paginación: 12 complejos por página
    paginator = Paginator(complejos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'complejos': page_obj.object_list,
        'total_complejos': paginator.count,
        # Parámetros de búsqueda para mantenerlos en el formulario
        'query': query,
        'ciudad_filtro': ciudad,
        'deporte_filtro': deporte,
        'orden_actual': orden,
        # Opciones para filtros
        'ciudades_disponibles': ciudades_disponibles,
        'sport_choices': Sport.choices,
    }
    
    return render(request, 'core/explorar_complejos.html', context)

@login_required(login_url='cuentas:login')
def mis_reservas(request):
    """
    Muestra todas las reservas del usuario autenticado, ordenadas por estado y fecha.
    
    Esta función retrieves las reservas del usuario actual y actualiza automáticamente
    su estado según la fecha actual (por ej., cambia de confirmada a finalizada si ya pasó).
    Permite filtrar por estado y muestra la información de la cancha y el complejo.
    
    Ordena por:
    1. Estado (en_progreso → pendiente_pago → confirmada → finalizada → cancelada)
    2. Fecha (más recientes primero)
    """
    
    reservas = Booking.objects.filter(user=request.user).select_related(
        'court', 'court__complex'
    )
    
    now = timezone.now()
    
    
    for reserva in reservas:
        # Caso 1: Si está pendiente de pago y ya pasó → cancelar automáticamente
        if reserva.status == Booking.Status.PENDING_PAYMENT and reserva.is_past():
            reserva.status = Booking.Status.CANCELLED
            reserva.save()
        # Caso 2: Si está confirmada y ya pasó → marcar como finalizada
        elif reserva.status == Booking.Status.CONFIRMED and reserva.is_past():
            reserva.status = Booking.Status.FINISHED
            reserva.save()
        # Caso 3: Si está confirmada pero ahora está en curso → cambiar a en_progreso
        elif reserva.status == Booking.Status.CONFIRMED and reserva.is_active():
            reserva.status = Booking.Status.IN_PROGRESS
            reserva.save()
        # Caso 4: Si está en progreso y ya pasó → marcar como finalizada
        elif reserva.status == Booking.Status.IN_PROGRESS and reserva.is_past():
            reserva.status = Booking.Status.FINISHED
            reserva.save()
    
    
    reservas = Booking.objects.filter(user=request.user).select_related(
        'court', 'court__complex'
    ).annotate(
        # Asignar un valor de ordenamiento a cada estado
        status_order=Case(
            When(status=Booking.Status.IN_PROGRESS, then=Value(1)),
            When(status=Booking.Status.PENDING_PAYMENT, then=Value(2)),
            When(status=Booking.Status.CONFIRMED, then=Value(3)),
            When(status=Booking.Status.FINISHED, then=Value(4)),
            When(status=Booking.Status.CANCELLED, then=Value(5)),
            default=Value(6),
            output_field=IntegerField(),
        )
    ).order_by('status_order', '-start')  # Primero por estado, luego por fecha descendente
    
    
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        reservas = reservas.filter(status=estado_filtro)
    
    
    context = {
        'reservas': reservas,
        'estado_filtro': estado_filtro,
        'status_choices': Booking.Status.choices,
    }
    
    
    return render(request, 'core/mis_reservas.html', context)

@login_required(login_url='cuentas:login')
def reserva_detalle(request, reserva_id):
    """
    Muestra los detalles completos de una reserva específica con permiso de acceso.
    
    Esta función obtiene una reserva específica y verifica que el usuario sea el propietario
    o administrador. Actualiza automáticamente el estado según la fecha actual y determina
    qué acciones (confirmación de pago, cancelación, cambio de estado) puede realizar el usuario.
    Propietarios solo pueden confirmar pago o cancelar, mientras que administradores pueden
    cambiar a cualquier estado.
    
    Args:
        reserva_id: ID de la reserva a mostrar
    """
   
    reserva = get_object_or_404(
        Booking.objects.select_related(
            'user', 'court', 'court__complex'
        ),
        id=reserva_id
    )
    
  
    if not (request.user == reserva.user or request.user.is_staff):
        return render(
            request,
            'core/error.html',
            {'message': 'No tienes permiso para ver esta reserva'},
            status=403
        )
    
    
    now = timezone.now()
    
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
    
   
    puede_confirmar_pago = (
        es_propietario and 
        reserva.status == Booking.Status.PENDING_PAYMENT and
        not reserva.is_past()
    )
    
    puede_cancelar = (
        es_propietario and 
        reserva.can_be_cancelled()
    )
    
 
    puede_cambiar_estado = es_admin
    todas_las_transiciones = [] if not puede_cambiar_estado else [
        ('confirmed', 'Confirmar'),
        ('in_progress', 'En curso'),
        ('finished', 'Finalizada'),
        ('cancelled', 'Cancelada'),
    ]
    
  
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