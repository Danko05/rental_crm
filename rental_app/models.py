"""
Моделі даних для системи прокату автомобілів
Використовуються принципи SOLID та GRASP
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date


class User(AbstractUser):
    """Користувач системи (може бути клієнтом або адміністратором)"""
    is_client = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'


class ClientProfile(models.Model):
    """Профіль клієнта - додаткова інформація"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    full_name = models.CharField('ПІБ', max_length=200)
    address = models.TextField('Адреса')
    phone = models.CharField('Телефон', max_length=20)
    is_blocked = models.BooleanField('Заблокований', default=False)
    created_at = models.DateTimeField('Дата реєстрації', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Профіль клієнта'
        verbose_name_plural = 'Профілі клієнтів'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.full_name
    
    @property
    def total_rentals(self):
        """Кількість оренд клієнта"""
        return self.rentals.count()


class CarType(models.Model):
    """Тип автомобіля (седан, кросовер, мінівен тощо)"""
    name = models.CharField('Назва типу', max_length=50, unique=True)
    description = models.TextField('Опис', blank=True)
    
    class Meta:
        verbose_name = 'Тип автомобіля'
        verbose_name_plural = 'Типи автомобілів'
    
    def __str__(self):
        return self.name


class Car(models.Model):
    """Автомобіль в автопарку"""
    STATUS_CHOICES = [
        ('available', 'Доступний'),
        ('rented', 'Орендований'),
        ('maintenance', 'На ремонті'),
        ('unavailable', 'Недоступний'),
    ]
    
    brand = models.CharField('Марка', max_length=50)
    model = models.CharField('Модель', max_length=50)
    car_type = models.ForeignKey(CarType, on_delete=models.PROTECT, verbose_name='Тип')
    year = models.IntegerField('Рік випуску', validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    daily_price = models.DecimalField('Ціна за добу', max_digits=10, decimal_places=2, 
                                      validators=[MinValueValidator(Decimal('0.01'))])
    photo = models.ImageField('Фото', upload_to='cars/', blank=True, null=True)
    description = models.TextField('Опис', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField('Дата додавання', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Автомобіль'
        verbose_name_plural = 'Автомобілі'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
    
    @property
    def total_revenue(self):
        """Загальна виручка від оренди цього авто"""
        return self.rentals.filter(status='completed').aggregate(
            total=models.Sum('total_cost')
        )['total'] or Decimal('0.00')
    
    @property
    def total_rentals_count(self):
        """Кількість оренд"""
        return self.rentals.filter(status='completed').count()
    
    @property
    def is_available(self):
        """Чи доступний автомобіль для оренди"""
        return self.status == 'available'


class Rental(models.Model):
    """Оренда автомобіля"""
    STATUS_CHOICES = [
        ('pending', 'Очікує підтвердження'),
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('overdue', 'Прострочена'),
        ('cancelled', 'Скасована'),
    ]
    
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='rentals', verbose_name='Клієнт')
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name='rentals', verbose_name='Автомобіль')
    start_date = models.DateField('Дата видачі')
    expected_end_date = models.DateField('Очікувана дата повернення')
    actual_end_date = models.DateField('Фактична дата повернення', null=True, blank=True)
    deposit = models.DecimalField('Застава', max_digits=10, decimal_places=2, 
                                  validators=[MinValueValidator(Decimal('0.01'))])
    daily_cost = models.DecimalField('Вартість за добу', max_digits=10, decimal_places=2)
    total_cost = models.DecimalField('Загальна вартість', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    damage_level = models.IntegerField('Рівень пошкоджень', default=0, 
                                       validators=[MinValueValidator(0), MaxValueValidator(3)])
    late_days = models.IntegerField('Днів запізнення', default=0)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Оренда'
        verbose_name_plural = 'Оренди'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Оренда {self.car} клієнтом {self.client.full_name}"
    
    @property
    def days_rented(self):
        """Кількість днів оренди"""
        end_date = self.actual_end_date or date.today()
        return (end_date - self.start_date).days + 1
    
    @property
    def is_overdue(self):
        """Чи прострочена оренда"""
        if self.status == 'active' and date.today() > self.expected_end_date:
            return True
        return False


class Fine(models.Model):
    """Штраф за пошкодження або запізнення"""
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='fines', verbose_name='Оренда')
    reason = models.CharField('Причина', max_length=200)
    amount = models.DecimalField('Сума штрафу', max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField('Дата нарахування', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Штраф {self.amount} грн за {self.reason}"


class Payment(models.Model):
    """Платіж (застава, повернення застави, доплата)"""
    PAYMENT_TYPE_CHOICES = [
        ('deposit', 'Застава'),
        ('refund', 'Повернення застави'),
        ('additional', 'Доплата'),
        ('fine', 'Оплата штрафу'),
    ]
    
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='payments', verbose_name='Оренда')
    payment_type = models.CharField('Тип платежу', max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField('Сума', max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField('Дата платежу', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Платіж'
        verbose_name_plural = 'Платежі'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount} грн"

