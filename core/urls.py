"""
URL configuration for the core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

# --- Main URL Patterns ---
# Diese Liste definiert die Einstiegspunkte für deine API-Module.
urlpatterns = [
    # Administrations-Interface
    path('admin/', admin.site.urls),

    # Authentication API endpoints (Login, Registration, Email-Check)
    # Erwartet im Frontend: /api/email-check/
    path('api/', include('auth_app.api.urls')),

    # Kanban Board API endpoints (Boards, Tasks, etc.)
    # Erwartet im Frontend: /api/kanban/boards/
    # Wir fügen hier 'api/' davor ein, damit es zum Frontend passt
    path('api/kanban/', include('kanban_app.api.urls')),
]