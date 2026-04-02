from django import forms
from .models import Resume, Review, Feedback, AIRequest


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['full_name', 'category', 'photo', 'skills', 'price']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your skills...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price per service (TJS)'
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

