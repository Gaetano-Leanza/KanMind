from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, TaskViewSet 
# EmailCheckView hier entfernen, da er jetzt in der auth_app lebt

# --- Router Configuration ---
router = DefaultRouter()
# Erzeugt die Endpunkte: /api/kanban/boards/ und /api/kanban/tasks/
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'tasks', TaskViewSet, basename='tasks')

# --- API URL Patterns ---
urlpatterns = [
    # Bindet die Router-URLs ein
    path('', include(router.urls)),
    
    # Der Email-Check Pfad wurde hier entfernt, 
    # da er nun zentral über die auth_app unter /api/email-check/ läuft.
]