from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Users


@admin.register(Users)
class UsersAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'full_name',
        'role_badge',
        'is_email_verified',
        'is_staff',
        'last_login',
    )
    list_filter = (
        'is_email_verified',
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'date_joined',
        'last_login',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'bio',
    )
    ordering = ('-date_joined',)
    list_per_page = 25
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = (
        'last_login',
        'date_joined',
        'is_email_verified',
        'email_verification_sent_at',
        'reset_password_sent_at',
    )

    fieldsets = (
        ('Account', {
            'fields': ('username', 'password', 'email')
        }),
        ('Profile', {
            'fields': ('first_name', 'last_name', 'bio')
        }),
        ('Verification', {
            'fields': (
                'is_email_verified',
                'email_verification_token',
                'email_verification_sent_at',
                'reset_password_token',
                'reset_password_sent_at',
            )
        }),
        ('Roles and Access', {
            'fields': (
                'groups',
                'user_permissions',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'groups',
                'is_staff',
                'is_superuser',
                'is_active',
            ),
        }),
    )

    @admin.display(description='Full name')
    def full_name(self, obj):
        full_name = f'{obj.first_name} {obj.last_name}'.strip()
        return full_name or '-'

    @admin.display(description='Roles')
    def role_badge(self, obj):
        return ', '.join(obj.get_role_names()) or '-'
