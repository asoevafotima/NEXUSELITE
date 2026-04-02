from django.db import models
from django.conf import settings


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

class ServiceOrder(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


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

    def str(self):
        return self.title
