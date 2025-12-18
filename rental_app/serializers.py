"""
Serializers для REST API
"""
from rest_framework import serializers
from rental_app.models import Car, Rental, ClientProfile, Fine, Payment, CarType


class CarTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarType
        fields = ['id', 'name', 'description']


class CarSerializer(serializers.ModelSerializer):
    car_type = CarTypeSerializer(read_only=True)
    car_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CarType.objects.all(),
        source='car_type',
        write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'car_type', 'car_type_id',
            'year', 'daily_price', 'photo', 'description',
            'status', 'status_display', 'is_available', 'created_at'
        ]


class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = ['id', 'reason', 'amount', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'payment_type', 'payment_type_display', 'amount', 'created_at']


class ClientProfileSerializer(serializers.ModelSerializer):
    total_rentals = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ClientProfile
        fields = [
            'id', 'full_name', 'address', 'phone',
            'is_blocked', 'created_at', 'total_rentals'
        ]


class RentalSerializer(serializers.ModelSerializer):
    client = ClientProfileSerializer(read_only=True)
    car = CarSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fines = FineSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    days_rented = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Rental
        fields = [
            'id', 'client', 'car', 'start_date', 'expected_end_date',
            'actual_end_date', 'deposit', 'daily_cost', 'total_cost',
            'status', 'status_display', 'damage_level', 'late_days',
            'created_at', 'updated_at', 'fines', 'payments', 'days_rented'
        ]
        read_only_fields = ['actual_end_date', 'total_cost', 'status', 'created_at', 'updated_at']

