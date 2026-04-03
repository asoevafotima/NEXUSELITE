# permissions.py

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from users.models import Users


ROLE_PERMISSIONS = {
    'Admin': {
        'view_resume', 'add_resume', 'change_resume', 'delete_resume',
        'view_serviceorder', 'delete_serviceorder',
        'view_feedback', 'delete_feedback',
    },
    'Specialist': {
        'view_resume', 'add_resume', 'change_resume', 'delete_resume',
        'view_serviceorder',
    },
    'Customer': {
        'view_resume',
        'add_serviceorder', 'view_serviceorder',
        'add_feedback',
    },
}


def get_logged_in_user(request):
    if hasattr(request, 'current_user'):
        return request.current_user

    user_id = request.session.get('user_id')
    if not user_id:
        request.current_user = None
        return None

    user = Users.objects.filter(id=user_id, is_email_verified=True).first()
    if not user:
        request.session.flush()
        request.current_user = None
        return None

    request.current_user = user
    return user


def get_user_role(user):
    def get_user_role(user):
        if not user:
            return None

        for role_name in ['Admin', 'Specialist', 'Customer']:
            if user.groups.filter(name=role_name).exists():
             return role_name
    return None


def user_has_perm(user, permission):
    """
    Проверяет право пользователя через нашу таблицу ROLE_PERMISSIONS.
    Не использует Django's has_perm() — он не работает с кастомными сессиями.
    """
    role = get_user_role(user)
    if not role:
        return False
    return permission in ROLE_PERMISSIONS.get(role, set())


def build_permission_flags(user):
    """Флаги для шаблонов"""
    role = get_user_role(user)
    return {
        'can_view_resume':   user_has_perm(user, 'view_resume'),
        'can_add_resume':    user_has_perm(user, 'add_resume'),
        'can_edit_resume':   user_has_perm(user, 'change_resume'),
        'can_delete_resume': user_has_perm(user, 'delete_resume'),
        'can_view_orders':   user_has_perm(user, 'view_serviceorder'),
        'can_add_orders':    user_has_perm(user, 'add_serviceorder'),
        'can_add_feedback':  user_has_perm(user, 'add_feedback'),
        'is_admin':          role == 'Admin',
        'is_specialist':     role == 'Specialist',
        'is_customer':       role == 'Customer',
    }



def session_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_logged_in_user(request):
            messages.error(request, 'Пожалуйста, войдите и подтвердите email.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = get_logged_in_user(request)
            if not user:
                return redirect('login')
            if get_user_role(user) not in role_names:
                messages.error(request, 'Доступ запрещён для вашей роли.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = get_logged_in_user(request)
            if not user:
                messages.error(request, 'Сначала войдите в систему.')
                return redirect('login')
            if not user_has_perm(user, permission_name):
                messages.error(request, 'У вас нет прав для этого действия.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator