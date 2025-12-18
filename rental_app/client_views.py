"""
Views для клієнтського інтерфейсу
Обробляють HTTP запити від клієнтів
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib import messages
from django.http import JsonResponse
from datetime import date
from rental_app.decorators import client_required
from rental_app.forms import (
    ClientRegistrationForm, 
    ClientProfileUpdateForm, 
    RentalForm, 
    CarSearchForm
)
from rental_app.models import Car, Rental, ClientProfile
from rental_app.services.rental_service import RentalService
from rental_app.services.car_service import CarService
from rental_app.patterns.pricing_strategy import PricingStrategyFactory
from rental_app.patterns.rental_factory import RentalFactory


def client_register(request):
    """
    Реєстрація нового клієнта.
    
    Якщо користувач вже зареєстрований як клієнт, перенаправляє на dashboard.
    """
    if request.user.is_authenticated and request.user.is_client:
        return redirect('client:dashboard')
    
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Реєстрація успішна! Тепер ви можете увійти.')
            return redirect('client:login')
    else:
        form = ClientRegistrationForm()
    
    return render(request, 'client/register.html', {'form': form})


def client_login(request):
    """
    Авторизація користувача (клієнта або адміністратора).
    
    Підтримує авторизацію як по email, так і по username.
    Автоматично перенаправляє на відповідний dashboard.
    """
    # Якщо вже авторизований, перенаправляємо
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_panel:dashboard')
        elif request.user.is_client:
            return redirect('client:dashboard')
    
    if request.method == 'POST':
        email_or_username = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email_or_username or not password:
            messages.error(request, 'Будь ласка, заповніть всі поля')
            return render(request, 'client/login.html')
        
        # Спробуємо автентифікувати по введеному значенню (email або username)
        user = authenticate(request, username=email_or_username, password=password)
        
        # Якщо не вдалося, спробуємо знайти користувача по email
        if user is None:
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            login(request, user)
            # Перенаправлення залежно від типу користувача
            if user.is_superuser:
                return redirect('admin_panel:dashboard')
            elif user.is_client:
                return redirect('client:dashboard')
            else:
                messages.error(request, 'У вас немає доступу до цієї системи')
        else:
            messages.error(request, 'Невірний email/username або пароль')
    
    return render(request, 'client/login.html')


@client_required
def client_dashboard(request):
    """
    Особистий кабінет клієнта.
    
    Показує інформацію про клієнта та його оренди.
    """
    client = request.user.client_profile
    rentals = RentalService.get_client_rentals(client)
    
    # Активні оренди включають active та pending (які вже почалися)
    from django.utils import timezone
    today = timezone.now().date()
    active_rentals = rentals.filter(
        status__in=['active', 'pending'],
        start_date__lte=today
    )
    
    context = {
        'client': client,
        'rentals': rentals,
        'active_rentals': active_rentals,
        'completed_rentals': rentals.filter(status='completed'),
    }
    
    return render(request, 'client/dashboard.html', context)


@client_required
def client_profile_edit(request):
    """
    Редагування профілю клієнта.
    
    Дозволяє клієнту оновити свої дані (ПІБ, адреса, телефон).
    """
    client = request.user.client_profile
    
    if request.method == 'POST':
        form = ClientProfileUpdateForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль оновлено!')
            return redirect('client:dashboard')
    else:
        form = ClientProfileUpdateForm(instance=client)
    
    return render(request, 'client/profile_edit.html', {'form': form})


def car_catalog(request):
    """
    Каталог доступних автомобілів.
    
    Підтримує фільтрацію за маркою, ціною та доступністю на конкретні дати оренди.
    Показує всі автомобілі, але позначає зайняті на вибрані дати.
    """
    form = CarSearchForm(request.GET)
    cars = None
    rental_start_date = None
    rental_end_date = None
    
    if form.is_valid():
        rental_start_date = form.cleaned_data.get('rental_start_date')
        rental_end_date = form.cleaned_data.get('rental_end_date')
        brand = form.cleaned_data.get('brand')
        price_from = form.cleaned_data.get('price_from')
        price_to = form.cleaned_data.get('price_to')
        
        # Показуємо всі автомобілі (не фільтруємо по доступності)
        cars = Car.objects.all()
        
        # Застосовуємо інші фільтри
        if brand:
            cars = cars.filter(brand__icontains=brand)
        if price_from:
            cars = cars.filter(daily_price__gte=price_from)
        if price_to:
            cars = cars.filter(daily_price__lte=price_to)
    else:
        # Якщо форма не валідна, спробуємо витягнути дати з GET параметрів
        rental_start_date_str = request.GET.get('rental_start_date')
        rental_end_date_str = request.GET.get('rental_end_date')
        
        if rental_start_date_str:
            try:
                rental_start_date = date.fromisoformat(rental_start_date_str)
            except (ValueError, TypeError):
                rental_start_date = None
        
        if rental_end_date_str:
            try:
                rental_end_date = date.fromisoformat(rental_end_date_str)
            except (ValueError, TypeError):
                rental_end_date = None
        
        # Якщо форма не валідна, показуємо всі автомобілі
        cars = Car.objects.all()
    
    # Створюємо список з інформацією про доступність кожного автомобіля
    # Перевіряємо, чи обидві дати дійсно введені
    has_dates = rental_start_date is not None and rental_end_date is not None
    
    cars_with_availability = []
    for car in cars:
        is_busy = False
        if has_dates:
            is_busy = CarService.is_car_busy_for_dates(car, rental_start_date, rental_end_date)
        
        cars_with_availability.append({
            'car': car,
            'is_busy': is_busy,
        })
    
    context = {
        'cars_with_availability': cars_with_availability,
        'form': form,
        'rental_start_date': rental_start_date,
        'rental_end_date': rental_end_date,
        'has_dates': has_dates,
    }
    
    return render(request, 'client/catalog.html', context)


def calculate_rental_price(request, car_id):
    """
    API endpoint для розрахунку вартості оренди та застави.
    
    Використовується для відображення сум в реальному часі.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        car = get_object_or_404(Car, id=car_id)
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not start_date_str or not end_date_str:
            return JsonResponse({'error': 'Missing dates'}, status=400)
        
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        
        # Валідація дат
        if start_date < date.today():
            return JsonResponse({'error': 'Дата початку не може бути в минулому'}, status=400)
        
        if end_date <= start_date:
            return JsonResponse({'error': 'Дата закінчення повинна бути після дати початку'}, status=400)
        
        # Розрахунок вартості оренди
        strategy = PricingStrategyFactory.get_default_strategy()
        total_cost = strategy.calculate_price(car, start_date, end_date)
        
        # Отримуємо деталі розрахунку, якщо стратегія підтримує це
        details = None
        if hasattr(strategy, 'calculate_price_details'):
            details = strategy.calculate_price_details(car, start_date, end_date)
        
        # Розрахунок застави (30% від вартості)
        days = (end_date - start_date).days + 1
        deposit = RentalFactory.calculate_deposit(car, days)
        
        response_data = {
            'success': True,
            'total_cost': str(total_cost),
            'deposit': str(deposit),
            'days': days,
            'daily_price': str(car.daily_price)
        }
        
        # Додаємо деталі, якщо вони є
        if details:
            response_data['details'] = {
                'base_price': str(details['base_price']),
                'year_description': details['year_description'],
                'year_adjustment': str(details['year_adjustment']),
                'price_with_year': str(details['price_with_year']),
                'duration_description': details['duration_description'],
                'duration_discount_amount': str(details['duration_discount_amount']),
                'final_price': str(details['final_price']),
            }
        
        return JsonResponse(response_data)
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Помилка розрахунку'}, status=500)


def car_detail(request, car_id):
    """
    Детальна інформація про автомобіль.
    
    Для авторизованих клієнтів показує форму для оформлення оренди.
    """
    car = get_object_or_404(Car, id=car_id)
    rental_form = None
    
    # Якщо клієнт авторизований, показуємо форму оренди
    if request.user.is_authenticated and request.user.is_client:
        if request.method == 'POST':
            rental_form = RentalForm(request.POST)
            if rental_form.is_valid():
                try:
                    client = request.user.client_profile
                    rental = RentalService.create_rental(
                        client=client,
                        car=car,
                        start_date=rental_form.cleaned_data['start_date'],
                        end_date=rental_form.cleaned_data['expected_end_date']
                    )
                    messages.success(
                        request, 
                        f'Оренда оформлена успішно! Застава: {rental.deposit} грн, Вартість: {rental.total_cost} грн'
                    )
                    return redirect('client:my_rentals')
                except ValueError as e:
                    messages.error(request, str(e))
                    rental_form = RentalForm(request.POST)  # Зберігаємо введені дані
        else:
            rental_form = RentalForm()
    
    context = {
        'car': car,
        'rental_form': rental_form,
    }
    
    return render(request, 'client/car_detail.html', context)


@client_required
def my_rentals(request):
    """
    Список всіх оренд клієнта.
    
    Автоматично оновлює статуси прострочених оренд.
    Показує активні оренди на початку, а також всі минулі оренди.
    """
    client = request.user.client_profile
    rentals = RentalService.get_client_rentals(client)
    
    # Оновлюємо прострочені оренди
    RentalService.update_overdue_rentals()
    
    # Розділяємо оренди за статусами
    # Активні оренди - це active та pending, які вже почалися
    from django.utils import timezone
    from django.db.models import Q
    today = timezone.now().date()
    active_rentals = rentals.filter(
        status__in=['active', 'pending'],
        start_date__lte=today
    )
    # Всі минулі оренди - завершені та прострочені
    past_rentals = rentals.filter(status__in=['completed', 'overdue'])
    
    context = {
        'rentals': rentals,
        'active_rentals': active_rentals,
        'past_rentals': past_rentals,
    }
    
    return render(request, 'client/my_rentals.html', context)


@client_required
def rental_detail(request, rental_id):
    """
    Детальна інформація про конкретну оренду.
    
    Показує всю інформацію про оренду, штрафи та платежі.
    """
    client = request.user.client_profile
    rental = get_object_or_404(Rental, id=rental_id, client=client)
    
    context = {
        'rental': rental,
        'fines': rental.fines.all(),
        'payments': rental.payments.all(),
    }
    
    return render(request, 'client/rental_detail.html', context)
