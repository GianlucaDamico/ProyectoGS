from rest_framework import serializers
from .models import Booking
from venues.serializers import CourtDetailSerializer

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