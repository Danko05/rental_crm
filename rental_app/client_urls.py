"""
URLs для клієнтського інтерфейсу
"""
from django.urls import path
from django.contrib.auth.views import LogoutView
from rental_app import client_views

app_name = 'client'

urlpatterns = [
    path('', client_views.car_catalog, name='catalog'),
    path('register/', client_views.client_register, name='register'),
    path('login/', client_views.client_login, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', client_views.client_dashboard, name='dashboard'),
    path('profile/edit/', client_views.client_profile_edit, name='profile_edit'),
    path('catalog/', client_views.car_catalog, name='catalog_list'),
    path('car/<int:car_id>/', client_views.car_detail, name='car_detail'),
    path('car/<int:car_id>/calculate-price/', client_views.calculate_rental_price, name='calculate_price'),
    path('my-rentals/', client_views.my_rentals, name='my_rentals'),
    path('rental/<int:rental_id>/', client_views.rental_detail, name='rental_detail'),
]

