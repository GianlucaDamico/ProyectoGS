from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from venues.models import Complex, Court, Amenity, Sport, Surface

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