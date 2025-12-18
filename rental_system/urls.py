"""
URL configuration for rental_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rental_app import client_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('rental_app.api_urls')),
    path('client/', include('rental_app.client_urls')),
    path('admin-panel/', include('rental_app.admin_urls')),
    path('', client_views.car_catalog, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

