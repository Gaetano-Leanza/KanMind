from django.urls import path
from .views import LoginView, RegistrationView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/registration/', RegistrationView.as_view(),
         name='auth-registration'),
]
