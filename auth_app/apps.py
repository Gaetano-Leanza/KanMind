from django.apps import AppConfig

# --- App Configuration ---

class AuthAppConfig(AppConfig):
    """
    Configuration class for the 'auth_app'.
    This handles the app's initialization and registration within the Django project.
    """
    name = 'auth_app'
    
    # Optional: You could add a verbose name here for the Admin interface
    # verbose_name = "Benutzerverwaltung & Authentifizierung"