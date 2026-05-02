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
                {"repeated_password": "Passwörter stimmen nicht überein."})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Email bereits registriert."})

        return data

    def create(self, validated_data):
        """Erstellt den User und mappt die Frontend-Felder auf Django-Felder."""
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('fullname', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Validiert die Logindaten (Email & Passwort)."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
