from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from venues.models import Complex, Court, Amenity, Sport, Surface
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

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

    return render(request, 'core/mis_reservas.html')