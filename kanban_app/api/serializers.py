"""
Serializers for the Kanban board application.

Defines the structure and validation logic for converting
Django models into JSON representations for the API, aligning
data with frontend requirements.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask, TaskNote


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer providing a streamlined representation of User objects.

    Used to deliver full 'OwnerData' and 'MemberData' with ID, email,
    and a concatenated full name to fulfill the 'Board has expected
    properties' frontend requirement.
    """
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        """
        Retrieves the user's full name.

        Returns the concatenated first and last names, or falls back to
        the username if the name fields are empty.
        """
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class TaskNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments with frontend-aligned naming.

    Converts model fields like 'message' and 'posted_at' to API-level
    names 'content' and 'created_at', while using nested data.
    """
    author = serializers.SerializerMethodField()
    content = serializers.CharField(source='message')
    created_at = serializers.DateTimeField(
        source='posted_at', format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = TaskNote
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        """
        Retrieves the note author's full name.

        Uses the same fallback logic as UserMinimalSerializer to
        ensure a display name is always returned.
        """
        return f"{obj.writer.first_name} {obj.writer.last_name}".strip() or obj.writer.username


class KanbanTaskSerializer(serializers.ModelSerializer):
    """
    Main serializer for tasks, using nested representations and custom field mappings.

    Alters model field names ('label', 'info_text', 'deadline', etc.)
    for frontend consumption. Includes nested user details and
    write-only PrimaryKey fields for creation/update.
    """
    title = serializers.CharField(source='label')
    description = serializers.CharField(source='info_text', allow_blank=True)
    status = serializers.CharField(source='current_status')
    priority = serializers.SerializerMethodField()

    assignee = UserMinimalSerializer(source='worker', read_only=True)
    reviewer = UserMinimalSerializer(read_only=True)
    due_date = serializers.DateTimeField(source='deadline', format="%Y-%m-%d")
    comments_count = serializers.IntegerField(
        source='notes.count', read_only=True)

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
        """
        Converts the integer priority_level into a descriptive string.

        Defaults to 'medium' if the numerical value is unexpected.
        """
        priorities = {1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return priorities.get(obj.priority_level, 'medium')


class BoardSerializer(serializers.ModelSerializer):
    """
    Standard serializer for Boards, including aggregated stats and nested lists.

    Combines primary board data with related tasks, membership info,
    and computed counts for total tickets, status distribution, and
    priority levels.
    """
    title = serializers.CharField(source='name')
    owner_id = serializers.ReadOnlyField(source='creator.id')
    owner_data = UserMinimalSerializer(source='creator', read_only=True)
    members_data = UserMinimalSerializer(
        source='participants', many=True, read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        source='participants',
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        required=False
    )

    tasks = KanbanTaskSerializer(source='all_tasks', many=True, read_only=True)
    member_count = serializers.IntegerField(
        source='participants.count', read_only=True)
    ticket_count = serializers.IntegerField(
        source='all_tasks.count', read_only=True)

    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBoard
        fields = [
            'id', 'title', 'owner_id', 'owner_data', 'members_data',
            'members',
            'tasks', 'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count'
        ]

    def create(self, validated_data):
        """
        Creates a new board and handles the nested participant relationships.

        Pops the participants from validated_data before model creation
        and then sets them using the many-to-many manager.
        """
        participants = validated_data.pop('participants', [])
        board = ProjectBoard.objects.create(**validated_data)
        if participants:
            board.participants.set(participants)
        return board

    def update(self, instance, validated_data):
        """
        Updates an existing board instance and handles the related participants.

        Extracts participants and calls the parent update method before
        synchronizing the many-to-many relationship.
        """
        participants = validated_data.pop('participants', None)
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        return instance

    def get_tasks_to_do_count(self, obj):
        """Calculates the count of tasks with statuses in the 'To-Do' list."""
        return obj.all_tasks.filter(current_status__in=['bk', 'to-do']).count()

    def get_tasks_high_prio_count(self, obj):
        """Calculates the count of tasks with priority level 3 or higher."""
        return obj.all_tasks.filter(priority_level__gte=3).count()


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    """
    Simplified response serializer used after a successful board update.

    Returns the basic updated fields (title, owner, and members)
    in the same format as BoardSerializer but without the computationally
    heavy nested task lists and statistics.
    """
    title = serializers.CharField(source='name')
    owner_data = UserMinimalSerializer(source='creator', read_only=True)
    members_data = UserMinimalSerializer(source='participants', many=True, read_only=True)

    class Meta:
        model = ProjectBoard
        fields = ['id', 'title', 'owner_data', 'members_data']