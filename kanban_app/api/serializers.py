"""
Serializers for the Kanban board application.

Defines the structure and validation logic for converting
Django models into JSON representations for the API, aligning
data with frontend requirements.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask, TaskNote


class PriorityField(serializers.Field):
    """
    Übersetzt die Integer aus der Datenbank in Strings für das Frontend
    und Strings vom Frontend zurück in Integer für die Datenbank.
    """

    def to_representation(self, value):

        priorities = {1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return priorities.get(value, 'medium')

    def to_internal_value(self, data):

        priorities_inv = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        if data not in priorities_inv:
            raise serializers.ValidationError(f"Invalid priority: {data}")
        return priorities_inv[data]


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
    priority = PriorityField(source='priority_level', required=False)
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


class BoardSerializer(serializers.ModelSerializer):
    """
    Refactored serializer to match the flat structure required by automated tests.
    Includes title mapping, specific task/member counters, and full user objects.
    """
   
    title = serializers.CharField(source='name')
    owner_id = serializers.ReadOnlyField(source='creator.id')
    owner_data = UserMinimalSerializer(source='creator', read_only=True)
    members_data = UserMinimalSerializer(
        source='participants', many=True, read_only=True)

    # Write-only field to handle participant IDs during POST/PATCH
    members = serializers.PrimaryKeyRelatedField(
        source='participants',
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        required=False
    )

    # Computed counts for the Success Response
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBoard
        fields = [
            'id', 'title', 'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id', 'members',
            'owner_data', 'members_data'
        ]

    def get_member_count(self, obj):
        """Returns the number of participants in the board."""
        return obj.participants.count()

    def get_ticket_count(self, obj):
        """Returns total count of all tasks associated with this board."""
        return obj.all_tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Counts tasks that are in 'Backlog' (bk) or 'To-Do' status."""
        return obj.all_tasks.filter(current_status__in=['bk', 'to-do']).count()

    def get_tasks_high_prio_count(self, obj):
        """Counts tasks with High (3) or Critical (4) priority."""
        return obj.all_tasks.filter(priority_level__gte=3).count()

    def create(self, validated_data):
        """Handles board creation and many-to-many participant links."""
        participants = validated_data.pop('participants', [])
        board = ProjectBoard.objects.create(**validated_data)
        if participants:
            board.participants.set(participants)
        return board

    def update(self, instance, validated_data):
        """Handles board updates and synchronization of participants."""
        participants = validated_data.pop('participants', None)
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        return instance


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    """
    Simplified response serializer used after a successful board update.

    Returns the basic updated fields (title, owner, and members)
    in the same format as BoardSerializer but without the computationally
    heavy nested task lists and statistics.
    """
    title = serializers.CharField(source='name')
    owner_data = UserMinimalSerializer(source='creator', read_only=True)
    members_data = UserMinimalSerializer(
        source='participants', many=True, read_only=True)

    class Meta:
        model = ProjectBoard
        fields = ['id', 'title', 'owner_data', 'members_data']


class BoardDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name')
    owner_id = serializers.ReadOnlyField(source='creator.id')
    members = UserMinimalSerializer(
        source='participants', many=True, read_only=True)
    tasks = KanbanTaskSerializer(source='all_tasks', many=True, read_only=True)

    class Meta:
        model = ProjectBoard
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']
