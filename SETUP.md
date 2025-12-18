# Інструкція з налаштування проекту

## Крок 1: Встановлення залежностей

```bash
pip install -r requirements.txt
```

## Крок 2: Налаштування бази даних

```bash
python manage.py makemigrations
python manage.py migrate
```

## Крок 3: Створення суперкористувача (адміністратора)

```bash
python manage.py createsuperuser
```

Введіть:
- Email (буде використовуватися як username)
- Пароль



## Крок 4: Запуск сервера

```bash
python manage.py runserver
```


