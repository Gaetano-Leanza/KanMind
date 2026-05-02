from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import BoardViewSet, TaskViewSet, EmailCheckView


router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'tasks', TaskViewSet, basename='tasks')

urlpatterns = [
    path('', include(router.urls)),

    path('email-check/', EmailCheckView.as_view(), name='kanban-email-check'),
]
