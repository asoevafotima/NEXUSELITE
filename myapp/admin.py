from django.contrib import admin
from .models import Resume, ServiceOrder, Review, Feedback, Category

admin.site.register(Resume)
admin.site.register(ServiceOrder)
admin.site.register(Review)
admin.site.register(Feedback)
admin.site.register(Category)