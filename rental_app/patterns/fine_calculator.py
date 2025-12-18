"""
GoF Pattern: Strategy для розрахунку штрафів
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from rental_app.models import Rental


class FineCalculationStrategy(ABC):
    """Абстрактна стратегія розрахунку штрафів"""
    
    @abstractmethod
    def calculate_damage_fine(self, rental: Rental, damage_level: int) -> Decimal:
        """Розраховує штраф за пошкодження"""
        pass
    
    @abstractmethod
    def calculate_late_fine(self, rental: Rental, late_days: int) -> Decimal:
        """Розраховує штраф за запізнення"""
        pass


class StandardFineStrategy(FineCalculationStrategy):
    """Стандартна стратегія розрахунку штрафів"""
    
    DAMAGE_MULTIPLIERS = {
        0: Decimal('0.0'),      # Без пошкоджень
        1: Decimal('0.1'),      # Легкі пошкодження - 10% від застави
        2: Decimal('0.3'),      # Середні пошкодження - 30% від застави
        3: Decimal('0.5'),      # Серйозні пошкодження - 50% від застави
    }
    
    LATE_FINE_PER_DAY = Decimal('500.00')  # Штраф за день запізнення
    
    def calculate_damage_fine(self, rental: Rental, damage_level: int) -> Decimal:
        """Розраховує штраф за пошкодження"""
        if damage_level not in self.DAMAGE_MULTIPLIERS:
            damage_level = 0
        
        multiplier = self.DAMAGE_MULTIPLIERS[damage_level]
        return rental.deposit * multiplier
    
    def calculate_late_fine(self, rental: Rental, late_days: int) -> Decimal:
        """Розраховує штраф за запізнення"""
        if late_days <= 0:
            return Decimal('0.00')
        
        return self.LATE_FINE_PER_DAY * Decimal(str(late_days))


class FineCalculator:
    """Калькулятор штрафів (Facade pattern)"""
    
    def __init__(self, strategy: FineCalculationStrategy = None):
        self.strategy = strategy or StandardFineStrategy()
    
    def calculate_total_fines(self, rental: Rental, damage_level: int, late_days: int) -> Decimal:
        """Розраховує загальну суму штрафів"""
        damage_fine = self.strategy.calculate_damage_fine(rental, damage_level)
        late_fine = self.strategy.calculate_late_fine(rental, late_days)
        return damage_fine + late_fine
    
    def calculate_refund(self, rental: Rental, total_fines: Decimal) -> Decimal:
        """Розраховує суму повернення застави після вирахування штрафів"""
        refund = rental.deposit - total_fines
        return max(refund, Decimal('0.00'))  # Не може бути від'ємним

