from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Complex, Court, Amenity
from .serializers import (
    AmenitySerializer
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