from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Complex, Court, Amenity
from .serializers import (
    AmenitySerializer,
    CourtListSerializer,
    CourtDetailSerializer
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