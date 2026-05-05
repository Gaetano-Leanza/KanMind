from django.urls import path
from .views import LoginView, RegistrationView

# --- Authentication URL Routing ---
# This file maps specific URL endpoints to the authentication logic.
# These paths are typically included in the main project's URL configuration.

urlpatterns = [
    # Endpoint for user login: Expects credentials and returns a token
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    
    # Endpoint for user registration: Handles new account creation
    path('auth/registration/', RegistrationView.as_view(),
         name='auth-registration'),
]