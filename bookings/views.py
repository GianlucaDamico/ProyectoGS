from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Booking
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: solo el dueño de la reserva puede editarla.

    Este es un patrón muy común en APIs REST.
    Permite que cualquier usuario autenticado pueda ver reservas,
    pero solo el dueño puede modificarlas o eliminarlas.
    """

    def has_object_permission(self, request, view, obj):
        # Permisos de lectura (GET, HEAD, OPTIONS) están permitidos para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permisos de escritura solo para el dueño de la reserva
        return obj.user == request.user
class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Reservas.

    Proporciona todas las operaciones CRUD:
    - list: GET /api/bookings/
    - create: POST /api/bookings/
    - retrieve: GET /api/bookings/{id}/
    - update: PUT /api/bookings/{id}/
    - partial_update: PATCH /api/bookings/{id}/
    - destroy: DELETE /api/bookings/{id}/

    También incluye acciones personalizadas como 'my_bookings' y 'cancel'.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    # Filtros disponibles
    filterset_fields = ['status', 'court', 'lighting']

    # Ordenamiento
    ordering_fields = ['start', 'end', 'created_at']
    ordering = ['-start']  # Por defecto, más recientes primero

    def get_queryset(self):
        """
        Retorna las reservas según el usuario.

        IMPORTANTE: Este es el patrón de "aislamiento por usuario" que
        mencionan los documentos técnicos. Cada usuario solo ve sus propias
        reservas, a menos que sea superusuario.
        """
        user = self.request.user

        # Los superusuarios ven todo
        if user.is_superuser:
            queryset = Booking.objects.all()
        else:
            # Los usuarios normales solo ven sus propias reservas
            queryset = Booking.objects.filter(user=user)

        # Optimización: traemos relaciones en la misma query
        queryset = queryset.select_related('user', 'court', 'court__complex')

        return queryset

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'list':
            return BookingListSerializer
        else:  # retrieve
            return BookingDetailSerializer

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """
        Endpoint personalizado: "Mis Partidos"

        URL: GET /api/bookings/my_bookings/

        Retorna solo las reservas del usuario autenticado,
        útil para mostrar "Mis Partidos" en el frontend.

        El parámetro detail=False significa que este endpoint
        no requiere un ID específico, aplica a la colección.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Podemos añadir filtros adicionales aquí
        # Por ejemplo, solo reservas futuras
        future_only = request.query_params.get('future', None)
        if future_only == 'true':
            from django.utils import timezone
            queryset = queryset.filter(start__gte=timezone.now())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva reserva.

        El usuario se asigna automáticamente desde el request (ver serializer).
        Aquí también podríamos añadir lógica adicional, como calcular
        el precio total automáticamente.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Aquí podrías calcular el precio total antes de guardar
        # Por ahora asumimos que viene en el request

        self.perform_create(serializer)

        # Retornamos el detalle completo de la reserva creada
        headers = self.get_success_headers(serializer.data)
        booking = serializer.instance
        detail_serializer = BookingDetailSerializer(booking)

        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

