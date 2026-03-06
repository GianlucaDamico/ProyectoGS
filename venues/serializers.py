from rest_framework import serializers
from .models import Amenity

class AmenitySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Amenity.
    """

    class Meta:
        model = Amenity
        fields = ['id', 'name']
        read_only_fields = ['id']