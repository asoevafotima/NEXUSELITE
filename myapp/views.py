from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail 
from .models import Resume, Review, ServiceOrder, Feedback, AIRequest
from .forms import ResumeForm, ReviewForm, FeedbackForm, AIRequestForm, ServiceOrderForm
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
        queryset = Resume.objects.select_related('category', 'user').order_by('-created_at')
        self.filterset = ResumeFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        resumes = list(context['resumes'])
        categories = list(
            Resume.objects.select_related('category')
            .values_list('category__name', flat=True)
            .distinct()
        )
        context['featured_resumes'] = resumes[:6]
        context['categories_preview'] = categories[:8]
        context['stats'] = {
            'resumes': Resume.objects.count(),
            'specialists': Resume.objects.values('user').distinct().count(),
            'categories': len(categories),
            'reviews': Review.objects.count(),
        }
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
        context['availability_text'] = self.object.get_availability_text()
        context['is_available_now'] = self.object.is_available_now()
        context.update(base_context(self.request))
        return context


class ResumeCreateView(PermissionRequiredMixin, CreateView):

    required_permission = 'add_resume'
    model = Resume
    form_class = ResumeForm
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resume'] = Resume.objects.get(pk=self.kwargs['pk'])
        context.update(base_context(self.request))
        return context

    def form_valid(self, form):
        form.instance.resume_id = self.kwargs['pk']
        form.instance.author = get_logged_in_user(self.request)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('resume_detail', kwargs={'pk': self.kwargs['pk']})


class OrderCreateView(PermissionRequiredMixin, CreateView):
    required_permission = 'add_serviceorder'
    model = ServiceOrder
    form_class = ServiceOrderForm
    template_name = 'order_add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resume'] = Resume.objects.get(pk=self.kwargs['pk'])
        context.update(base_context(self.request))
        return context

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
                        f'Срок услуги: {form.instance.get_duration_label()}\n\n'
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


def studio_view(request):
    return render(request, 'studio.html', base_context(request))


RESOURCE_PAGES = {
    'blog': {
        'title': 'Блог Nexus Elite',
        'subtitle': 'Новости, кейсы и практические материалы',
        'description': 'Здесь мы собираем статьи о рынке услуг, портфолио специалистов, подборе исполнителей и цифровых инструментах для работы.',
    },
    'faq': {
        'title': 'Частые вопросы',
        'subtitle': 'Быстрые ответы по платформе',
        'description': 'Вопросы о регистрации, заказах, отзывах, безопасности, подборе специалистов и работе AI-помощника.',
    },
    'support': {
        'title': 'Поддержка',
        'subtitle': 'Мы помогаем с любыми вопросами',
        'description': 'Если у вас не работает регистрация, заказ, редактирование профиля или AI-чат, напишите в поддержку через форму обратной связи.',
    },
    'rules': {
        'title': 'Правила платформы',
        'subtitle': 'Прозрачные условия работы',
        'description': 'Раздел с базовыми правилами публикации резюме, общения с клиентами, оформления заказов и модерации контента.',
    },
    'privacy': {
        'title': 'Конфиденциальность',
        'subtitle': 'Как мы работаем с данными',
        'description': 'Мы используем данные аккаунта только для работы платформы, заказов, сообщений и повышения безопасности.',
    },
    'offer': {
        'title': 'Публичная оферта',
        'subtitle': 'Основные условия использования',
        'description': 'Раздел с условиями использования платформы Nexus Elite для заказчиков и специалистов.',
    },
    'database': {
        'title': 'База специалистов',
        'subtitle': 'Категории, навыки и профили',
        'description': 'Каталог специалистов с фильтрацией по категориям, навыкам, стоимости и доступности.',
    },
    'analytics': {
        'title': 'Аналитика',
        'subtitle': 'Тренды, востребованность и рост',
        'description': 'Материалы о популярных категориях, динамике спроса и поведении клиентов на платформе.',
    },
    'security': {
        'title': 'Безопасность',
        'subtitle': 'Защита аккаунтов и заказов',
        'description': 'Советы по защите аккаунта, безопасной коммуникации и работе с заказами на платформе.',
    },
    'newsletter': {
        'title': 'Подписка на дайджест',
        'subtitle': 'Новости платформы и подборки специалистов',
        'description': 'Подборки новых резюме, статьи, обновления платформы и советы по поиску специалистов.',
    },
    'development': {
        'title': 'Разработка',
        'subtitle': 'Услуги по созданию цифровых продуктов',
        'description': 'Backend, frontend, Telegram-боты, автоматизация, корпоративные сайты и внутренние сервисы.',
    },
    'design': {
        'title': 'Дизайн',
        'subtitle': 'Интерфейсы, брендинг и визуальные системы',
        'description': 'UI/UX, брендинг, баннеры, лендинги, презентации и визуальные материалы для бизнеса.',
    },
    'marketing': {
        'title': 'Маркетинг',
        'subtitle': 'Продвижение и рост',
        'description': 'Контент, таргетинг, аналитика, воронки продаж и упаковка продукта для роста бизнеса.',
    },
    'top-categories': {
        'title': 'Топ категории',
        'subtitle': 'Самые востребованные направления',
        'description': 'Раздел с самыми популярными категориями специалистов на платформе и быстрым переходом к поиску.',
    },
}


def resource_page(request, slug):
    page = RESOURCE_PAGES.get(slug)
    if not page:
        return redirect('home')

    context = {
        'slug': slug,
        **page,
        **base_context(request),
    }
    return render(request, 'resource_page.html', context)
