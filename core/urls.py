"""
URL configuration for the core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

# --- Main URL Patterns ---
# This list defines the entry points for the different modules of the application.
urlpatterns = [
    # Administrative interface provided by Django
    path('admin/', admin.site.urls),

    # Authentication API endpoints (Login, Registration, etc.)
    # Routes to the sub-routing defined in auth_app.api.urls
    path('api/', include('auth_app.api.urls')),

    # Kanban Board API endpoints (Boards, Tasks, etc.)
    # Routes to the sub-routing defined in kanban_app.api.urls
    path('kanban/', include('kanban_app.api.urls')),
]