from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

# --- User Authentication & Registration ---

class RegistrationView(APIView):
    """
    Handles the registration of new users.
    Creates a Django User object and generates an authentication token.
    """
    
    # Allows anyone to access this endpoint without being logged in
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Processes registration data: Validates input, creates user, and returns token.
        """
        # Extracting data from the request body
        email = request.data.get('email')
        password = request.data.get('password')
        repeated_password = request.data.get('repeated_password')
        fullname = request.data.get('fullname')

        # 1. Validation: Check if passwords match
        if password != repeated_password:
            return Response(
                {'error': 'Passwörter stimmen nicht überein.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validation: Ensure the email (used as username) is unique
        if User.objects.filter(username=email).exists():
            return Response(
                {'error': 'Ein User mit dieser E-Mail existiert bereits.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Execution: Create the user and store the full name in first_name
        user = User.objects.create_user(
            username=email, email=email, password=password)
        user.first_name = fullname
        user.save()

        # 4. Token Generation: Create or retrieve a token for the new user
        token, created = Token.objects.get_or_create(user=user)

        # Return the relevant session data and the token key
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'fullname': user.first_name
        }, status=status.HTTP_201_CREATED)