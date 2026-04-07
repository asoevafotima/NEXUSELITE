from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    professian = models.CharField(max_length=100, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    skills = models.TextField()
    
    description = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to='resumes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.full_name

    def get_active_order(self):
        now = timezone.now()
        for order in self.serviceorder_set.order_by('-created_at'):
            if order.ends_at > now:
                return order
        return None

    def is_available_now(self):
        return self.get_active_order() is None

    def get_availability_text(self):
        active_order = self.get_active_order()
        if not active_order:
            return 'Свободен сейчас'
        return f'Свободен через {active_order.get_remaining_text()}'

class ServiceOrder(models.Model):
    DURATION_UNIT_CHOICES = [
        ('hours', 'Часы'),
        ('days', 'Дни'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    details = models.TextField(blank=True)
    duration_value = models.PositiveIntegerField(default=1)
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='hours')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_duration_delta(self):
        if self.duration_unit == 'days':
            return timedelta(days=self.duration_value)
        return timedelta(hours=self.duration_value)

    @property
    def ends_at(self):
        return self.created_at + self.get_duration_delta()

    def get_duration_label(self):
        return f'{self.duration_value} {self._pluralize(self.duration_value, self.duration_unit)}'

    def get_remaining_text(self):
        remaining = self.ends_at - timezone.now()
        if remaining.total_seconds() <= 0:
            return 'несколько минут'

        if self.duration_unit == 'days':
            days = max(1, int((remaining.total_seconds() + 86399) // 86400))
            return f'{days} {self._pluralize(days, "days")}'

        hours = max(1, int((remaining.total_seconds() + 3599) // 3600))
        return f'{hours} {self._pluralize(hours, "hours")}'

    @staticmethod
    def _pluralize(value, unit):
        if unit == 'days':
            forms = ('день', 'дня', 'дней')
        else:
            forms = ('час', 'часа', 'часов')

        value = abs(value) % 100
        if 11 <= value <= 19:
            return forms[2]
        value = value % 10
        if value == 1:
            return forms[0]
        if 2 <= value <= 4:
            return forms[1]
        return forms[2]


class Review(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    text = models.TextField()

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



class AIRequest(models.Model):
    MODE_CHOICES = [
        ('summary', 'Summary'),
        ('quiz', 'Quiz'),
        ('keywords', 'Keywords'),
        ('simplify', 'Simplify'),
        ('ask', 'Ask')
    ]
    
    title = models.CharField(max_length=200, blank=True, null=True)
    user_text = models.TextField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    ai_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"AI request #{self.pk or 'new'}"
