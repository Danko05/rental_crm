"""
GoF Pattern: Strategy
Визначає сімейство алгоритмів розрахунку вартості оренди,
інкапсулює кожен з них і робить їх взаємозамінними.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date, timedelta
from rental_app.models import Car


class PricingStrategy(ABC):
    """Абстрактна стратегія розрахунку ціни"""
    
    @abstractmethod
    def calculate_price(self, car: Car, start_date: date, end_date: date) -> Decimal:
        """Розраховує вартість оренди"""
        pass


class StandardPricingStrategy(PricingStrategy):
    """Стандартна стратегія: ціна залежить тільки від кількості днів"""
    
    def calculate_price(self, car: Car, start_date: date, end_date: date) -> Decimal:
        days = (end_date - start_date).days + 1
        return car.daily_price * Decimal(str(days))


class YearBasedPricingStrategy(PricingStrategy):
    """Стратегія з урахуванням року випуску (новіші авто дорожчі)"""
    
    def calculate_price(self, car: Car, start_date: date, end_date: date) -> Decimal:
        days = (end_date - start_date).days + 1
        current_year = date.today().year
        age = current_year - car.year
        
        # Коефіцієнт: новіші авто дорожчі
        if age <= 2:
            multiplier = Decimal('1.2')
        elif age <= 5:
            multiplier = Decimal('1.0')
        elif age <= 10:
            multiplier = Decimal('0.9')
        else:
            multiplier = Decimal('0.8')
        
        return car.daily_price * Decimal(str(days)) * multiplier


class DurationBasedPricingStrategy(PricingStrategy):
    """Стратегія зі знижками за тривалість оренди"""
    
    def calculate_price(self, car: Car, start_date: date, end_date: date) -> Decimal:
        days = (end_date - start_date).days + 1
        base_price = car.daily_price * Decimal(str(days))
        
        # Знижки за тривалість
        if days >= 30:
            discount = Decimal('0.15')  # 15% знижка
        elif days >= 14:
            discount = Decimal('0.10')  # 10% знижка
        elif days >= 7:
            discount = Decimal('0.05')  # 5% знижка
        else:
            discount = Decimal('0.0')
        
        return base_price * (Decimal('1.0') - discount)


class CombinedPricingStrategy(PricingStrategy):
    """Комбінована стратегія: рік + тривалість"""
    
    def _calculate_year_multiplier(self, age: int) -> tuple[Decimal, str]:
        """Розраховує коефіцієнт за рік """
        if age <= 2:
            return Decimal('1.2'), f"+20% (авто {age} років)"
        elif age <= 5:
            return Decimal('1.0'), "Без зміни (авто 3-5 років)"
        elif age <= 10:
            return Decimal('0.9'), f"-10% (авто {age} років)"
        else:
            return Decimal('0.8'), f"-20% (авто {age} років)"
    
    def _calculate_duration_discount(self, days: int) -> tuple[Decimal, str]:
        """Розраховує знижку за тривалість """
        if days >= 30:
            return Decimal('0.15'), "-15% (оренда 30+ днів)"
        elif days >= 14:
            return Decimal('0.10'), "-10% (оренда 14+ днів)"
        elif days >= 7:
            return Decimal('0.05'), "-5% (оренда 7+ днів)"
        else:
            return Decimal('0.0'), "Без знижки"
    
    def calculate_price(self, car: Car, start_date: date, end_date: date) -> Decimal:
        days = (end_date - start_date).days + 1
        current_year = date.today().year
        age = current_year - car.year
        
        year_multiplier, _ = self._calculate_year_multiplier(age)
        duration_discount, _ = self._calculate_duration_discount(days)
        
        base_price = car.daily_price * Decimal(str(days)) * year_multiplier
        return base_price * (Decimal('1.0') - duration_discount)
    
    def calculate_price_details(self, car: Car, start_date: date, end_date: date) -> dict:
        """Розраховує вартість оренди з деталями для відображення"""
        days = (end_date - start_date).days + 1
        current_year = date.today().year
        age = current_year - car.year
        
        # Базова ціна
        base_price = car.daily_price * Decimal(str(days))
        
        # Коефіцієнт за рік
        year_multiplier, year_description = self._calculate_year_multiplier(age)
        
        # Ціна з урахуванням року
        price_with_year = base_price * year_multiplier
        year_adjustment = price_with_year - base_price
        
        # Знижка за тривалість
        duration_discount, duration_description = self._calculate_duration_discount(days)
        
        # Фінальна ціна
        final_price = price_with_year * (Decimal('1.0') - duration_discount)
        duration_discount_amount = price_with_year * duration_discount
        
        return {
            'base_price': base_price,
            'days': days,
            'year_multiplier': year_multiplier,
            'year_description': year_description,
            'year_adjustment': year_adjustment,
            'price_with_year': price_with_year,
            'duration_discount': duration_discount,
            'duration_description': duration_description,
            'duration_discount_amount': duration_discount_amount,
            'final_price': final_price,
        }


class PricingStrategyFactory:
    """Factory для створення стратегій розрахунку ціни"""
    
    STRATEGIES = {
        'standard': StandardPricingStrategy,
        'year_based': YearBasedPricingStrategy,
        'duration_based': DurationBasedPricingStrategy,
        'combined': CombinedPricingStrategy,
    }
    
    @classmethod
    def create_strategy(cls, strategy_type: str = 'combined') -> PricingStrategy:
        """Створює стратегію розрахунку ціни"""
        strategy_class = cls.STRATEGIES.get(strategy_type, CombinedPricingStrategy)
        return strategy_class()
    
    @classmethod
    def get_default_strategy(cls) -> PricingStrategy:
        """Повертає стратегію за замовчуванням"""
        return cls.create_strategy('combined')

