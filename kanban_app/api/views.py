from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class LoginView(APIView):
    """
    Authentifiziert einen Benutzer via Email und Passwort.
    Entspricht exakt der Vorgabe: POST /api/login/
    """
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Da Django standardmäßig mit Usernames arbeitet, suchen wir den User per Email
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user:
            token, created = Token.get_or_create(user=user)
            return Response({
                "token": token.key,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_200_OK)
        
        return Response({
            "error": "Ungültige Anfragedaten."
        }, status=status.HTTP_400_BAD_REQUEST)