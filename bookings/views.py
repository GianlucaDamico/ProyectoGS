
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .services import BookingService
from django.utils import timezone
from datetime import timedelta

from .models import Booking
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer
)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: solo el dueño de la reserva puede editarla.

    Este es un patrón muy común en APIs REST.
    Permite que cualquier usuario autenticado pueda ver reservas,
    pero solo el dueño puede modificarlas o eliminarlas.
    """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

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

    filterset_fields = ['status', 'court', 'lighting']

    ordering_fields = ['start', 'end', 'created_at']
    ordering = ['-start']

    def get_queryset(self):
        """
        Retorna las reservas según el usuario.

        IMPORTANTE: Este es el patrón de "aislamiento por usuario" que
        mencionan los documentos técnicos. Cada usuario solo ve sus propias
        reservas, a menos que sea superusuario.
        """
        user = self.request.user

        if user.is_superuser:
            queryset = Booking.objects.all()
        else:

            queryset = Booking.objects.filter(user=user)

        queryset = queryset.select_related('user', 'court', 'court__complex')

        return queryset

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        else:
            return BookingDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea una nueva reserva.

        El usuario se asigna automáticamente desde el request (ver serializer).
        Aquí también podríamos añadir lógica adicional, como calcular
        el precio total automáticamente.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        booking = serializer.instance
        detail_serializer = BookingDetailSerializer(booking)

        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

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

        future_only = request.query_params.get('future', None)
        if future_only == 'true':
            queryset = queryset.filter(start__gte=timezone.now())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):

        booking = self.get_object()

        try:
            BookingService.cancel_booking(booking)

            serializer = BookingDetailSerializer(booking)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def disponibilidad(self, request):
        """
        Endpoint personalizado para consultar los horarios ocupados.
        Ruta: GET /api/bookings/disponibilidad/?court_id=X&fecha=YYYY-MM-DD
        """
        court_id = request.query_params.get('court_id')
        fecha = request.query_params.get('fecha')

        if not court_id or not fecha:
            return Response({'error': 'Faltan parámetros court_id y fecha'}, status=400)

        reservas = self.get_queryset().filter(
            court_id=court_id,
            start__date=fecha
        )

        reservas = reservas.exclude(status='CANCELLED')

        horas_ocupadas = []
        for reserva in reservas:

            tiempo_actual = reserva.start

            while tiempo_actual < reserva.end:
                hora_str = tiempo_actual.strftime('%H:%M')

                if hora_str not in horas_ocupadas:
                    horas_ocupadas.append(hora_str)

                tiempo_actual += timedelta(hours=1)

        return Response({'ocupados': horas_ocupadas})