from django import forms
from .models import Resume, Review, Feedback, AIRequest, ServiceOrder


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            'full_name',
            'professian',
            'category',
            'price',
            'photo',
            'description',
            'skills',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Как вас зовут'
            }),
            'professian': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Сантехник, Дизайнер, Разработчик'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Коротко опишите, чем вы полезны клиенту'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите навыки, опыт, инструменты и сильные стороны'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Цена за услугу (сомони)'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']   
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your review here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5
            }),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject of your feedback'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your message...'
            }),
        }

class AIRequestForm(forms.ModelForm):
    class Meta:
        model = AIRequest
        fields = ['title', 'user_text', 'mode']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'user_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
        }


class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = ['text', 'details', 'duration_value', 'duration_unit']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите, какая услуга вам нужна...'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Добавьте детали, дедлайн, пожелания и формат работы...'
            }),
            'duration_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Например: 3'
            }),
            'duration_unit': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

