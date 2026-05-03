from django.apps import AppConfig

# --- Application Configuration ---
class KanbanAppConfig(AppConfig):
    """
    Configuration class for the 'kanban_app'.
    This class is used by Django to configure the application's behavior
    and metadata within the project.
    """
    
    # Sets the default type for primary keys (auto-incrementing 64-bit integer)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # The full Python path to the application
    name = 'kanban_app'