# NEXUS ELITE — Resume & Services Platform

Django-приложение, где пользователи публикуют резюме (анкеты исполнителей), заказывают услуги, оставляют отзывы, а также пользуются встроенным AI-ассистентом (через OpenRouter) для работы с текстом.

## Возможности

- **Аутентификация пользователей** — регистрация, вход/выход, подтверждение email по токену, восстановление и смена пароля, профиль.
- **Резюме** — создание, просмотр, редактирование и удаление анкет с категориями, навыками, ценой и фото.
- **Заказы услуг** — оформление заказа на резюме с длительностью (часы/дни) и автоматическим расчётом доступности исполнителя.
- **Отзывы** — рейтинг и комментарии к резюме.
- **AI-ассистент** — режимы summary, quiz, keywords, simplify, ask через OpenRouter API, с историей запросов.
- **Обратная связь** — форма feedback.
- **Роли и права** — кастомная модель пользователя с группами и разрешениями.

## Стек

- Python / Django 6.0
- SQLite (по умолчанию)
- django-crispy-forms + crispy-bootstrap5
- django-filter
- Pillow (загрузка изображений)
- requests + python-dotenv
- OpenRouter API (AI-функции)

## Структура проекта

```
server/     — настройки проекта (settings, urls, wsgi/asgi)
myapp/      — резюме, заказы, отзывы, feedback, AI-запросы
users/      — кастомная модель пользователя и аутентификация
templates/  — HTML-шаблоны
media/      — загруженные файлы (не в git)
```

## Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/asoevafotima/exam.git
cd exam   # каталог репозитория

# 2. Создать и активировать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Установить зависимости
pip install django django-crispy-forms crispy-bootstrap5 django-filter pillow requests python-dotenv

# 4. Создать файл .env (см. ниже)

# 5. Применить миграции
python manage.py migrate

# 6. Создать суперпользователя (опционально)
python manage.py createsuperuser

# 7. Запустить сервер
python manage.py runserver
```

Приложение будет доступно по адресу http://127.0.0.1:8000/

## Переменные окружения (`.env`)

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Почта (подтверждение email, сброс пароля)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password

# AI-ассистент
OPENROUTER_API_KEY=your-openrouter-key
```

## Тесты

```bash
python manage.py test
```
