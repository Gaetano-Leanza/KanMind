from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.api.urls')),
    path('api/kanban/', include('kanban_app.api.urls')),
]
