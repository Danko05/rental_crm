"""
GoF Pattern: Factory Method
Інкапсулює логіку створення оренд з валідацією та обчисленнями
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from rental_app.models import Car, Rental, ClientProfile, Payment
from rental_app.patterns.pricing_strategy import PricingStrategyFactory


class RentalFactory:
    """Фабрика для створення оренд"""
    
    @staticmethod
    def calculate_deposit(car: Car, rental_days: int) -> Decimal:
        """Розраховує заставну суму (зазвичай 30% від вартості оренди)"""
        strategy = PricingStrategyFactory.get_default_strategy()
        estimated_end = date.today() + timedelta(days=rental_days)
        rental_cost = strategy.calculate_price(car, date.today(), estimated_end)
        return rental_cost * Decimal('0.3')
    
    @classmethod
    @transaction.atomic
    def create_rental(
        cls,
        client: ClientProfile,
        car: Car,
        start_date: date,
        end_date: date,
        pricing_strategy: str = 'combined'
    ) -> Rental:
        """
        Створює нову оренду з автоматичним розрахунком цін
        
        Args:
            client: Профіль клієнта
            car: Автомобіль для оренди
            start_date: Дата початку оренди
            end_date: Дата закінчення оренди
            pricing_strategy: Тип стратегії розрахунку ціни
        
        Returns:
            Створена оренда
        
        Raises:
            ValueError: Якщо автомобіль недоступний або дати некоректні
        """
        # Валідація
        if not car.is_available:
            raise ValueError(f"Автомобіль {car} недоступний для оренди")
        
        if start_date < date.today():
            raise ValueError("Дата початку не може бути в минулому")
        
        if end_date <= start_date:
            raise ValueError("Дата закінчення повинна бути після дати початку")
        
        # Розрахунок вартості
        strategy = PricingStrategyFactory.create_strategy(pricing_strategy)
        total_cost = strategy.calculate_price(car, start_date, end_date)
        daily_cost = car.daily_price
        
        # Розрахунок застави
        days = (end_date - start_date).days + 1
        deposit = cls.calculate_deposit(car, days)
        
        # Створення оренди
        # Якщо дата початку сьогодні або в минулому, статус 'active', інакше 'pending'
        rental_status = 'active' if start_date <= date.today() else 'pending'
        
        rental = Rental.objects.create(
            client=client,
            car=car,
            start_date=start_date,
            expected_end_date=end_date,
            deposit=deposit,
            daily_cost=daily_cost,
            total_cost=total_cost,
            status=rental_status
        )
        
        # Створення платежу застави
        Payment.objects.create(
            rental=rental,
            payment_type='deposit',
            amount=deposit
        )
        
        # Оновлення статусу авто
        car.status = 'rented'
        car.save()
        
        return rental
    
    @classmethod
    def validate_rental_dates(cls, start_date: date, end_date: date) -> tuple[bool, str]:
        """
        Валідує дати оренди.
        
        Args:
            start_date: Дата початку оренди
            end_date: Дата закінчення оренди
            
        Returns:
            tuple: (is_valid, error_message)
                - is_valid: True якщо дати валідні
                - error_message: Повідомлення про помилку (якщо є)
        """
        today = date.today()
        max_rental_days = 365
        
        if start_date < today:
            return False, "Дата початку не може бути в минулому"
        
        if end_date <= start_date:
            return False, "Дата закінчення повинна бути після дати початку"
        
        rental_days = (end_date - start_date).days
        if rental_days > max_rental_days:
            return False, f"Максимальна тривалість оренди - {max_rental_days} днів"
        
        if rental_days < 1:
            return False, "Мінімальна тривалість оренди - 1 день"
        
        return True, ""

