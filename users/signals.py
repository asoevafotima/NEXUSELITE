from django.contrib.auth.models import Group
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Users


@receiver(pre_save, sender=Users)
def normalize_user_email(sender, instance, **kwargs):
    if instance.email:
        instance.email = instance.email.strip().lower()


@receiver(post_save, sender=Users)
def ensure_default_role(sender, instance, created, **kwargs):
    if not created or instance.is_superuser or instance.groups.exists():
        return

    default_group, _ = Group.objects.get_or_create(name='Customer')
    instance.groups.add(default_group)
