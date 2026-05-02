# KannMind Backend

This is the Django-based REST API for the KannMind Task Management System.

## Features
- **Authentication**: Custom login and registration via `auth_app`.
- **Project Boards**: Create and manage Kanban boards with participants.
- **Task Management**: CRUD operations for tasks including status updates and priorities.
- **Comments**: Chronological task notes with ownership protection.

## Installation & Setup
1. **Clone the repository**
2. **Create a virtual environment**: `python -m venv venv`
3. **Activate venv**: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Run migrations**: `python manage.py migrate`
6. **Start server**: `python manage.py runserver`

## Tech Stack
- Python / Django
- Django Rest Framework (DRF)
- Token Authentication