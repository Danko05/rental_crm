"""
Service Layer для роботи з автомобілями
"""
from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q
from rental_app.models import Car, Rental


class CarService:
    """Сервіс для управління автомобілями"""
    
    @staticmethod
    def get_available_cars():
        """Отримує доступні автомобілі"""
        return Car.objects.filter(status='available')
    
    @staticmethod
    def get_cars_available_for_dates(start_date, end_date):
        """
        Отримує автомобілі, які доступні на вказані дати оренди.
        
        Показує всі автомобілі, але виключає ті, які мають оренду зі статусом
        'active', 'pending' або 'overdue', яка перетинається з вказаним періодом.
        
        Args:
            start_date: Дата початку оренди
            end_date: Дата закінчення оренди
            
        Returns:
            QuerySet доступних автомобілів
        """
        from django.db.models import Q
        
        # Показуємо всі автомобілі (не тільки зі статусом 'available')
        all_cars = Car.objects.all()
        
        # Виключаємо автомобілі, які мають активні оренди на вказаний період
        # Перевіряємо перетин дат оренд:
        # - оренда починається до кінця нашого періоду
        # - оренда закінчується після початку нашого періоду
        busy_cars = Rental.objects.filter(
            status__in=['active', 'pending', 'overdue'],
            start_date__lte=end_date,
            expected_end_date__gte=start_date
        ).values_list('car_id', flat=True).distinct()
        
        # Повертаємо всі автомобілі, які не зайняті на вказаний період
        return all_cars.exclude(id__in=busy_cars)
    
    @staticmethod
    def is_car_busy_for_dates(car, start_date, end_date):
        """
        Перевіряє, чи автомобіль зайнятий на вказані дати.
        
        Args:
            car: Автомобіль для перевірки
            start_date: Дата початку оренди
            end_date: Дата закінчення оренди
            
        Returns:
            bool: True якщо автомобіль зайнятий на вказаний період
        """
        return Rental.objects.filter(
            car=car,
            status__in=['active', 'pending', 'overdue'],
            start_date__lte=end_date,
            expected_end_date__gte=start_date
        ).exists()
    
    @staticmethod
    def get_cars_by_status(status):
        """Отримує автомобілі за статусом"""
        return Car.objects.filter(status=status)
    
    @staticmethod
    def get_car_financial_report(car):
        """
        Отримує фінансовий звіт по автомобілю
        
        Returns:
            dict з фінансовими показниками
        """
        completed_rentals = car.rentals.filter(status='completed')
        
        total_revenue = completed_rentals.aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0.00')
        
        total_fines = sum(
            fine.amount for rental in completed_rentals
            for fine in rental.fines.all()
        )
        
        # Розраховуємо середню тривалість оренди
        if completed_rentals.exists():
            total_days = sum(
                rental.days_rented for rental in completed_rentals
            )
            avg_rental_duration = total_days / completed_rentals.count()
        else:
            avg_rental_duration = 0
        
        return {
            'car': car,
            'total_rentals': completed_rentals.count(),
            'total_revenue': total_revenue,
            'total_fines': Decimal(str(total_fines)),
            'net_revenue': total_revenue - Decimal(str(total_fines)),
            'avg_rental_duration': round(avg_rental_duration, 1),
            'occupancy_rate': CarService._calculate_occupancy_rate(car),
        }
    
    @staticmethod
    def _calculate_occupancy_rate(car):
        """Розраховує коефіцієнт зайнятості авто"""
        from datetime import date, timedelta
        from django.utils import timezone
        
        # Розраховуємо за останні 90 днів
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        total_days = 90
        rented_days = 0
        
        rentals = car.rentals.filter(
            start_date__lte=end_date,
            expected_end_date__gte=start_date,
            status__in=['active', 'completed']
        )
        
        for rental in rentals:
            rental_start = max(rental.start_date, start_date)
            rental_end = min(
                rental.actual_end_date or rental.expected_end_date,
                end_date
            )
            if rental_end >= rental_start:
                rented_days += (rental_end - rental_start).days + 1
        
        return round((rented_days / total_days) * 100, 2) if total_days > 0 else 0
    
    @staticmethod
    def get_top_cars_by_revenue(limit=5):
        """Отримує ТОП автомобілів за виручкою"""
        cars = Car.objects.annotate(
            revenue=Sum('rentals__total_cost', filter=Q(rentals__status='completed'))
        ).order_by('-revenue')[:limit]
        
        return cars
    
    @staticmethod
    def get_cars_occupancy_report():
        """Отримує звіт по зайнятості автомобілів"""
        cars = Car.objects.all()
        report = []
        
        for car in cars:
            report.append({
                'car': car,
                'status': car.get_status_display(),
                'occupancy_rate': CarService._calculate_occupancy_rate(car),
                'total_rentals': car.rentals.count(),
            })
        
        return sorted(report, key=lambda x: x['occupancy_rate'], reverse=True)

