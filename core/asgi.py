"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# --- Environment Setup ---
# Set the default Django settings module for the 'asgi' program.
# This ensures that the asynchronous server knows which settings to use.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# --- Asynchronous Application Initialization ---
# The 'application' variable is the entry point for ASGI-compatible web servers 
# (such as Daphne or Uvicorn). This allows your project to handle asynchronous 
# protocols like WebSockets in addition to standard HTTP.
application = get_asgi_application()