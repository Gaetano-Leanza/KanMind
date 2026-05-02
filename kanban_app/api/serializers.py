from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask, TaskNote


class UserMinimalSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class TaskNoteSerializer(serializers.ModelSerializer):
    """ Serializer für Kommentare gemäß image_04ead4.png """
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
        priorities = {1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return priorities.get(obj.priority_level, 'medium')


class BoardSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name')
    owner_id = serializers.ReadOnlyField(source='creator.id')
    members = UserMinimalSerializer(
        source='participants', many=True, read_only=True)
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
            'id', 'title', 'owner_id', 'members', 'tasks',
            'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count'
        ]

    def get_tasks_to_do_count(self, obj):
        return obj.all_tasks.filter(current_status='bk').count()

    def get_tasks_high_prio_count(self, obj):
        return obj.all_tasks.filter(priority_level=3).count()
