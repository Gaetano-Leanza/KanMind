from rest_framework import serializers
from kanban_app.models import Board,Task,Comment
from auth_app.models import User
from auth_app.api.serializers import UserSerializer



class SimplifiedUserSerializer(serializers.ModelSerializer):
    """
    Simplified user serializer that returns only ID, email,
    and full name.
    """
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        """
        Combines first and last name into a full name.
        """
        return f"{obj.first_name} {obj.last_name}".strip()


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer for representing boards including
    members, owner, and various counts
    (members, tickets, task statuses).
    """
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
    )
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'members', 'owner_id',
            'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count'
        ]

    def get_member_count(self, obj):
        """Returns the number of members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Returns the total number of tasks in the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Returns the number of tasks with status 'to_do'."""
        return obj.tasks.filter(status='to_do').count()

    def get_tasks_high_prio_count(self, obj):
        """Returns the number of tasks with high priority."""
        return obj.tasks.filter(priority='high').count()


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a board with title
    and members specified (members are write-only).
    """
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
    )

    class Meta:
        model = Board
        fields = ['title', 'members']


class TasksofBoardSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks of a board including
    comment count and simplified user info
    for assignees and reviewers.
    """
    comments_count = serializers.SerializerMethodField()
    assignee = SimplifiedUserSerializer( read_only=True)
    reviewer = SimplifiedUserSerializer( read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]

    def get_comments_count(self, obj):
        """Returns the number of comments for a task."""
        return obj.comments.count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for boards with full
    user information for members and tasks.
    """
    members = UserSerializer(many=True, read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    tasks = TasksofBoardSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating boards, showing owner and
    members as read-only fields using UserSerializer.
    """
    owner_data = UserSerializer(read_only=True, source='owner')
    members_data = UserSerializer(many=True, read_only=True, source='members')

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_data', 'members_data']


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating tasks,
    expects 'assignee_id' and 'reviewer_id' as foreign key IDs.
    """
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = Task
        exclude = ['assignee', 'reviewer']

    def create(self, validated_data):
        """
        Creates a task and assigns assignee and reviewer.
        """
        assignee = validated_data.pop('assignee_id')
        reviewer = validated_data.pop('reviewer_id')

        task = Task.objects.create(**validated_data,
                                   assignee=assignee,
                                   reviewer=reviewer)
       
        return task

    def update(self, instance, validated_data):
        """
        Updates task fields and sets assignee and reviewer
        if new values are provided.
        """
        assignee = validated_data.pop('assignee_id', None)
        reviewer = validated_data.pop('reviewer_id', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if assignee is not None:
            instance.assignee=assignee
        if reviewer is not None:
            instance.reviewer=reviewer
            
        instance.save()

        return instance


class TaskSerializer(serializers.ModelSerializer):
    """
    Full task serializer including board relation,
    user info for assignees and reviewers, and comment count.
    """
    board = serializers.PrimaryKeyRelatedField(queryset=Board.objects.all())
    comments_count = serializers.SerializerMethodField()
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer( read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]

    def get_comments_count(self, obj):
        """Returns the number of comments for a task."""
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single task
    with assignees and reviewers as nested user data.
    """
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date'
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating comments with only the content field.
    """

    class Meta:
        model = Comment
        fields = ['content']


class CommentResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for returning comments with author's username.
    """
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']

    
    def get_author(self, obj):
     return f"{obj.author.first_name} {obj.author.last_name}".strip()
