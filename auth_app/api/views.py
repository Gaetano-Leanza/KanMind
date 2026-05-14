from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# --- User Onboarding & Authentication ---

class RegistrationView(APIView):
    """
    Handles new user registration.
    Validates input, creates a User instance, and issues an initial Auth Token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Creates a new user and returns user data along with a unique Token.
        """
        email = request.data.get('email')
        password = request.data.get('password')
        repeated_password = request.data.get('repeated_password')
        fullname = request.data.get('fullname', '')

        # Validation: Password confirmation check
        if password != repeated_password:
            return Response({'password': ['Passwords do not match.']}, status=status.HTTP_400_BAD_REQUEST)

        # Validation: Check if email (used as username) is already taken
        if User.objects.filter(username=email).exists():
            return Response({'email': ['A user with this email already exists.']}, status=status.HTTP_400_BAD_REQUEST)

        # Create user object and assign full name to first_name field
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=fullname
        )

        # Generate or retrieve the authentication token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'fullname': user.first_name
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Handles user login.
    Authenticates credentials and returns a valid Auth Token for session management.
    """
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Validates credentials and retrieves the user's Auth Token.
        """
        # Frontend provides 'email' which serves as the Django 'username'
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Django's built-in authentication against username and password
        user = authenticate(username=email, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email,
                'fullname': user.first_name
            }, status=status.HTTP_200_OK)
        else:
            # Returns a 400 status if credentials do not match (geändert für den Test!)
            return Response(
                {'non_field_errors': ['Invalid credentials']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class EmailCheckView(APIView):
    """
    Checks if an email is already registered and returns user details.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Handles GET requests to check if a user exists and returns their profile.
        """
        email = request.query_params.get('email')
        
        try:
            # We search for the user by email
            user = User.objects.get(username=email)
            
            # If found, we return the data the frontend needs for the "Added members" list
            return Response({
                'exists': True,
                'id': user.id,
                'email': user.email,
                'fullname': f"{user.first_name}".strip() or user.username
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # If not found, we just return that it doesn't exist
            return Response({
                'exists': False
            }, status=status.HTTP_200_OK)