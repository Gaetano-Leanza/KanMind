"""
URL configuration for the core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, TaskViewSet

# --- Router Configuration ---
# The DefaultRouter automatically creates the endpoints for your viewsets.
router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'tasks', TaskViewSet, basename='tasks')

# --- API URL Patterns ---
urlpatterns = [
    # This includes all routes registered above (e.g., /boards/, /tasks/)
    path('', include(router.urls)),
]