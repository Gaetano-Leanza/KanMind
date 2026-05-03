#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This script is the main entry point for managing the project via the terminal.
It handles tasks like starting the server, creating migrations, and managing the database.
"""
import os
import sys


def main():
    """
    Run administrative tasks.

    1. Sets the default settings module.
    2. Attempts to import and execute Django management commands.
    """
    # Link the script to your project's settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    try:
        # Import the command line execution utility from Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Error handling if Django is not found (e.g., virtual environment not active)
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Execute the command passed via the terminal (e.g., 'runserver')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # The starting point of the script when called directly
    main()
