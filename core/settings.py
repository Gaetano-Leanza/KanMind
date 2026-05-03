from pathlib import Path

# --- Path configuration ---
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security settings ---
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5=m*&s5p86-^4y45q+5njn-igye1q9h_&fcl^&8tz5usp3lj6k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Domains/IPs allowed to access this Django site
ALLOWED_HOSTS = [
    'gaetano-leanza.developerakademie.org',
    '127.0.0.1', 
    'localhost'
]

# --- Application definition ---
INSTALLED_APPS = [
    # Core Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    # Local project apps
    'auth_app',
    'kanban_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Handles Cross-Origin Resource Sharing
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL configuration location
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Entry point for WSGI-compatible web servers
WSGI_APPLICATION = 'core.wsgi.application'

# --- Database configuration ---
# Using SQLite for development as per BASE_DIR
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Password validation ---
# Ensuring passwords meet security standards
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Django Rest Framework (DRF) settings ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# --- CORS configuration ---
# Allowed origins for Cross-Origin requests
CORS_ALLOWED_ORIGINS = [
    "https://gaetano-leanza.developerakademie.org",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

# Allowed HTTP headers for CORS requests
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# --- Internationalization ---
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# --- Static files (CSS, JavaScript, Images) ---
STATIC_URL = 'static/'

# Primary key field type for models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'