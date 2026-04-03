from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail 
from .models import Resume, Review, ServiceOrder, Feedback, AIRequest
from .forms import ResumeForm, ReviewForm, FeedbackForm, AIRequestForm
from .filters import ResumeFilter

from .permissions import (
    get_logged_in_user, user_has_perm, get_user_role,
    build_permission_flags, session_login_required
)

import requests
import json
import os
from dotenv import load_dotenv
from django.conf import settings

load_dotenv()
MODEL_NAME = "google/gemini-2.0-flash-001"



class LoginRequiredMixin:
    """Просто проверяет авторизацию."""
    def dispatch(self, request, *args, **kwargs):
        if not get_logged_in_user(request):
            messages.error(request, 'Войдите в систему для доступа.')
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin:
    """
    Проверяет конкретное право из нашей системы ролей.
    Укажите required_permission = 'add_resume' в классе.
    """
    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        user = get_logged_in_user(request)
        if not user:
            messages.error(request, 'Войдите в систему.')
            return redirect('login')
        if self.required_permission and not user_has_perm(user, self.required_permission):
            messages.error(request, 'У вас нет прав для этого действия.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class OwnerOrAdminMixin:
    """
    Для edit/delete: разрешает только владельцу объекта или Admin.
    Модель должна иметь поле `user` (владелец).
    """
    def dispatch(self, request, *args, **kwargs):
        user = get_logged_in_user(request)
        if not user:
            return redirect('login')
        obj = self.get_object()
        role = get_user_role(user)
        if role != 'Admin' and getattr(obj, 'user', None) != user:
            messages.error(request, 'Вы можете редактировать только свои записи.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)



def base_context(request):
    user = get_logged_in_user(request)
    ctx = build_permission_flags(user)
    ctx['current_user'] = user
    return ctx



def ask_ai(text: str, mode: str = "ask"):
    OPENROUTER_API_KEY = getattr(settings, "OPENROUTER_API_KEY", "")
    url = "https://openrouter.ai/api/v1/chat/completions"

    try:
        db_resumes = Resume.objects.select_related('category').all().order_by('-created_at')[:15]
        workers_info = ""
        for s in db_resumes:
            workers_info += (
                f"- Специалист: {s.full_name}\n"
                f"  Профессия: {s.professian}\n"
                f"  Категория: {s.category.name}\n"
                f"  Навыки: {s.skills}\n"
                f"  Цена: {s.price} руб.\n"
                f"  Описание: {s.description if s.description else 'Нет описания'}\n"
                "-------------------\n"
            )
    except Exception as e:
        return f"Ошибка при чтении базы данных: {str(e)}"

    system_instruction = (
        "Ты — узкоспециализированный AI-ассистент платформы Nexus Elite.\n"
        "У тебя есть доступ к списку реальных резюме из нашей базы:\n\n"
        f"{workers_info if workers_info else 'База мастеров пока пуста.'}\n\n"
        "Твоя задача — помогать пользователям ТОЛЬКО в трех направлениях:\n"
        "1. Рекомендация конкретных специалистов из списка выше на основе их навыков.\n"
        "2. Советы, какой тип мастера нужен для решения проблемы.\n"
        "3. Помощь в написании и улучшении резюме.\n\n"
        "ПРАВИЛА:\n"
        "- Если в списке есть подходящий человек, назови его имя и профессию.\n"
        "- Если подходящего мастера НЕТ, скажи: 'На данный момент в нашей базе нет такого специалиста, но я могу посоветовать, как его выбрать'.\n"
        "- На вопросы НЕ по теме (игры, рецепты, политика) отвечай: 'Я консультирую только по вопросам поиска специалистов и карьеры'.\n"
        "- Отвечай на русском языке, вежливо и по делу.\n\n"
        
    
        "Всегда давай как можно больше полезной и подробной информации: объясняй рекомендации развернуто, указывай почему именно этот специалист подходит (сравнивая навыки и цену), приводи несколько вариантов если возможно, добавляй советы по выбору, что спросить у мастера при обращении, и любые полезные детали из его резюме. Будь максимально информативным и подробным в рамках своих правил."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Nexus Elite AI Assistant",
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": text}
        ],
        "temperature": 0.4,
        "max_tokens": 1000,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=40)
        if response.status_code != 200:
            return f"Ошибка API ({response.status_code}): {response.text[:200]}"
        result = response.json()
        if 'error' in result:
            return f"Ошибка нейросети: {result['error'].get('message', 'Неизвестная ошибка')}"
        return result['choices'][0]['message']['content'].strip()
    except requests.exceptions.Timeout:
        return "Ошибка: Сервер нейросети слишком долго отвечает."
    except requests.exceptions.ConnectionError:
        return "Ошибка: Нет соединения с API OpenRouter."
    except Exception as e:
        return f"Критическая ошибка: {str(e)}"


def ai_api(request):
    if not get_logged_in_user(request):
        return JsonResponse({"response": "Требуется авторизация."}, status=401)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("user_text", "").strip()
            mode = data.get("mode", "ask")
            if not text:
                return JsonResponse({"response": "Пустой запрос"}, status=400)
            return JsonResponse({"response": ask_ai(text, mode)})
        except json.JSONDecodeError:
            return JsonResponse({"response": "Неверный JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"response": f"Серверная ошибка: {str(e)}"}, status=500)

    return JsonResponse({"response": "Используйте POST."})



class Home(ListView):
    model = Resume
    template_name = 'home.html'
    context_object_name = 'resumes'

    def get_queryset(self):
        self.filterset = ResumeFilter(self.request.GET, queryset=Resume.objects.all())
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context.update(base_context(self.request)) 
        return context



class HomeView(LoginRequiredMixin, CreateView):
    model = AIRequest
    form_class = AIRequestForm
    template_name = "homeview.html"
    success_url = reverse_lazy('history')

    def form_valid(self, form):
        user_text = form.cleaned_data.get('user_text')
        mode = form.cleaned_data.get('mode', 'ask')
        form.instance.title = (user_text[:60] + "...") if user_text else "Новый запрос"
        form.instance.ai_response = ask_ai(user_text, mode)
        return super().form_valid(form)


@session_login_required
def history(request):
    reqs = AIRequest.objects.all().order_by('-created_at')
    return render(request, 'history.html', {'requests': reqs, **base_context(request)})


class ResumeDetailView(DetailView):
 
    model = Resume
    template_name = 'resume_detail.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = Review.objects.filter(resume=self.object)
        context.update(base_context(self.request))
        return context


class ResumeCreateView(PermissionRequiredMixin, CreateView):

    required_permission = 'add_resume'
    model = Resume
    fields = ['full_name', 'professian', 'category', 'price', 'photo', 'description', 'skills']
    template_name = 'resume_add.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = get_logged_in_user(self.request)
        return super().form_valid(form)


class ResumeUpdateView(OwnerOrAdminMixin, PermissionRequiredMixin, UpdateView):
  
    required_permission = 'change_resume'
    model = Resume
    form_class = ResumeForm
    template_name = 'resume_edit.html'
    success_url = reverse_lazy('home')


class ResumeDeleteView(OwnerOrAdminMixin, PermissionRequiredMixin, DeleteView):
    required_permission = 'delete_resume'
    model = Resume
    template_name = 'resume_delete.html'
    success_url = reverse_lazy('home')


class ReviewCreateView(LoginRequiredMixin, CreateView):

    model = Review
    form_class = ReviewForm
    template_name = 'review_add.html'

    def form_valid(self, form):
        form.instance.resume_id = self.kwargs['pk']
        form.instance.author = get_logged_in_user(self.request)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('resume_detail', kwargs={'pk': self.kwargs['pk']})


class OrderCreateView(PermissionRequiredMixin, CreateView):
    required_permission = 'add_serviceorder'
    model = ServiceOrder
    fields = ['text', 'details']
    template_name = 'order_add.html'

    def form_valid(self, form):
        form.instance.resume_id = self.kwargs['pk']
        form.instance.customer = get_logged_in_user(self.request)
        
        response = super().form_valid(form)
        
        try:
            resume = Resume.objects.get(pk=self.kwargs['pk'])
            specialist_email = resume.user.email
            print(f">>> EMAIL СПЕЦИАЛИСТА: '{specialist_email}'")
            
            if not specialist_email:
                print(">>> EMAIL ПУСТОЙ — письмо не отправлено!")
            else:
                customer = get_logged_in_user(self.request)
                send_mail(
                    subject=f'Новый заказ от {customer.username}',
                    message=(
                        f'Вам поступил новый заказ!\n\n'
                        f'Клиент: {customer.username}\n'
                        f'Email клиента: {customer.email}\n\n'
                        f'Текст заказа:\n{form.cleaned_data.get("text", "")}\n\n'
                        f'Детали:\n{form.cleaned_data.get("details", "")}'
                    ),
                    from_email=None,
                    recipient_list=[specialist_email],
                    fail_silently=False,
                )
                print(">>> ПИСЬМО ОТПРАВЛЕНО!")
        except Exception as e:
            print(f">>> ОШИБКА: {e}")
        
        messages.success(self.request, 'Заказ отправлен')
        return response

    def get_success_url(self): 
        return reverse('resume_detail', kwargs={'pk': self.kwargs['pk']})
    

class FeedbackCreateView(PermissionRequiredMixin, CreateView):
  
    required_permission = 'add_feedback'
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedback.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = get_logged_in_user(self.request)
        if user:
            form.instance.user = user
        messages.success(self.request, 'Спасибо за отзыв!')
        return super().form_valid(form)


def about_view(request):  
    return render(request, 'aboutas.html', base_context(request))