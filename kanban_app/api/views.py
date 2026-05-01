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


class RegistrationView(APIView):
    """
    Erstellt einen neuen Benutzer basierend auf der API-Dokumentation.
    Entspricht exakt der Vorgabe: POST /api/registration/
    """
    def post(self, request):
        data = request.data
        fullname = data.get('fullname', '')
        email = data.get('email')
        password = data.get('password')
        repeated_password = data.get('repeated_password')

        # 1. Validierung der Eingaben
        if not email or not password or not fullname:
            return Response({"error": "Bitte füllen Sie alle Felder aus."}, status=status.HTTP_400_BAD_REQUEST)

        if password != repeated_password:
            return Response({"error": "Passwörter stimmen nicht überein."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "Diese Email ist bereits registriert."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Namen für das Django-Modell aufteilen (First Name / Last Name)
        name_parts = fullname.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # 3. User-Objekt erstellen
        # Wir nutzen die Email als Username, da Django ein Username-Feld erzwingt
        user = User.objects.create_user(
            username=email, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # 4. Token für den neuen User generieren
        token, created = Token.get_or_create(user=user)

        # 5. Erfolgsantwort gemäß Screenshot
        return Response({
            "token": token.key,
            "fullname": fullname,
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)