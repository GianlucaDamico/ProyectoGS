from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AmenityViewSet, CourtViewSet, ComplexViewSet, CreateReviewView

router = DefaultRouter()

router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'courts', CourtViewSet, basename='court')
router.register(r'complexes', ComplexViewSet, basename='complex')

urlpatterns = [
    path('', include(router.urls)),
    path('reviews/create/', CreateReviewView.as_view(), name='create-review'),
]