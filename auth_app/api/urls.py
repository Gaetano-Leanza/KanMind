"""
URL configuration for the authentication app.

This module defines the routing for user registration, login, 
and email validation endpoints.
"""

from django.urls import path
# Ensure all necessary views, including EmailCheckView, are imported here
from .views import RegistrationView, LoginView, EmailCheckView 

urlpatterns = [
    # Endpoint for registering a new user account
    path('registration/', RegistrationView.as_view(), name='registration'),
    
    # Endpoint for user authentication and token generation
    path('login/', LoginView.as_view(), name='login'),
    
    # Endpoint to validate if an email address already exists in the database
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]