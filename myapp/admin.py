from django.contrib import admin

from .models import AIRequest, Category, Feedback, Resume, Review, ServiceOrder


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'professian',
        'category',
        'user',
        'price',
        'created_at',
    )
    list_filter = ('category', 'created_at')
    search_fields = (
        'full_name',
        'professian',
        'skills',
        'description',
        'user__username',
        'user__email',
    )
    autocomplete_fields = ('user', 'category')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Resume', {
            'fields': (
                'user',
                'full_name',
                'professian',
                'category',
                'skills',
                'description',
                'price',
                'photo',
            )
        }),
        ('Meta', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'resume', 'customer', 'duration_value', 'duration_unit', 'short_text', 'created_at')
    list_filter = ('created_at', 'resume__category')
    search_fields = (
        'resume__full_name',
        'customer__username',
        'customer__email',
        'text',
        'details',
    )
    autocomplete_fields = ('resume', 'customer')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)

    @admin.display(description='Text')
    def short_text(self, obj):
        text = (obj.text or '').strip()
        return text[:60] + '...' if len(text) > 60 else (text or '-')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'resume', 'author', 'rating', 'short_text')
    list_filter = ('rating', 'resume__category')
    search_fields = (
        'resume__full_name',
        'author__username',
        'author__email',
        'text',
    )
    autocomplete_fields = ('resume', 'author')
    list_per_page = 25

    @admin.display(description='Review')
    def short_text(self, obj):
        text = (obj.text or '').strip()
        return text[:60] + '...' if len(text) > 60 else (text or '-')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'user', 'short_message', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'subject',
        'message',
        'user__username',
        'user__email',
    )
    autocomplete_fields = ('user',)
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)

    @admin.display(description='Message')
    def short_message(self, obj):
        text = (obj.message or '').strip()
        return text[:60] + '...' if len(text) > 60 else (text or '-')


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'mode', 'short_user_text', 'created_at')
    list_filter = ('mode', 'created_at')
    search_fields = ('title', 'user_text', 'ai_response')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)

    @admin.display(description='Request')
    def short_user_text(self, obj):
        text = (obj.user_text or '').strip()
        return text[:60] + '...' if len(text) > 60 else (text or '-')
