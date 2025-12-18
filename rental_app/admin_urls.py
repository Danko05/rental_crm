"""
URLs для адмінського інтерфейсу
"""
from django.urls import path
from rental_app import admin_views

app_name = 'admin_panel'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),
    path('cars/', admin_views.admin_cars, name='cars'),
    path('cars/add/', admin_views.admin_car_add, name='car_add'),
    path('cars/<int:car_id>/edit/', admin_views.admin_car_edit, name='car_edit'),
    path('cars/<int:car_id>/delete/', admin_views.admin_car_delete, name='car_delete'),
    path('cars/<int:car_id>/financial/', admin_views.admin_car_financial, name='car_financial'),
    path('cars/occupancy/', admin_views.admin_cars_occupancy, name='cars_occupancy'),
    path('clients/', admin_views.admin_clients, name='clients'),
    path('clients/<int:client_id>/', admin_views.admin_client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', admin_views.admin_client_edit, name='client_edit'),
    path('clients/<int:client_id>/delete/', admin_views.admin_client_delete, name='client_delete'),
    path('rentals/', admin_views.admin_rentals, name='rentals'),
    path('rentals/<int:rental_id>/', admin_views.admin_rental_detail, name='rental_detail'),
    path('rentals/<int:rental_id>/complete/', admin_views.admin_rental_complete, name='rental_complete'),
    path('statistics/', admin_views.admin_statistics, name='statistics'),
    path('car-types/', admin_views.admin_car_types, name='car_types'),
    path('car-types/add/', admin_views.admin_car_type_add, name='car_type_add'),
    path('car-types/<int:type_id>/edit/', admin_views.admin_car_type_edit, name='car_type_edit'),
    path('car-types/<int:type_id>/delete/', admin_views.admin_car_type_delete, name='car_type_delete'),
]

