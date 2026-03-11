from rest_framework import serializers
from .models import Amenity, Court, Complex

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
    
class ComplexListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar complejos.
    Incluye información resumida de las canchas que tiene.
    """
    courts = CourtListSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    courts_count = serializers.SerializerMethodField()

    class Meta:
        model = Complex
        fields = [
            'id',
            'name',
            'city',
            'calle',
            'altura',
            'city',
            'barrio',
            'telefono_comercial',
            'email_comercial',
            'amenities',
            'courts_count',
            'courts'
        ]
        read_only_fields = ['id']

    def get_courts_count(self, obj):
        return obj.courts.count()

class ComplexDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para un complejo específico.
    Incluye toda la información de las canchas.
    """
    courts = CourtDetailSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Complex
        fields = [
            'id',
            'owner',
            'owner_username',
            'name',
            'city',
            'calle',
            'altura',
            'city',
            'barrio',
            'telefono_comercial',
            'email_comercial',
            'amenities',
            'courts'
        ]
        read_only_fields = ['id', 'owner']