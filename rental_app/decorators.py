"""
Декоратори для перевірки прав доступу
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def client_required(view_func):
    """Перевіряє, чи користувач є клієнтом"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_client or request.user.is_superuser:
            return redirect('client:login')
        if not hasattr(request.user, 'client_profile'):
            return redirect('client:register')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Перевіряє, чи користувач є адміністратором"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('client:login')
        return view_func(request, *args, **kwargs)
    return wrapper

