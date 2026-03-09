from rest_framework import serializers
from .models import Booking
from venues.serializers import CourtDetailSerializer
from .services import BookingService

class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar reservas.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    court_name = serializers.CharField(source='court.name', read_only=True)
    complex_name = serializers.CharField(source='court.complex.name', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    duration_minutes = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'court',
            'court_name',
            'complex_name',
            'start',
            'end',
            'duration_minutes',
            'status',
            'status_display',
            'total_price',
            'lighting',
            'is_past',
            'is_active',
            'can_cancel',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_duration_minutes(self, obj):
        return obj.get_duration_minutes()

    def get_is_past(self, obj):
        return obj.is_past()

    def get_is_active(self, obj):
        return obj.is_active()

    def get_can_cancel(self, obj):
        return obj.can_be_cancelled()

class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para una reserva específica.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    court_details = CourtDetailSerializer(source='court', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    duration_minutes = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'user_username',
            'court',
            'court_details',
            'start',
            'end',
            'duration_minutes',
            'status',
            'status_display',
            'total_price',
            'lighting',
            'is_past',
            'is_active',
            'can_cancel',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_duration_minutes(self, obj):
        return obj.get_duration_minutes()

    def get_is_past(self, obj):
        return obj.is_past()

    def get_is_active(self, obj):
        return obj.is_active()

    def get_can_cancel(self, obj):
        return obj.can_be_cancelled()

class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para crear nuevas reservas.
    """

    class Meta:
        model = Booking
        fields = [
            'court',
            'start',
            'end',
            'lighting',
        ]

    def validate(self, attrs):
        """
        Validaciones a nivel de objeto.
        """
        court = attrs['court']
        start = attrs['start']
        end = attrs['end']
        lighting = attrs.get('lighting', False)
        
        # Instancia temporal para validaciones del modelo
        booking = Booking(court=court, start=start, end=end, lighting=lighting)
        
        try:
            booking.clean()
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        # Verificamos disponibilidad usando el servicio
        is_available, conflicting = BookingService.check_availability(court, start, end)
        if not is_available:
            raise serializers.ValidationError(
                f"La cancha no está disponible en ese horario. "
                f"Hay {conflicting.count()} reserva(s) que solapan."
            )
        
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        booking = BookingService.create_booking(
            user=user,
            court=validated_data['court'],
            start=validated_data['start'],
            end=validated_data['end'],
            lighting=validated_data.get('lighting', False)
        )
        return booking

class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar reservas existentes.
    """

    class Meta:
        model = Booking
        fields = ['status', 'lighting']

    def validate_status(self, value):
        instance = self.instance

        if instance and instance.status != value:
            if instance.status == Booking.Status.FINISHED:
                raise serializers.ValidationError(
                    "No se puede cambiar el estado de una reserva finalizada."
                )

            if instance.status == Booking.Status.CANCELLED:
                raise serializers.ValidationError(
                    "No se puede cambiar el estado de una reserva cancelada."
                )

        return value