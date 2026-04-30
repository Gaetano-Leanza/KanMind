from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import ProjectBoard, KanbanTask 

class KanbanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanTask
        fields = ['id', 'label', 'current_status', 'priority_level', 'deadline']

    def validate_label(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Der Titel ist zu kurz!")
        return value