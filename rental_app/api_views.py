"""
REST API Views для системи прокату автомобілів
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rental_app.models import Car, Rental, ClientProfile
from rental_app.serializers import (
    CarSerializer, RentalSerializer, ClientProfileSerializer
)
from rental_app.services.rental_service import RentalService
from rental_app.services.car_service import CarService

User = get_user_model()


class CarViewSet(viewsets.ReadOnlyModelViewSet):
    """API для перегляду автомобілів"""
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Отримати доступні автомобілі"""
        cars = CarService.get_available_cars()
        serializer = self.get_serializer(cars, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def financial_report(self, request, pk=None):
        """Отримати фінансовий звіт по автомобілю"""
        car = self.get_object()
        report = CarService.get_car_financial_report(car)
        return Response(report)


class RentalViewSet(viewsets.ModelViewSet):
    """API для управління орендами"""
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Rental.objects.all()
        elif user.is_client and hasattr(user, 'client_profile'):
            return Rental.objects.filter(client=user.client_profile)
        return Rental.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Створити нову оренду"""
        if not request.user.is_client:
            return Response(
                {'error': 'Тільки клієнти можуть створювати оренди'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        client = request.user.client_profile
        car_id = request.data.get('car')
        start_date = request.data.get('start_date')
        end_date = request.data.get('expected_end_date')
        
        try:
            from datetime import datetime
            from rental_app.models import Car
            
            car = Car.objects.get(id=car_id)
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            rental = RentalService.create_rental(client, car, start, end)
            serializer = self.get_serializer(rental)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Завершити оренду (тільки для адмінів)"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Тільки адміністратори можуть завершувати оренди'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rental = self.get_object()
        actual_end_date = request.data.get('actual_end_date')
        damage_level = request.data.get('damage_level', 0)
        late_days = request.data.get('late_days', 0)
        
        try:
            from datetime import datetime
            end_date = datetime.strptime(actual_end_date, '%Y-%m-%d').date()
            
            rental, total_fines, refund = RentalService.complete_rental(
                rental, end_date, damage_level, late_days
            )
            
            return Response({
                'rental': RentalSerializer(rental).data,
                'total_fines': str(total_fines),
                'refund': str(refund),
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ClientProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """API для перегляду профілів клієнтів"""
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ClientProfile.objects.all()
        elif user.is_client and hasattr(user, 'client_profile'):
            return ClientProfile.objects.filter(user=user)
        return ClientProfile.objects.none()

