from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask, TaskNote

# --- Helper Serializers ---

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer providing the full 'OwnerData' and 'MemberData' objects.
    This fulfills the 'Board has expected properties' requirement.
    """
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        """Returns the full name or username as a fallback."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


# --- Comment & Task Serialization ---

class TaskNoteSerializer(serializers.ModelSerializer):
    """Serializer for task comments with frontend-aligned naming."""
    author = serializers.SerializerMethodField()
    content = serializers.CharField(source='message')
    created_at = serializers.DateTimeField(
        source='posted_at', format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = TaskNote
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        return f"{obj.writer.first_name} {obj.writer.last_name}".strip() or obj.writer.username


class KanbanTaskSerializer(serializers.ModelSerializer):
    """Main serializer for tasks using nested representations."""
    title = serializers.CharField(source='label')
    description = serializers.CharField(source='info_text', allow_blank=True)
    status = serializers.CharField(source='current_status')
    priority = serializers.SerializerMethodField()
    
    assignee = UserMinimalSerializer(source='worker', read_only=True)
    reviewer = UserMinimalSerializer(read_only=True)
    due_date = serializers.DateTimeField(source='deadline', format="%Y-%m-%d")
    comments_count = serializers.IntegerField(source='notes.count', read_only=True)

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
        priorities = {1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return priorities.get(obj.priority_level, 'medium')


# --- Board Serialization ---

class BoardSerializer(serializers.ModelSerializer):
    """
    Standard serializer for Boards. 
    Includes aggregated stats and nested owner/member data.
    """
    title = serializers.CharField(source='name')
    
    owner_id = serializers.ReadOnlyField(source='creator.id')
    owner_data = UserMinimalSerializer(source='creator', read_only=True)
    
    # Anzeige der Mitglieder als Objekte
    members_data = UserMinimalSerializer(source='participants', many=True, read_only=True)
    
    # Erlaubt das Senden von IDs beim POST/PATCH
    participants = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True, required=False
    )
    
    tasks = KanbanTaskSerializer(source='all_tasks', many=True, read_only=True)
    
    member_count = serializers.IntegerField(source='participants.count', read_only=True)
    ticket_count = serializers.IntegerField(source='all_tasks.count', read_only=True)
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBoard
        fields = [
            'id', 'title', 'owner_id', 'owner_data', 'members_data', 'participants', 'tasks',
            'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count'
        ]

    def create(self, validated_data):
        """Sorgt dafür, dass Mitglieder beim Erstellen gespeichert werden."""
        participants = validated_data.pop('participants', [])
        board = ProjectBoard.objects.create(**validated_data)
        if participants:
            board.participants.set(participants)
        return board

    def update(self, instance, validated_data):
        """Sorgt dafür, dass Mitglieder beim Bearbeiten (PATCH) aktualisiert werden."""
        participants = validated_data.pop('participants', None)
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        return instance

    def get_tasks_to_do_count(self, obj):
        return obj.all_tasks.filter(current_status__in=['bk', 'to-do']).count()

    def get_tasks_high_prio_count(self, obj):
        return obj.all_tasks.filter(priority_level__gte=3).count()


class BoardUpdateResponseSerializer(BoardSerializer):
    """
    Nutzt jetzt die Logik des Haupt-Serializers, 
    um sicherzustellen, dass PATCH-Antworten identisch sind.
    """
    class Meta(BoardSerializer.Meta):
        fields = ['id', 'title', 'owner_data', 'members_data']