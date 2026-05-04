from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, TaskViewSet, EmailCheckView

# --- Router Configuration ---
# The DefaultRouter automatically generates URL patterns for the ViewSets.
# It creates endpoints for standard actions like list, create, retrieve, update, and destroy.
router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'tasks', TaskViewSet, basename='tasks')

# --- API URL Patterns ---
urlpatterns = [
    # Include all router-generated URLs (e.g., /api/boards/, /api/tasks/)
    path('', include(router.urls)),

    # Custom APIView for utility functions (Email validation)
    path('email-check/', EmailCheckView.as_view(), name='kanban-email-check'),
]