from django.contrib import admin
from .models import ProjectBoard, KanbanTask, TaskNote

# --- Admin Configuration for Project Boards ---
@admin.register(ProjectBoard)
class ProjectBoardAdmin(admin.ModelAdmin):
    """
    Configuration for the ProjectBoard model in the admin interface.
    Defines visible columns, filters, and search functionality.
    """
    # Columns displayed in the list view
    list_display = ('id', 'name', 'creator', 'timestamp')
    
    # Filter options in the right sidebar
    list_filter = ('timestamp', 'creator')
    
    # Fields used for the search bar
    search_fields = ('name', 'summary')

# --- Admin Configuration for Kanban Tasks ---
@admin.register(KanbanTask)
class KanbanTaskAdmin(admin.ModelAdmin):
    """
    Detailed configuration for Kanban tasks.
    Enables quick editing of status and priority levels directly from the list.
    """
    # Columns displayed in the list view
    list_display = ('label', 'current_status', 'priority_level', 'deadline', 'worker')
    
    # Sidebar filters for status, priority, and board affiliation
    list_filter = ('current_status', 'priority_level', 'parent_board')
    
    # Fields searchable by the user
    search_fields = ('label', 'info_text')
    
    # Allows changing these fields directly without opening the detail view
    list_editable = ('current_status', 'priority_level')

# --- Basic Registration ---
# Simple registration for TaskNotes without custom configuration
admin.site.register(TaskNote)