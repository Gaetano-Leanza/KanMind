from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
    """Erstellt einen neuen Benutzer und liefert einen Token zurück."""

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = self._create_user(serializer.validated_data)
            return self._get_auth_response(user, status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _create_user(self, data):
        name_parts = data['fullname'].split(' ', 1)
        return User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else ""
        )

    def _get_auth_response(self, user, status_code):
        token, _ = Token.get_or_create(user=user)
        return Response({
            "token": token.key,
            "fullname": f"{user.first_name} {user.last_name}".strip(),
            "email": user.email,
            "user_id": user.id
        }, status=status_code)


class LoginView(APIView):
    """Authentifiziert den User und gibt Token zurück."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = self._authenticate_email(serializer.validated_data)
        if user:
            return RegistrationView()._get_auth_response(user, status.HTTP_200_OK)
        return Response({"error": "Ungültige Login-Daten"}, status=status.HTTP_400_BAD_REQUEST)

    def _authenticate_email(self, data):
        try:
            user_obj = User.objects.get(email=data['email'])
            return authenticate(username=user_obj.username, password=data['password'])
        except User.DoesNotExist:
            return None
