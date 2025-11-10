import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import dj_database_url
# Cargar variables del archivo .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.getenv('SECRET_KEY', 'django-default-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

ALLOWED_HOSTS = ["3.151.4.203", "localhost", "127.0.0.1"]

# Aplicaciones principales
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps propias
    'usuarios',
    'productos',
    'ventas',
    'creditos',
    'reportes',

    # Terceros
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS habilitado
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # carpeta para tus HTML
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# -------------------------------
# BASE DE DATOS
# -------------------------------
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3')

#DATABASES = {
 #   'default': {
  #      'ENGINE': 'django.db.backends.postgresql',
   #     'NAME': os.getenv('DB_NAME', 'tiendaropa'),
   #     'USER': os.getenv('DB_USER', 'postgres'),
   #     'PASSWORD': os.getenv('DB_PASSWORD', 'tu_contraseña'),
   #     'HOST': os.getenv('DB_HOST', 'localhost'),
   #     'PORT': os.getenv('DB_PORT', '5432'),
    #}
#}
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}
# -------------------------------
# USUARIOS PERSONALIZADOS
# -------------------------------
AUTH_USER_MODEL = 'usuarios.Usuario'

# -------------------------------
# CONTRASEÑAS
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------
# INTERNACIONALIZACIÓN
# -------------------------------
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# -------------------------------
# ARCHIVOS ESTÁTICOS Y MEDIA
# -------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
#STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------------
# REST FRAMEWORK
# -------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}

# -------------------------------
# CORS (para conectar con Flask u otro frontend)
# -------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://3.151.4.203",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# -------------------------------
# CONFIG GLOBAL
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#quitar esto para produccion
SIMPLE_JWT = {
    # Tiempo de vida del token de acceso (Access Token)
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),

    # Tiempo de vida del token de actualización (Refresh Token)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Si deseas que el refresh token cambie al usarlo
    'ROTATE_REFRESH_TOKENS': False,

    # Permite seguir usando un refresh token después de obtener otro
    'BLACKLIST_AFTER_ROTATION': False,

    # Algoritmo de firma (no cambies esto)
    'ALGORITHM': 'HS256',

    # Clave secreta de Django (ya se toma de settings.SECRET_KEY)
    'SIGNING_KEY': SECRET_KEY,

    # Tipo de autenticación esperado
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",  # Para desarrollo
        "LOCATION": "unique-reportes-cache"
        #"BACKEND": "django.core.cache.backends.redis.RedisCache",
        #"LOCATION": "redis://127.0.0.1:6379/1"

    }
}
