from django.contrib.auth.models import User
from rest_framework import serializers

# --- Authentication Serializers ---

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration logic including password validation.
    Maps frontend fields like 'fullname' to Django's 'first_name'.
    """
    fullname = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        # Ensure the password is never included in any GET response
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        """
        Performs cross-field validation for passwords and email uniqueness.
        Returns validated data or raises a ValidationError.
        """
        # Security check: Password confirmation
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError(
                {"repeated_password": "Passwörter stimmen nicht überein."})

        # Integrity check: Ensure email is not already in use
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Email bereits registriert."})

        return data

    def create(self, validated_data):
        """
        Finalizes user creation. 
        Uses the email as the username to streamline the login process.
        """
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('fullname', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Simple non-model serializer for login attempts.
    Validates the format of the required email and password fields.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)