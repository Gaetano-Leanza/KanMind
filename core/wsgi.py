"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# --- Environment Setup ---
# Set the default Django settings module for the 'wsgi' program.
# This connects the WSGI server to your project's settings file.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# --- Application Initialization ---
# This 'application' object is the entry point for WSGI-compatible web servers
# (like Gunicorn or Apache). It handles the communication between the
# web server and your Django backend.
application = get_wsgi_application()