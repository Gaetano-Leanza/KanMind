
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RegistrationView, BoardViewSet, EmailCheckView


router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='boards')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]
