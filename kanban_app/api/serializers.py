from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask, TaskNote

# --- Helper Serializers ---

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Reduced user serializer for nested representations.
    Concatenates names into a single 'fullname' field for the frontend.
    """
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        """Helper to create a display name, falling back to username if names are missing."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


# --- Comment & Task Serialization ---

class TaskNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    Maps internal database fields (message, posted_at) to API-standard names.
    """
    author = serializers.SerializerMethodField()
    content = serializers.CharField(source='message')
    created_at = serializers.DateTimeField(
        source='posted_at', format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = TaskNote
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        """Retrieves the full name of the comment author."""
        return f"{obj.writer.first_name} {obj.writer.last_name}".strip() or obj.writer.username


class KanbanTaskSerializer(serializers.ModelSerializer):
    """
    Main serializer for tasks.
    Uses 'source' to align internal model fields with the frontend's naming convention.
    """
    title = serializers.CharField(source='label')
    description = serializers.CharField(source='info_text', allow_blank=True)
    status = serializers.CharField(source='current_status')
    priority = serializers.SerializerMethodField()
    
    # Nested display data (Read-Only)
    assignee = UserMinimalSerializer(source='worker', read_only=True)
    reviewer = UserMinimalSerializer(read_only=True)
    due_date = serializers.DateTimeField(source='deadline', format="%Y-%m-%d")
    comments_count = serializers.IntegerField(source='notes.count', read_only=True)

    # Fields for write operations (Primary Key based)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='worker', write_only=True, required=False, allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='reviewer', write_only=True, required=False, allow_null=True
    )
    board = serializers.PrimaryKeyRelatedField(
        queryset=ProjectBoard.objects.all(), source='parent_board', required=False
    )

    class Meta:
        model = KanbanTask
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id',
            'due_date', 'comments_count'
        ]

    def get_priority(self, obj):
        """Converts integer priority levels to human-readable string tags."""
        priorities = {1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return priorities.get(obj.priority_level, 'medium')


# --- Board Serialization ---

class BoardSerializer(serializers.ModelSerializer):
    """
    Complex serializer for project boards.
    Includes aggregated data (counts) and nested task/member objects.
    """
    title = serializers.CharField(source='name')
    owner_id = serializers.ReadOnlyField(source='creator.id')
    
    # Nested collections
    members = UserMinimalSerializer(source='participants', many=True, read_only=True)
    tasks = KanbanTaskSerializer(source='all_tasks', many=True, read_only=True)
    
    # Aggregated statistics for the dashboard
    member_count = serializers.IntegerField(source='participants.count', read_only=True)
    ticket_count = serializers.IntegerField(source='all_tasks.count', read_only=True)
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBoard
        fields = [
            'id', 'title', 'owner_id', 'members', 'tasks',
            'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count'
        ]

    def get_tasks_to_do_count(self, obj):
        """Calculates the number of tasks currently in the backlog."""
        return obj.all_tasks.filter(current_status='bk').count()

    def get_tasks_high_prio_count(self, obj):
        """Calculates the number of tasks marked with high priority (Level 3)."""
        return obj.all_tasks.filter(priority_level=3).count()