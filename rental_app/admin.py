"""
Django Admin налаштування
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from rental_app.models import User, ClientProfile, Car, CarType, Rental, Fine, Payment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_client', 'is_staff', 'is_superuser')
    list_filter = ('is_client', 'is_staff', 'is_superuser')


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'get_email', 'is_blocked', 'created_at')
    list_filter = ('is_blocked', 'created_at')
    search_fields = ('full_name', 'phone', 'user__email')
    readonly_fields = ('created_at',)
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'


@admin.register(CarType)
class CarTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'car_type', 'daily_price', 'status', 'created_at')
    list_filter = ('status', 'car_type', 'year')
    search_fields = ('brand', 'model')
    readonly_fields = ('created_at',)


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('client', 'car', 'start_date', 'expected_end_date', 'status', 'total_cost', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('client__full_name', 'car__brand', 'car__model')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('rental', 'reason', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('reason', 'rental__client__full_name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('rental', 'payment_type', 'amount', 'created_at')
    list_filter = ('payment_type', 'created_at')
    search_fields = ('rental__client__full_name',)

