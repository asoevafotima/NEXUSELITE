import secrets
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone


class Users(AbstractUser):
    bio = models.TextField(blank=True, default='')
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=120, blank=True, default='')
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    reset_password_token = models.CharField(max_length=120, blank=True, default='')
    reset_password_sent_at = models.DateTimeField(blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='account_users',
        verbose_name='Roles',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='account_users',
        verbose_name='Extra permissions',
    )

    def __str__(self):
        return self.username

    def get_direct_permissions(self):
        return {
            f'{p.content_type.app_label}.{p.codename}'
            for p in self.user_permissions.select_related('content_type')
        }

    def get_group_permissions(self):
        return {
            f'{p.content_type.app_label}.{p.codename}'
            for p in Permission.objects.filter(group__account_users=self)
            .select_related('content_type').distinct()
        }

    def get_all_permissions(self, obj=None):
        return self.get_direct_permissions() | self.get_group_permissions()

    def has_perm(self, permission_name, obj=None):
        if self.is_superuser:
            return True
        return permission_name in self.get_all_permissions()

    def get_role_names(self):
        return list(self.groups.values_list('name', flat=True))

    def has_role(self, *role_names):
        return self.groups.filter(name__in=role_names).exists()

    def generate_email_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token

    def confirm_email(self):
        self.is_email_verified = True
        self.email_verification_token = ''
        self.email_verification_sent_at = None
        self.save(update_fields=['is_email_verified', 'email_verification_token', 'email_verification_sent_at'])

    def email_verification_token_is_valid(self):
        if not self.email_verification_token or not self.email_verification_sent_at:
            return False
        return timezone.now() <= self.email_verification_sent_at + timedelta(hours=24)

    def generate_reset_password_token(self):
        self.reset_password_token = secrets.token_urlsafe(32)
        self.reset_password_sent_at = timezone.now()
        self.save(update_fields=['reset_password_token', 'reset_password_sent_at'])
        return self.reset_password_token

    def clear_reset_password_token(self):
        self.reset_password_token = ''
        self.reset_password_sent_at = None
        self.save(update_fields=['reset_password_token', 'reset_password_sent_at'])

    def reset_password_token_is_valid(self):
        if not self.reset_password_token or not self.reset_password_sent_at:
            return False
        return timezone.now() <= self.reset_password_sent_at + timedelta(hours=1)