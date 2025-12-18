"""
Форми для адмінського інтерфейсу
"""
from django import forms
from rental_app.models import Car, Rental, ClientProfile, Fine, CarType


class CarTypeForm(forms.ModelForm):
    """Форма для додавання/редагування типу автомобіля"""
    
    class Meta:
        model = CarType
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_name(self):
        """Валідація назви типу"""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Назва типу не може бути порожньою')
        return name


class CarForm(forms.ModelForm):
    """
    Форма для додавання/редагування автомобіля.
    
    Дозволяє швидко створити новий тип автомобіля прямо в формі.
    """
    new_car_type = forms.CharField(
        label='Або створіть новий тип',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Назва нового типу'
        })
    )
    
    class Meta:
        model = Car
        fields = '__all__'
        widgets = {
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'car_type': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'daily_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Ініціалізація форми з перевіркою наявності типів"""
        super().__init__(*args, **kwargs)
        # Якщо типів немає, створюємо базовий тип
        if not CarType.objects.exists():
            CarType.objects.get_or_create(
                name='Седан', 
                defaults={'description': 'Класичний легковий автомобіль'}
            )
    
    def clean(self):
        """
        Валідація та обробка даних форми.
        
        Якщо введено новий тип, створює його автоматично.
        """
        cleaned_data = super().clean()
        new_car_type_name = cleaned_data.get('new_car_type', '').strip()
        car_type = cleaned_data.get('car_type')
        
        # Якщо введено новий тип і не вибрано існуючий
        if new_car_type_name and not car_type:
            car_type, created = CarType.objects.get_or_create(
                name=new_car_type_name,
                defaults={'description': f'Тип автомобіля: {new_car_type_name}'}
            )
            cleaned_data['car_type'] = car_type
        
        # Перевірка наявності типу
        if not cleaned_data.get('car_type'):
            raise forms.ValidationError(
                'Необхідно вибрати або створити тип автомобіля'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Збереження автомобіля"""
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class CompleteRentalForm(forms.Form):
    """Форма завершення оренди з розрахунком штрафів"""
    
    actual_end_date = forms.DateField(
        label='Фактична дата повернення',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    damage_level = forms.IntegerField(
        label='Рівень пошкоджень (0-3)',
        min_value=0,
        max_value=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='0 - без пошкоджень, 1 - легкі, 2 - середні, 3 - серйозні'
    )
    late_days = forms.IntegerField(
        label='Днів запізнення',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean_actual_end_date(self):
        """Валідація дати повернення"""
        actual_end_date = self.cleaned_data.get('actual_end_date')
        if actual_end_date:
            from datetime import date
            if actual_end_date < date.today():
                raise forms.ValidationError(
                    'Дата повернення не може бути в минулому'
                )
        return actual_end_date


class ClientProfileAdminForm(forms.ModelForm):
    """Форма редагування профілю клієнта (для адміністратора)"""
    
    class Meta:
        model = ClientProfile
        fields = '__all__'
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_blocked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_phone(self):
        """Валідація номера телефону"""
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Номер телефону обов\'язковий')
        return phone
