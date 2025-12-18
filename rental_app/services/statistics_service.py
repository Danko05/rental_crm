"""
Service Layer для статистики та звітів
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, Q
from django.db import models
from django.utils import timezone
from rental_app.models import Rental, Car, Fine, Payment, ClientProfile


class StatisticsService:
    """Сервіс для генерації статистики"""
    
    @staticmethod
    def get_dashboard_stats():
        """Отримує статистику для dashboard"""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Загальна статистика
        total_cars = Car.objects.count()
        available_cars = Car.objects.filter(status='available').count()
        # Активні оренди = active + pending (які вже почалися або починаються сьогодні)
        today = timezone.now().date()
        active_rentals = Rental.objects.filter(
            status__in=['active', 'pending'],
            start_date__lte=today
        ).count()
        total_clients = ClientProfile.objects.count()
        
        # Фінансова статистика
        # Дохід за місяць - враховуємо оренди, які завершилися в поточному місяці
        # (використовуємо actual_end_date, якщо він є, інакше expected_end_date)
        monthly_revenue = Rental.objects.filter(
            status='completed'
        ).filter(
            models.Q(actual_end_date__gte=month_start, actual_end_date__isnull=False) |
            models.Q(actual_end_date__isnull=True, expected_end_date__gte=month_start)
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')
        
        total_revenue = Rental.objects.filter(
            status='completed'
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')
        
        total_deposits = Payment.objects.filter(
            payment_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_fines = Fine.objects.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # ТОП автомобілі
        from rental_app.services.car_service import CarService
        top_cars = CarService.get_top_cars_by_revenue(5)
        
        return {
            'total_cars': total_cars,
            'available_cars': available_cars,
            'active_rentals': active_rentals,
            'total_clients': total_clients,
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue,
            'total_deposits': total_deposits,
            'total_fines': total_fines,
            'top_cars': top_cars,
        }
    
    @staticmethod
    def get_revenue_by_period(start_date, end_date):
        """Отримує виручку за період - групує по датах завершення оренди"""
        # Шукаємо оренди, які завершилися в цьому періоді
        rentals = Rental.objects.filter(
            status='completed'
        ).filter(
            Q(actual_end_date__gte=start_date, actual_end_date__lte=end_date, actual_end_date__isnull=False) |
            Q(actual_end_date__isnull=True, expected_end_date__gte=start_date, expected_end_date__lte=end_date)
        )
        
        # Групуємо по днях - використовуємо дату завершення оренди
        revenue_by_day = {}
        for rental in rentals:
            # Використовуємо actual_end_date, якщо він є, інакше expected_end_date
            day = rental.actual_end_date if rental.actual_end_date else rental.expected_end_date
            
            if day not in revenue_by_day:
                revenue_by_day[day] = Decimal('0.00')
            revenue_by_day[day] += rental.total_cost
        
        return sorted(revenue_by_day.items())
    
    @staticmethod
    def get_average_rental_cost():
        """Отримує середню вартість оренди"""
        avg = Rental.objects.filter(
            status='completed'
        ).aggregate(avg=Avg('total_cost'))['avg']
        
        return avg or Decimal('0.00')

