from django.shortcuts import render
from bookings.services import BookingService
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .services import ComplexStatsService as ComplexService
from django.utils.dateparse import parse_datetime
from rest_framework import status

from .models import Complex, Court, Amenity
from .serializers import (
    AmenitySerializer,
    CourtListSerializer,
    CourtDetailSerializer,
    ComplexListSerializer,
    ComplexDetailSerializer
)


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Amenities (servicios).

    ReadOnlyModelViewSet proporciona automáticamente:
    - list: GET /api/amenities/
    - retrieve: GET /api/amenities/{id}/

    No permite crear, actualizar o eliminar porque los amenities
    son gestionados solo por administradores desde el admin de Django.
    """
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny] 

class CourtViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Canchas.

    Permite buscar y filtrar canchas por diferentes criterios.
    Útil para cuando un jugador busca dónde jugar.
    """
    queryset = Court.objects.all()
    permission_classes = [permissions.AllowAny]  # Búsqueda pública
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtros específicos para canchas
    filterset_fields = ['sport', 'surface', 'has_lighting', 'complex']

    # Búsqueda por nombre de cancha o nombre de complejo
    search_fields = ['name', 'complex__name', 'complex__city']

    # Ordenamiento
    ordering_fields = ['base_price_per_hour', 'name']
    ordering = ['base_price_per_hour']  # Por defecto, más baratas primero

    def get_queryset(self):
        """
        Optimización y filtros personalizados.
        """
        queryset = Court.objects.all()

        # Optimización: traemos el complejo en la misma query
        queryset = queryset.select_related('complex')

        # Filtro personalizado: solo canchas de complejos activos
        # (Esto lo podrías implementar si añades un campo 'active' en Complex)
        # queryset = queryset.filter(complex__active=True)

        return queryset

    def get_serializer_class(self):
        """
        Serializer apropiado según la acción.
        """
        if self.action == 'list':
            return CourtListSerializer
        return CourtDetailSerializer

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Endpoint personalizado para verificar disponibilidad de una cancha.

        URL: GET /api/courts/{id}/availability/?date=2024-03-15

        Este es un ejemplo de cómo añadir acciones personalizadas a un ViewSet.
        Por ahora retorna un placeholder, lo implementaremos completamente después.
        """
        court = self.get_object()
        date = request.query_params.get('date', None)

        # Aquí implementarías lógica para verificar qué bloques horarios
        # están disponibles para esta cancha en la fecha especificada

        return Response({
            'court_id': court.id,
            'court_name': court.name,
            'date': date,
            'message': 'Endpoint de disponibilidad - implementación pendiente'
        })
    
    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        """
        Endpoint para verificar disponibilidad de una cancha en un rango de tiempo.

        URL: GET /api/courts/{id}/check_availability/?start=2024-03-15T10:00&end=2024-03-15T11:00

        Retorna si la cancha está disponible o no en ese rango.
        """
        court = self.get_object()
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        lighting = request.query_params.get('lighting', 'false').lower() == 'true'

        if not start or not end:
            return Response(
                {'error': 'Parámetros "start" y "end" son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start = parse_datetime(start)
            end = parse_datetime(end)

            if not start or not end:
                raise ValueError("Formato de fecha inválido")

        except ValueError as e:
            return Response(
                {'error': f"Error en el formato de fecha: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_available, conflicting = BookingService.check_availability(court, start, end)

        response_data = {
            'court_id': court.id,
            'court_name': court.name,
            'start': start,
            'end': end,
            'available': is_available,
        }

        if not is_available:
            from bookings.serializers import BookingListSerializer
            response_data['conflicting_bookings'] = BookingListSerializer(
                conflicting, many=True).data
        else : 
            estimated_price = BookingService.calculate_price(court, start, end, lighting)
            response_data['estimated_price'] = str(estimated_price)
            response_data['lighting_available'] = court.has_lighting
        
        return Response(response_data)

class ComplexViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Complejos deportivos.

    Proporciona endpoints para listar y ver detalles de complejos.
    Los usuarios pueden buscar y filtrar complejos sin estar autenticados.
    """
    queryset = Complex.objects.all()
    permission_classes = [permissions.AllowAny]  # Búsqueda pública
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Campos por los que se puede filtrar
    filterset_fields = ['city']

    # Campos por los que se puede buscar (con búsqueda parcial)
    search_fields = ['name', 'city']

    # Campos por los que se puede ordenar
    ordering_fields = ['name', 'city']
    ordering = ['name']  # Orden por defecto

    def get_queryset(self):
        """
        Optimizamos la query para traer relaciones necesarias
        y evitar el problema N+1.
        """
        queryset = Complex.objects.all()

        # Optimización: traemos canchas y amenities en la misma query
        queryset = queryset.prefetch_related('courts', 'amenities')

        return queryset

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.

        - list: serializer simplificado
        - retrieve: serializer detallado con toda la info
        """
        if self.action == 'list':
            return ComplexListSerializer
        return ComplexDetailSerializer
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):

        complex = self.get_object()
        if complex.owner != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'No tienes permiso para ver estas estadísticas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = request.query_params.get('days', 30)
        stats = ComplexService.get_complex_stats(complex, days=days)

        return Response(stats)