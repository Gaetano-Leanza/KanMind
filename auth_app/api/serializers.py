from django.contrib.auth.models import User
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    """Verarbeitet die Benutzerregistrierung inkl. Passwortprüfung."""
    fullname = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError(
                "Passwörter stimmen nicht überein.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email bereits registriert.")
        return data


class LoginSerializer(serializers.Serializer):
    """Validiert die Logindaten (Email & Passwort)."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
