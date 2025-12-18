"""
URLs для REST API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rental_app import api_views

router = DefaultRouter()
router.register(r'cars', api_views.CarViewSet, basename='car')
router.register(r'rentals', api_views.RentalViewSet, basename='rental')
router.register(r'clients', api_views.ClientProfileViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
]

