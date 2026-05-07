from django.urls import path
from .views import RegistrationView, LoginView, EmailCheckView # Stelle sicher, dass EmailCheckView hier importiert ist

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Diesen Pfad hinzufügen, damit /api/email-check/ funktioniert:
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]