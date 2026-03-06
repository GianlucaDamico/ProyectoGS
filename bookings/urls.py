from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

# El router genera automáticamente:
# GET    /bookings/              → list
# POST   /bookings/              → create
# GET    /bookings/{id}/         → retrieve
# PUT    /bookings/{id}/         → update
# PATCH  /bookings/{id}/         → partial_update
# DELETE /bookings/{id}/         → destroy
# GET    /bookings/my_bookings/  → acción personalizada
# POST   /bookings/{id}/cancel/  → acción personalizada

urlpatterns = [
    path('', include(router.urls)),
]