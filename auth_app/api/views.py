from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView


from .serializers import LoginSerializer, RegistrationSerializer


class LoginView(APIView):
    """
    Authentifiziert einen Benutzer via Email und Passwort.
    Liefert Token und Profildaten zurück.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = self._get_authenticated_user(serializer.validated_data)
        if not user:
            return Response({"error": "Ungültige Daten"}, status=status.HTTP_400_BAD_REQUEST)

        return self._get_auth_response(user)

    def _get_authenticated_user(self, data):
        try:
            user_obj = User.objects.get(email=data.get('email'))
            return authenticate(username=user_obj.username, password=data.get('password'))
        except User.DoesNotExist:
            return None

    def _get_auth_response(self, user):
        token, _ = Token.get_or_create(user=user)
        return Response({
            "token": token.key,
            "fullname": f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_200_OK)
