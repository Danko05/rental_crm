"""
Views для адмінського інтерфейсу
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from rental_app.decorators import admin_required
from rental_app.admin_forms import CarForm, CompleteRentalForm, ClientProfileAdminForm, CarTypeForm
from rental_app.models import Car, Rental, ClientProfile, CarType
from rental_app.services.rental_service import RentalService
from rental_app.services.car_service import CarService
from rental_app.services.statistics_service import StatisticsService


@admin_required
def admin_dashboard(request):
    """Головна панель адміністратора"""
    stats = StatisticsService.get_dashboard_stats()
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'admin/dashboard.html', context)


@admin_required
def admin_cars(request):
    """Управління автопарком"""
    cars = Car.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    
    if status_filter:
        cars = cars.filter(status=status_filter)
    
    context = {
        'cars': cars,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/cars.html', context)


@admin_required
def admin_car_add(request):
    """
    Додавання нового автомобіля до автопарку.
    
    Підтримує створення нового типу автомобіля прямо в формі.
    """
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save()
            # Повідомлення про створення нового типу (якщо було)
            new_type_name = form.cleaned_data.get('new_car_type', '').strip()
            if new_type_name:
                messages.success(
                    request, 
                    f'Автомобіль додано! Створено новий тип: {car.car_type.name}'
                )
            else:
                messages.success(request, 'Автомобіль додано!')
            return redirect('admin_panel:cars')
    else:
        form = CarForm()
    
    return render(request, 'admin/car_form.html', {'form': form, 'action': 'Додати'})


@admin_required
def admin_car_edit(request, car_id):
    """Редагування автомобіля"""
    car = get_object_or_404(Car, id=car_id)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, 'Автомобіль оновлено!')
            return redirect('admin_panel:cars')
    else:
        form = CarForm(instance=car)
    
    return render(request, 'admin/car_form.html', {'form': form, 'action': 'Редагувати', 'car': car})


@admin_required
def admin_car_delete(request, car_id):
    """Видалення автомобіля"""
    car = get_object_or_404(Car, id=car_id)
    
    # Перевіряємо всі оренди (не тільки активні)
    all_rentals = car.rentals.all()
    active_rentals = car.rentals.filter(status__in=['active', 'pending', 'overdue'])
    
    # Якщо є активні оренди, забороняємо видалення
    if active_rentals.exists():
        messages.error(
            request, 
            f'Неможливо видалити автомобіль з активними орендами! '
            f'Знайдено {active_rentals.count()} активних оренд.'
        )
        return redirect('admin_panel:cars')
    
    # Якщо є будь-які оренди (навіть завершені), показуємо попередження
    if all_rentals.exists():
        if request.method == 'POST':
            try:
                car.delete()
                messages.success(request, 'Автомобіль видалено!')
                return redirect('admin_panel:cars')
            except Exception as e:
                messages.error(
                    request, 
                    f'Неможливо видалити автомобіль! '
                    f'Автомобіль має {all_rentals.count()} оренд в історії. '
                    f'Спочатку видаліть або завершіть всі оренди.'
                )
                return redirect('admin_panel:cars')
        
        # Показуємо форму з попередженням
        return render(request, 'admin/car_delete.html', {
            'car': car,
            'rentals_count': all_rentals.count(),
            'has_rentals': True
        })
    
    # Якщо оренд немає, видаляємо без попереджень
    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Автомобіль видалено!')
        return redirect('admin_panel:cars')
    
    return render(request, 'admin/car_delete.html', {
        'car': car,
        'rentals_count': 0,
        'has_rentals': False
    })


@admin_required
def admin_car_financial(request, car_id):
    """Фінансовий звіт по автомобілю"""
    car = get_object_or_404(Car, id=car_id)
    report = CarService.get_car_financial_report(car)
    
    return render(request, 'admin/car_financial.html', report)


@admin_required
def admin_cars_occupancy(request):
    """Звіт по зайнятості автомобілів"""
    report = CarService.get_cars_occupancy_report()
    
    return render(request, 'admin/cars_occupancy.html', {'report': report})


@admin_required
def admin_clients(request):
    """Управління клієнтами"""
    clients = ClientProfile.objects.all().order_by('-created_at')
    search = request.GET.get('search')
    
    if search:
        clients = clients.filter(
            Q(full_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    context = {
        'clients': clients,
        'search': search,
    }
    
    return render(request, 'admin/clients.html', context)


@admin_required
def admin_client_detail(request, client_id):
    """Детальна інформація про клієнта"""
    client = get_object_or_404(ClientProfile, id=client_id)
    rentals = client.rentals.all().order_by('-created_at')
    
    context = {
        'client': client,
        'rentals': rentals,
    }
    
    return render(request, 'admin/client_detail.html', context)


@admin_required
def admin_client_edit(request, client_id):
    """Редагування клієнта"""
    client = get_object_or_404(ClientProfile, id=client_id)
    
    if request.method == 'POST':
        form = ClientProfileAdminForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клієнта оновлено!')
            return redirect('admin_panel:clients')
    else:
        form = ClientProfileAdminForm(instance=client)
    
    return render(request, 'admin/client_form.html', {'form': form, 'client': client})


@admin_required
def admin_client_delete(request, client_id):
    """Видалення клієнта"""
    client = get_object_or_404(ClientProfile, id=client_id)
    
    if request.method == 'POST':
        client.user.delete()
        messages.success(request, 'Клієнта видалено!')
        return redirect('admin_panel:clients')
    
    return render(request, 'admin/client_delete.html', {'client': client})


@admin_required
def admin_rentals(request):
    """
    Управління орендами.
    
    Автоматично оновлює статуси оренд перед відображенням.
    """
    # Оновлюємо статуси оренд (pending -> active, active -> overdue)
    RentalService.update_overdue_rentals()
    
    rentals = Rental.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    client_id = request.GET.get('client_id')
    
    if status_filter:
        # Для фільтра "active" показуємо також pending, які вже почалися
        if status_filter == 'active':
            from django.utils import timezone
            today = timezone.now().date()
            rentals = rentals.filter(
                status__in=['active', 'pending'],
                start_date__lte=today
            )
        else:
            rentals = rentals.filter(status=status_filter)
    if client_id:
        rentals = rentals.filter(client_id=client_id)
    
    context = {
        'rentals': rentals,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/rentals.html', context)


@admin_required
def admin_rental_detail(request, rental_id):
    """Детальна інформація про оренду"""
    rental = get_object_or_404(Rental, id=rental_id)
    
    context = {
        'rental': rental,
        'fines': rental.fines.all(),
        'payments': rental.payments.all(),
    }
    
    return render(request, 'admin/rental_detail.html', context)


@admin_required
def admin_rental_complete(request, rental_id):
    """
    Завершення оренди.
    
    Дозволяє завершити оренду зі статусом 'active', 'overdue' або 'pending'.
    """
    rental = get_object_or_404(Rental, id=rental_id)
    
    # Перевірка, чи можна завершити оренду
    if rental.status == 'completed':
        messages.warning(request, 'Ця оренда вже завершена')
        return redirect('admin_panel:rental_detail', rental_id=rental.id)
    
    if request.method == 'POST':
        form = CompleteRentalForm(request.POST)
        if form.is_valid():
            try:
                rental, total_fines, refund = RentalService.complete_rental(
                    rental=rental,
                    actual_end_date=form.cleaned_data['actual_end_date'],
                    damage_level=form.cleaned_data['damage_level'],
                    late_days=form.cleaned_data['late_days']
                )
                messages.success(
                    request,
                    f'Оренда завершена! Штрафи: {total_fines} грн, Повернення: {refund} грн'
                )
                return redirect('admin_panel:rental_detail', rental_id=rental.id)
            except Exception as e:
                messages.error(request, f'Помилка: {str(e)}')
    else:
        form = CompleteRentalForm()
        # Встановлюємо дату повернення за замовчуванням (сьогодні або очікувану дату)
        from django.utils import timezone
        today = timezone.now().date()
        if rental.expected_end_date <= today:
            form.fields['actual_end_date'].initial = today
        else:
            form.fields['actual_end_date'].initial = rental.expected_end_date
    
    context = {
        'rental': rental,
        'form': form,
    }
    
    return render(request, 'admin/rental_complete.html', context)


@admin_required
def admin_statistics(request):
    """Фінансова статистика"""
    stats = StatisticsService.get_dashboard_stats()
    
    # Додаткова статистика
    from datetime import timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    revenue_by_period = StatisticsService.get_revenue_by_period(last_30_days, today)
    avg_rental_cost = StatisticsService.get_average_rental_cost()
    
    context = {
        'stats': stats,
        'revenue_by_period': revenue_by_period,
        'avg_rental_cost': avg_rental_cost,
    }
    
    return render(request, 'admin/statistics.html', context)


@admin_required
def admin_car_types(request):
    """Управління типами автомобілів"""
    car_types = CarType.objects.all().order_by('name')
    
    context = {
        'car_types': car_types,
    }
    
    return render(request, 'admin/car_types.html', context)


@admin_required
def admin_car_type_add(request):
    """Додавання типу автомобіля"""
    if request.method == 'POST':
        form = CarTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип автомобіля додано!')
            return redirect('admin_panel:car_types')
    else:
        form = CarTypeForm()
    
    return render(request, 'admin/car_type_form.html', {'form': form, 'action': 'Додати'})


@admin_required
def admin_car_type_edit(request, type_id):
    """Редагування типу автомобіля"""
    car_type = get_object_or_404(CarType, id=type_id)
    
    if request.method == 'POST':
        form = CarTypeForm(request.POST, instance=car_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип автомобіля оновлено!')
            return redirect('admin_panel:car_types')
    else:
        form = CarTypeForm(instance=car_type)
    
    return render(request, 'admin/car_type_form.html', {'form': form, 'action': 'Редагувати', 'car_type': car_type})


@admin_required
def admin_car_type_delete(request, type_id):
    """Видалення типу автомобіля"""
    car_type = get_object_or_404(CarType, id=type_id)
    
    # Перевірка, чи використовується тип
    if car_type.car_set.exists():
        messages.error(request, 'Неможливо видалити тип, який використовується в автомобілях!')
        return redirect('admin_panel:car_types')
    
    if request.method == 'POST':
        car_type.delete()
        messages.success(request, 'Тип автомобіля видалено!')
        return redirect('admin_panel:car_types')
    
    return render(request, 'admin/car_type_delete.html', {'car_type': car_type})

