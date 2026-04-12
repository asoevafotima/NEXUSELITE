from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed, post_save, pre_save
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


@receiver(m2m_changed, sender=Users.groups.through)
def keep_single_primary_role(sender, instance, action, **kwargs):
    if action not in ('post_add', 'post_remove'):
        return
    if getattr(instance, '_syncing_roles', False):
        return

    priority = ['Admin', 'Specialist', 'Customer']
    role_names = list(instance.groups.filter(name__in=priority).values_list('name', flat=True))
    if len(role_names) <= 1:
        return

    chosen_role = next((name for name in priority if name in role_names), None)
    if not chosen_role:
        return

    instance._syncing_roles = True
    try:
        instance.groups.remove(*instance.groups.filter(name__in=priority).exclude(name=chosen_role))
    finally:
        instance._syncing_roles = False
