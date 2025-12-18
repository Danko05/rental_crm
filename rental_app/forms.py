"""
Форми для системи прокату автомобілів
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import date
from rental_app.models import User, ClientProfile, Car, Rental, CarType


class ClientRegistrationForm(UserCreationForm):
    """
    Форма реєстрації нового клієнта.
    
    Створює користувача та профіль клієнта одночасно.
    """
    full_name = forms.CharField(
        label='ПІБ',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Повне ім\'я'
        })
    )
    address = forms.CharField(
        label='Адреса',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3, 
            'placeholder': 'Ваша адреса'
        })
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+380XXXXXXXXX'
        })
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'email@example.com'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'full_name', 'address', 'phone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Додаємо стилі до полів паролів
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        """Валідація email на унікальність"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Користувач з таким email вже існує')
        return email
    
    def clean_phone(self):
        """Валідація номера телефону"""
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError('Номер телефону обов\'язковий')
        return phone
    
    def save(self, commit=True):
        """
        Збереження користувача та створення профілю клієнта.
        
        Args:
            commit: Чи зберігати в базу даних
            
        Returns:
            Створений користувач
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Використовуємо email як username
        user.is_client = True
        
        if commit:
            user.save()
            ClientProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone']
            )
        
        return user


class ClientProfileUpdateForm(forms.ModelForm):
    """Форма оновлення профілю клієнта"""
    
    class Meta:
        model = ClientProfile
        fields = ('full_name', 'address', 'phone')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_phone(self):
        """Валідація номера телефону"""
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError('Номер телефону обов\'язковий')
        return phone


class RentalForm(forms.ModelForm):
    """
    Форма створення оренди.
    
    Валідує дати та перевіряє їх коректність.
    """
    start_date = forms.DateField(
        label='Дата видачі',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    expected_end_date = forms.DateField(
        label='Очікувана дата повернення',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = Rental
        fields = ('start_date', 'expected_end_date')
    
    def clean(self):
        """
        Валідація дат оренди.
        
        Перевіряє:
        - Дата початку не в минулому
        - Дата закінчення після дати початку
        - Максимальна тривалість оренди
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('expected_end_date')
        
        if not start_date or not end_date:
            return cleaned_data
        
        today = date.today()
        max_rental_days = 365
        
        # Перевірка дати початку
        if start_date < today:
            raise ValidationError("Дата початку не може бути в минулому")
        
        # Перевірка дати закінчення
        if end_date <= start_date:
            raise ValidationError("Дата закінчення повинна бути після дати початку")
        
        # Перевірка максимальної тривалості
        rental_days = (end_date - start_date).days
        if rental_days > max_rental_days:
            raise ValidationError(
                f"Максимальна тривалість оренди - {max_rental_days} днів"
            )
        
        return cleaned_data


class CarSearchForm(forms.Form):
    """
    Форма пошуку автомобілів.
    
    Дозволяє фільтрувати автомобілі за маркою, ціною та доступністю на дати оренди.
    """
    brand = forms.CharField(
        label='Марка',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Марка авто'
        })
    )
    price_from = forms.DecimalField(
        label='Ціна від',
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    price_to = forms.DecimalField(
        label='Ціна до',
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    rental_start_date = forms.DateField(
        label='Дата початку оренди',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )
    rental_end_date = forms.DateField(
        label='Дата закінчення оренди',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )
    
    def clean(self):
        """Валідація дат оренди та цін"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('rental_start_date')
        end_date = cleaned_data.get('rental_end_date')
        price_from = cleaned_data.get('price_from')
        price_to = cleaned_data.get('price_to')
        
        if start_date and end_date:
            if start_date < date.today():
                raise ValidationError('Дата початку не може бути в минулому')
            if end_date <= start_date:
                raise ValidationError('Дата закінчення повинна бути після дати початку')
        
        if price_from and price_to:
            if price_from > price_to:
                raise ValidationError('Ціна "від" не може бути більше ціни "до"')
        
        return cleaned_data
    
    def clean(self):
        """Валідація дат оренди"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('rental_start_date')
        end_date = cleaned_data.get('rental_end_date')
        
        if start_date and end_date:
            if start_date < date.today():
                raise ValidationError('Дата початку не може бути в минулому')
            if end_date <= start_date:
                raise ValidationError('Дата закінчення повинна бути після дати початку')
        
        return cleaned_data
