from django.contrib import admin
from .models import ProjectBoard, KanbanTask, TaskNote


@admin.register(ProjectBoard)
class ProjectBoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'creator', 'timestamp')
    list_filter = ('timestamp', 'creator')
    search_fields = ('name', 'summary')

@admin.register(KanbanTask)
class KanbanTaskAdmin(admin.ModelAdmin):
    list_display = ('label', 'current_status', 'priority_level', 'deadline', 'worker')
    list_filter = ('current_status', 'priority_level', 'parent_board')
    search_fields = ('label', 'info_text')
    list_editable = ('current_status', 'priority_level')

admin.site.register(TaskNote)