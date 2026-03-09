from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AmenityViewSet, CourtViewSet, ComplexViewSet

# Creamos un router
router = DefaultRouter()

# Registramos nuestros viewsets
# El primer argumento es el prefijo de la URL
# El segundo es el viewset
# El tercero es el basename (usado para generar nombres de URL)

router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'courts', CourtViewSet, basename='court')
router.register(r'complexes', ComplexViewSet, basename='complex')

# El router genera automáticamente estos URLs:
# GET    /complexes/          → list
# POST   /complexes/          → create (si estuviera habilitado)
# GET    /complexes/{id}/     → retrieve
# PUT    /complexes/{id}/     → update (si estuviera habilitado)
# PATCH  /complexes/{id}/     → partial_update (si estuviera habilitado)
# DELETE /complexes/{id}/     → destroy (si estuviera habilitado)
# GET    /courts/{id}/availability/  → acción personalizada

urlpatterns = [
    path('', include(router.urls)),
]