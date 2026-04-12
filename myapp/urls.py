from django.urls import path
from .views import *
from . import views 

urlpatterns = [
    path('', Home.as_view(), name='home'),  
    path('ai/', HomeView.as_view(), name='homeview'), 
    path('history/', views.history, name='history'),
    path('about/', about_view, name='aboutas'),
    path('studio/', views.studio_view, name='studio'),
    path('pages/<slug:slug>/', views.resource_page, name='resource_page'),
    path('api/ai/', views.ai_api, name='ai-api'),     

    path('resume/add/', ResumeCreateView.as_view(), name='resume_add'),
    path('resume/<int:pk>/', ResumeDetailView.as_view(), name='resume_detail'),
    path('resume/<int:pk>/edit/', ResumeUpdateView.as_view(), name='resume_edit'),
    path('resume/<int:pk>/delete/', ResumeDeleteView.as_view(), name='resume_delete'),

    path('resume/<int:pk>/review_add', ReviewCreateView.as_view(), name='review_add'),
    path('resume/<int:pk>/order_add', OrderCreateView.as_view(), name='order_add'),

    path('feedback/', FeedbackCreateView.as_view(), name='feedback'),
]
