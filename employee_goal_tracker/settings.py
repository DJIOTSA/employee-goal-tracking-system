"""
Django settings for employee_goal_tracker project.

Generated by 'django-admin startproject' using Django 4.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-%csmn#0%!$e5ig(kqlym-)bj*58us+8d8@^zvbzseqp+0+0&de"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    'corsheaders',
    "rest_framework.authtoken", # after this we need to migrate the app to ensure that all changes are applied
    "EGT",
    "Chat",
    "Notification",
    "payroll",
    "tasks",
    "performance",
    'django_celery_beat',
    'django_celery_results',

]

# To avoid debug to be displaying
DEBUG = True
# ALLOWED_HOSTS = ["127.0.0.1",]
# ALLOWED_PORTS = ["8000",]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,

}





MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'corsheaders.middleware.CorsMiddleware',
]

# CORS_ORIGIN_ALLOW_ALL = True



ROOT_URLCONF = "employee_goal_tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'EGT/templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "employee_goal_tracker.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": BASE_DIR / "db.sqlite3",
    # },
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'egtdb',
        'USER': 'mhulo',
        'PASSWORD': 'mhulo2029',
        'HOST': 'localhost',
        'PORT': '5432',
    },

}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'EGT.MyUser'

# AUTHENTICATION_BACKENDS = [
#     'django.contrib.auth.backends.ModelBackend',
#     'EGT.authentications.EmployeeUserBackend',
#     'EGT.authentications.AdministratorUserBackend',
# ]


EMAIL_FROM = os.environ.get('AUTHEMAIL_DEFAULT_EMAIL_FROM') or 'EGT'
EMAIL_BCC = os.environ.get('AUTHEMAIL_DEFAULT_EMAIL_BCC') or 'EGT'  

EMAIL_HOST = os.environ.get('AUTHEMAIL_EMAIL_HOST') or 'smtp.gmail.com'
EMAIL_PORT = os.environ.get('AUTHEMAIL_EMAIL_PORT') or 587
"""
EMAIL_HOST_USER ='egt4startup@gmail.com'
EMAIL_HOST_PASSWORD = 'ljjt rfcr zrwd nnyi'
"""
EMAIL_HOST_USER = os.environ.get('AUTHEMAIL_EMAIL_HOST_USER') or 'egt4startup@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get('AUTHEMAIL_EMAIL_HOST_PASSWORD') or 'ljjt rfcr zrwd nnyi'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False


# configure media file; update file trough the application
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = 'media/'


# celery BROKER, celery setting.
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BROKER', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
# Celery Configuration Options
CELERY_TIMEZONE = "Africa/Douala"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'run-every-midnight': {
        'task': 'tasks.tasks.repeat_daily',
        'schedule': crontab(hour=0, minute=0, day_of_week='*'),
        # Adjust timezone based on user's timezone
        'options': {'timezone': 'user_timezone_here'},
    },
    'run-every-monday-at-': {
        'task': 'tasks.tasks.repeat_weekly',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),
        # Adjust timezone based on user's timezone
        'options': {'timezone': 'user_timezone_here'},
    },
    'run-every-1st-day-of-month-at-midnight': {
        'task': 'tasks.tasks.repeat_monthly',
        'schedule': crontab(hour=0, minute=0, day_of_month=1),
        # Adjust timezone based on user's timezone
        'options': {'timezone': 'user_timezone_here'},
    },
}

# CELERY_CACHE_BACKEND = 'default'

# django setting.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}