from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import Users
from .forms import (
    LoginForm,
    RegistrationForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    ChangePasswordForm,
)


def get_logged_in_user(request):
    if hasattr(request, '_cached_current_user'):
        return request._cached_current_user

    user_id = request.session.get('user_id')
    if not user_id:
        request._cached_current_user = None
        return None

    user = Users.objects.filter(id=user_id).first()
    if not user:
        request.session.flush()
        request._cached_current_user = None
        return None

    request._cached_current_user = user
    return user


def send_confirmation_email(request, user):
    token = user.generate_email_verification_token()
    confirmation_url = request.build_absolute_uri(
        reverse('confirm_email', args=[token])
    )
    message = (
        f'Hello {user.username},\n\n'
        'Thank you for registering.\n'
        'Open the link below to confirm your email:\n'
        f'{confirmation_url}\n\n'
        'This confirmation link works for 24 hours.'
    )
    send_mail(
        subject='Confirm your email',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_reset_password_email(request, user):
    token = user.generate_reset_password_token()
    reset_url = request.build_absolute_uri(reverse('reset_password', args=[token]))
    message = (
        f'Hello {user.username},\n\n'
        'We received a request to reset your password.\n'
        'Open the link below to create a new password:\n'
        f'{reset_url}\n\n'
        'This reset link works for 1 hour.'
    )
    send_mail(
        subject='Reset your password',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def registrations(request):
    if get_logged_in_user(request):
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']
            role = form.cleaned_data.get('role', 'Customer')

            if role not in ('Specialist', 'Customer'):
                role = 'Customer'

            existing_email_user = Users.objects.filter(email=email).first()

            if existing_email_user and existing_email_user.is_email_verified:
                messages.error(request, 'This email is already registered.')
            else:
                try:
                    validate_password(password, user=Users(username=username, email=email))
                except ValidationError as error:
                    for msg in error.messages:
                        messages.error(request, msg)
                else:
                    if existing_email_user:
                        existing_email_user.username = username
                        existing_email_user.set_password(password)
                        existing_email_user.save(update_fields=['username', 'password'])
                        existing_email_user.groups.clear()
                        user_role, _ = Group.objects.get_or_create(name=role)
                        existing_email_user.groups.add(user_role)
                        send_confirmation_email(request, existing_email_user)
                    else:
                        user = Users.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                        )
                        user_role, _ = Group.objects.get_or_create(name=role)
                        user.groups.add(user_role)
                        send_confirmation_email(request, user)

                    messages.success(
                        request,
                        'Регистрация завершена. Подтвердите email перед входом.'
                    )
                    return redirect('email_confirmation_sent')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def email_confirmation_sent(request):
    return render(request, 'email_confirmation_sent.html')


def confirm_email(request, token):
    user = Users.objects.filter(email_verification_token=token).first()

    if not user:
        messages.error(request, 'This confirmation link is invalid.')
        return redirect('login')

    if not user.email_verification_token_is_valid():
        send_confirmation_email(request, user)
        messages.info(
            request,
            'The old confirmation link expired. A new confirmation email was sent.',
        )
        return redirect('email_confirmation_sent')

    user.confirm_email()
    messages.success(request, 'Your email was confirmed. You can now log in.')
    return redirect('login')


def login_view(request):
    if get_logged_in_user(request):
        return redirect('home')

    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = Users.objects.filter(username=username).first()

            if not user:
                messages.error(request, 'Пользователь не найден.')
            elif not check_password(password, user.password):
                messages.error(request, 'Неверный пароль.')
            elif not user.is_email_verified and not user.is_superuser:
                send_confirmation_email(request, user)
                messages.error(
                    request,
                    'Подтвердите email. Мы отправили новое письмо.',
                )
            else:
                request.session.flush()
                request.session['user_id'] = user.id
                request.session['username'] = user.username

                role = user.groups.filter(
                    name__in=['Admin', 'Specialist', 'Customer']
                ).values_list('name', flat=True).first()
                request.session['user_role'] = role or 'Customer'
                request.session.modified = True
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('home')
        else:
            messages.error(request, 'Проверьте введённые данные.')

    return render(request, 'login.html', {'form': form})


def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            user = Users.objects.filter(email=email, is_email_verified=True).first()
            if user:
                send_reset_password_email(request, user)
            messages.success(
                request,
                'If the email exists, a password reset link has been sent.',
            )
            return redirect('forgot_password')

    return render(request, 'forgot_password.html', {'form': form})


def reset_password(request, token):
    user = Users.objects.filter(reset_password_token=token).first()

    if not user or not user.reset_password_token_is_valid():
        if user:
            user.clear_reset_password_token()
        messages.error(request, 'This reset link is invalid or expired.')
        return redirect('forgot_password')

    form = ResetPasswordForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            password = form.cleaned_data['password']
            try:
                validate_password(password, user=user)
            except ValidationError as error:
                for msg in error.messages:
                    messages.error(request, msg)
            else:
                user.set_password(password)
                user.save()
                user.clear_reset_password_token()
                messages.success(request, 'Your password has been reset. Please log in.')
                return redirect('login')

    return render(request, 'reset_password.html', {'form': form})


def change_password(request):
    current_user = get_logged_in_user(request)

    if not current_user:
        messages.error(request, 'Please log in first.')
        return redirect('login')

    form = ChangePasswordForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']

            if not check_password(old_password, current_user.password):
                messages.error(request, 'Your current password is incorrect.')
            else:
                try:
                    validate_password(new_password, user=current_user)
                except ValidationError as error:
                    for msg in error.messages:
                        messages.error(request, msg)
                else:
                    current_user.set_password(new_password)
                    current_user.save()
                    messages.success(request, 'Your password was changed successfully.')
                    return redirect('home')

    return render(request, 'change_password.html', {'form': form})


def logout_view(request):
    request.session.flush()
    messages.info(request, 'Вы вышли из системы.')
    return redirect('login')    

from .forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm, ProfileForm
def profile_view(request):
    current_user = get_logged_in_user(request)
    if not current_user:
        return redirect('login')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=current_user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('profile')
        else:
            messages.error(request, 'Проверьте введённые данные.')
    else:
        form = ProfileForm(instance=current_user)

    from myapp.models import Resume
    
    is_specialist = current_user.has_role('Specialist')
    
    user_resumes = Resume.objects.filter(user=current_user) if is_specialist else []

    return render(request, 'profile.html', {
        'form': form,
        'current_user': current_user,
        'user_resumes': user_resumes,
        'role': current_user.get_role_names(),
        'is_specialist': is_specialist, 
    })