from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask


class UserMinimalSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class KanbanTaskSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='label')
    description = serializers.CharField(source='info_text', allow_blank=True)
    status = serializers.CharField(source='current_status')
    priority = serializers.SerializerMethodField()
    assignee = UserMinimalSerializer(source='worker', read_only=True)
    reviewer = UserMinimalSerializer(read_only=True)
    due_date = serializers.DateTimeField(source='deadline', format="%Y-%m-%d")

    class Meta:
        model = KanbanTask
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date'
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
