from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.registrations, name='register'),
    path('email-confirmation-sent/', views.email_confirmation_sent, name='email_confirmation_sent'),
    path('confirm-email/<str:token>/', views.confirm_email, name='confirm_email'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),

    path('change-password/', views.change_password, name='change_password'),
    path('profile/', views.profile_view, name='profile'),
]