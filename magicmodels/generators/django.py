import os
from typing import List
from .base import BaseGenerator
from ..schema import Model, Field

class DjangoGenerator(BaseGenerator):
    def _map_type(self, field: Field, current_model: str, models: List[Model]) -> str:
        if field.is_primary_key:
            return "models.AutoField(primary_key=True)"
        if field.is_foreign_key:
            return f"models.ForeignKey('{field.related_model.lower()}.{field.related_model}', on_delete=models.CASCADE"
        if field.is_many_to_many:
            return f"models.ManyToManyField('{field.related_model.lower()}.{field.related_model}')"
            
        t = field.type.lower()
        if t == "string":
            base = "models.CharField(max_length=255"
        elif t == "int":
            base = "models.IntegerField("
        elif t == "boolean":
            base = "models.BooleanField(default=False"
        elif t == "text":
            base = "models.TextField("
        elif t == "datetime":
            base = "models.DateTimeField(auto_now_add=True"
        else:
            base = "models.CharField(max_length=255"

        if field.is_indexed and not field.is_foreign_key:
            return f"{base}, db_index=True)"
        elif field.is_foreign_key:
             return base + ")"
        elif base.endswith("("):
            return f"{base})"
        else:
            return f"{base})"

    def generate(self, models: List[Model], output_dir: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "core"), exist_ok=True)

        # .env.example
        env_code = """SECRET_KEY=django-insecure-magicmodels-change-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
"""
        with open(os.path.join(output_dir, ".env.example"), "w") as f:
            f.write(env_code)

        app_names = [model.name.lower() for model in models]

        for model in models:
            app_dir = os.path.join(output_dir, model.name.lower())
            if os.path.exists(app_dir):
                print(f"Django app for '{model.name}' already exists. Skipping generation to preserve your code.")
                continue
                
            os.makedirs(app_dir, exist_ok=True)
            
            with open(os.path.join(app_dir, "__init__.py"), "w") as f:
                f.write("")
                
            os.makedirs(os.path.join(app_dir, "migrations"), exist_ok=True)
            with open(os.path.join(app_dir, "migrations", "__init__.py"), "w") as f:
                f.write("")

            # 1. models.py
            models_code = "from django.db import models\n\n\n"
            models_code += f"class {model.name}(models.Model):\n"
            string_fields = []
            for field in model.fields:
                if field.name == 'id' and field.is_primary_key:
                    continue
                type_str = self._map_type(field, model.name, models)
                if field.is_foreign_key:
                     models_code += f"    {field.name} = {type_str})\n"
                else:
                    models_code += f"    {field.name} = {type_str}\n"
                    
                if field.type.lower() in ("string", "text"):
                    string_fields.append(f"'{field.name}'")
                    
            models_code += f"\n    def __str__(self):\n        return str(self.pk)\n"
            with open(os.path.join(app_dir, "models.py"), "w") as f:
                f.write(models_code)

            # 2. serializers.py
            serializers_code = f"from rest_framework import serializers\nfrom .models import {model.name}\n\n\n"
            serializers_code += f"class {model.name}Serializer(serializers.ModelSerializer):\n"
            serializers_code += f"    class Meta:\n"
            serializers_code += f"        model = {model.name}\n"
            serializers_code += f"        fields = '__all__'\n"
            with open(os.path.join(app_dir, "serializers.py"), "w") as f:
                f.write(serializers_code)

            # 3. views.py
            views_code = "from rest_framework import viewsets, filters\n"
            views_code += "from django_filters.rest_framework import DjangoFilterBackend\n"
            views_code += "from rest_framework.permissions import AllowAny\n"
            views_code += f"from .models import {model.name}\nfrom .serializers import {model.name}Serializer\n\n\n"
            views_code += f"class {model.name}ViewSet(viewsets.ModelViewSet):\n"
            views_code += f"    queryset = {model.name}.objects.all()\n"
            views_code += f"    serializer_class = {model.name}Serializer\n"
            views_code += f"    permission_classes = [AllowAny]  # Update to IsAuthenticated as needed\n"
            views_code += f"    filter_backends = [\n"
            views_code += f"        DjangoFilterBackend,\n"
            views_code += f"        filters.SearchFilter,\n"
            views_code += f"        filters.OrderingFilter\n"
            views_code += f"    ]\n"
            views_code += f"    filterset_fields = '__all__'\n"
            if string_fields:
                views_code += f"    search_fields = [{', '.join(string_fields)}]\n"
            views_code += f"    ordering_fields = '__all__'\n"
            with open(os.path.join(app_dir, "views.py"), "w") as f:
                f.write(views_code)

            # 4. urls.py
            urls_code = "from django.urls import path, include\nfrom rest_framework import routers\n"
            urls_code += f"from .views import {model.name}ViewSet\n\n\n"
            urls_code += "router = routers.DefaultRouter()\n"
            urls_code += f"router.register(r'', {model.name}ViewSet)\n"
            urls_code += "\nurlpatterns = [\n    path('', include(router.urls)),\n]\n"
            with open(os.path.join(app_dir, "urls.py"), "w") as f:
                f.write(urls_code)
                
            # 5. apps.py
            apps_code = f"from django.apps import AppConfig\n\n\nclass {model.name}Config(AppConfig):\n    default_auto_field = 'django.db.models.BigAutoField'\n    name = '{model.name.lower()}'\n"
            with open(os.path.join(app_dir, "apps.py"), "w") as f:
                f.write(apps_code)
                
            # 6. utils.py
            with open(os.path.join(app_dir, "utils.py"), "w") as f:
                f.write(f"# Utility functions for {model.name}\n")
                
            # 7. tests.py
            tests_code = f"""from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as AuthUser


class {model.name}APITests(APITestCase):
    def setUp(self):
        self.user = AuthUser.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/{model.name.lower()}s/'

    def test_list_{model.name.lower()}s(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
"""
            with open(os.path.join(app_dir, "tests.py"), "w") as f:
                f.write(tests_code)

        # core/settings.py
        settings_apps = "\\n    ".join([f"'{app}'," for app in app_names])
        settings_code = f"""
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-magicmodels')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    {settings_apps}
]

REST_FRAMEWORK = {{
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': (
        'rest_framework.pagination.PageNumberPagination'
    ),
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}}

SPECTACULAR_SETTINGS = {{
    'TITLE': 'MagicModels API',
    'DESCRIPTION': 'API generated by MagicModels',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}}

SIMPLE_JWT = {{
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {{
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }},
    }},
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}
}}

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
"""
        settings_code = settings_code.replace("\\n", "\n") 
        with open(os.path.join(output_dir, "core", "settings.py"), "w") as f:
            f.write(settings_code)

        # core/urls.py
        url_includes = "\n    ".join([f"path('api/{model.name.lower()}s/', include('{model.name.lower()}.urls'))," for model in models])
        core_urls_code = f"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        '',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
    path(
        'api/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    {url_includes}
]
"""
        with open(os.path.join(output_dir, "core", "urls.py"), "w") as f:
            f.write(core_urls_code)

        # core/wsgi.py
        wsgi_code = """
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()
"""
        with open(os.path.join(output_dir, "core", "wsgi.py"), "w") as f:
            f.write(wsgi_code)

        with open(os.path.join(output_dir, "core", "__init__.py"), "w") as f:
            f.write("")

        # manage.py
        manage_code = """#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
"""
        with open(os.path.join(output_dir, "manage.py"), "w") as f:
            f.write(manage_code)
        os.chmod(os.path.join(output_dir, "manage.py"), 0o755)

        # requirements.txt
        req_code = "Django==4.2.11\ndjangorestframework==3.14.0\ndjango-filter==23.5\ndrf-spectacular==0.27.1\npython-decouple==3.8\ndjangorestframework-simplejwt==5.3.1\ngunicorn==21.2.0\npytest-django==4.8.0\n"
        with open(os.path.join(output_dir, "requirements.txt"), "w") as f:
            f.write(req_code)

        # Dockerfile
        dockerfile_code = """FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
"""
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile_code)

        # docker-compose.yml
        available_port = self.find_available_port()
        compose_code = f"""version: '3.8'
services:
  web:
    build: .
    ports:
      - "{available_port}:8000"
    volumes:
      - .:/app
    command: >
      sh -c "python manage.py makemigrations &&
             python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn core.wsgi:application --bind 0.0.0.0:8000 --reload"
"""
        with open(os.path.join(output_dir, "docker-compose.yml"), "w") as f:
            f.write(compose_code)
