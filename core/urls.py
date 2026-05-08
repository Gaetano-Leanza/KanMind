"""
URL configuration for the core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

# --- Main URL Patterns ---
urlpatterns = [
    # Administrations-Interface
    path('admin/', admin.site.urls),

    # Authentication API endpoints (Login, Registration, Email-Check)
    path('api/auth/', include('auth_app.api.urls')),

    # Kanban Board API endpoints (Boards, Tasks, etc.)
    path('api/', include('kanban_app.api.urls')),]
