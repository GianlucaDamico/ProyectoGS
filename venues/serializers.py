from rest_framework import serializers
from .models import Amenity, Court

class AmenitySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Amenity.
    """

    class Meta:
        model = Amenity
        fields = ['id', 'name']
        read_only_fields = ['id']

class CourtListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para Court cuando se muestra en listas.
    """
    sport_display = serializers.CharField(source='get_sport_display', read_only=True)
    surface_display = serializers.CharField(source='get_surface_display', read_only=True)

    class Meta:
        model = Court
        fields = [
            'id',
            'name',
            'sport',
            'sport_display',
            'surface',
            'surface_display',
            'has_lighting',
            'base_price_per_hour',
            'lighting_extra_per_hour'
        ]
        read_only_fields = ['id']

class CourtDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Court con información del complejo.
    """
    sport_display = serializers.CharField(source='get_sport_display', read_only=True)
    surface_display = serializers.CharField(source='get_surface_display', read_only=True)

    complex_name = serializers.SerializerMethodField()
    complex_city = serializers.SerializerMethodField()

    class Meta:
        model = Court
        fields = [
            'id',
            'complex',
            'complex_name',
            'complex_city',
            'name',
            'sport',
            'sport_display',
            'surface',
            'surface_display',
            'has_lighting',
            'base_price_per_hour',
            'lighting_extra_per_hour'
        ]
        read_only_fields = ['id']

    def get_complex_name(self, obj):
        return obj.complex.name

    def get_complex_city(self, obj):
        return obj.complex.city