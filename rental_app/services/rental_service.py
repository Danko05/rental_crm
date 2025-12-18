"""
Service Layer для роботи з орендами
Використовує принципи SOLID та GRASP
"""
from datetime import date
from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Sum, Avg
from rental_app.models import Rental, Car, Fine, Payment
from rental_app.patterns.rental_factory import RentalFactory
from rental_app.patterns.fine_calculator import FineCalculator
from rental_app.patterns.pricing_strategy import PricingStrategyFactory


class RentalService:
    """
    Сервіс для управління орендами.
    Інкапсулює всю бізнес-логіку роботи з орендами.
    """
    
    @staticmethod
    def create_rental(client, car, start_date, end_date):
        """
        Створює нову оренду через Factory.
        
        Args:
            client: Профіль клієнта
            car: Автомобіль для оренди
            start_date: Дата початку оренди
            end_date: Дата закінчення оренди
            
        Returns:
            Створена оренда
            
        Raises:
            ValueError: Якщо валідація не пройдена
        """
        return RentalFactory.create_rental(client, car, start_date, end_date)
    
    @staticmethod
    def get_client_rentals(client):
        """
        Отримує всі оренди клієнта, відсортовані за датою створення.
        
        Args:
            client: Профіль клієнта
            
        Returns:
            QuerySet оренд клієнта
        """
        return Rental.objects.filter(client=client).order_by('-created_at')
    
    @staticmethod
    def get_active_rentals():
        """
        Отримує всі активні оренди.
        
        Включає оренди зі статусом 'active' та 'pending', які вже почалися.
        
        Returns:
            QuerySet активних оренд
        """
        from django.utils import timezone
        today = timezone.now().date()
        return Rental.objects.filter(
            status__in=['active', 'pending'],
            start_date__lte=today
        )
    
    @staticmethod
    def update_overdue_rentals():
        """
        Оновлює статус прострочених оренд та активує pending оренди.
        
        Автоматично:
        - Змінює статус 'pending' на 'active' для оренд, які вже почалися
        - Змінює статус 'active' на 'overdue' для оренд з простроченою датою повернення
        
        Returns:
            Кількість оновлених оренд
        """
        today = date.today()
        
        # Активуємо pending оренди, які вже почалися
        pending_to_active = Rental.objects.filter(
            status='pending',
            start_date__lte=today
        )
        pending_count = pending_to_active.count()
        pending_to_active.update(status='active')
        
        # Оновлюємо прострочені оренди
        overdue_rentals = Rental.objects.filter(
            status='active',
            expected_end_date__lt=today
        )
        overdue_count = overdue_rentals.count()
        overdue_rentals.update(status='overdue')
        
        return pending_count + overdue_count
    
    @staticmethod
    @transaction.atomic
    def complete_rental(rental, actual_end_date, damage_level, late_days):
        """
        Завершує оренду з розрахунком штрафів та оновленням статусів.
        
        Args:
            rental: Оренда для завершення
            actual_end_date: Фактична дата повернення
            damage_level: Рівень пошкоджень (0-3)
            late_days: Кількість днів запізнення
            
        Returns:
            tuple: (rental, total_fines, refund)
                - rental: Оновлена оренда
                - total_fines: Загальна сума штрафів
                - refund: Сума повернення застави
        """
        calculator = FineCalculator()
        
        # Розрахунок штрафів
        total_fines = calculator.calculate_total_fines(rental, damage_level, late_days)
        refund = calculator.calculate_refund(rental, total_fines)
        
        # Оновлення даних оренди
        rental.actual_end_date = actual_end_date
        rental.damage_level = damage_level
        rental.late_days = late_days
        rental.status = 'completed'
        
        # Перерахунок вартості з урахуванням фактичних днів та штрафів
        strategy = PricingStrategyFactory.get_default_strategy()
        rental.total_cost = strategy.calculate_price(
            rental.car, 
            rental.start_date, 
            actual_end_date
        )
        rental.total_cost += total_fines
        rental.save()
        
        # Створення записів про штрафи
        RentalService._create_fine_records(rental, calculator, damage_level, late_days)
        
        # Повернення застави (якщо є що повертати)
        if refund > 0:
            Payment.objects.create(
                rental=rental,
                payment_type='refund',
                amount=refund
            )
        
        # Оновлення статусу автомобіля
        rental.car.status = 'available'
        rental.car.save()
        
        return rental, total_fines, refund
    
    @staticmethod
    def _create_fine_records(rental, calculator, damage_level, late_days):
        """
        Створює записи про штрафи в базі даних.
        
        Args:
            rental: Оренда
            calculator: Калькулятор штрафів
            damage_level: Рівень пошкоджень
            late_days: Кількість днів запізнення
        """
        if damage_level > 0:
            damage_fine = calculator.strategy.calculate_damage_fine(rental, damage_level)
            Fine.objects.create(
                rental=rental,
                reason=f"Пошкодження рівня {damage_level}",
                amount=damage_fine
            )
        
        if late_days > 0:
            late_fine = calculator.strategy.calculate_late_fine(rental, late_days)
            Fine.objects.create(
                rental=rental,
                reason=f"Запізнення на {late_days} днів",
                amount=late_fine
            )
    
    @staticmethod
    def get_rental_statistics():
        """
        Отримує статистику по орендам.
        
        Returns:
            dict: Словник зі статистикою:
                - total_rentals: Загальна кількість оренд
                - active_rentals: Кількість активних оренд
                - completed_rentals: Кількість завершених оренд
                - overdue_rentals: Кількість прострочених оренд
                - total_revenue: Загальна виручка
                - total_fines: Загальна сума штрафів
        """
        completed_rentals = Rental.objects.filter(status='completed')
        
        # Активні оренди включають active та pending (які вже почалися)
        from django.utils import timezone
        today = timezone.now().date()
        active_rentals_count = Rental.objects.filter(
            status__in=['active', 'pending'],
            start_date__lte=today
        ).count()
        
        stats = {
            'total_rentals': Rental.objects.count(),
            'active_rentals': active_rentals_count,
            'completed_rentals': completed_rentals.count(),
            'overdue_rentals': Rental.objects.filter(status='overdue').count(),
            'total_revenue': completed_rentals.aggregate(
                total=Sum('total_cost')
            )['total'] or Decimal('0.00'),
            'total_fines': Fine.objects.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
        }
        
        return stats
