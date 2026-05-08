from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import ProjectBoard, KanbanTask, TaskNote
from .serializers import BoardSerializer, KanbanTaskSerializer, TaskNoteSerializer

# --- Board Management ---
class BoardViewSet(viewsets.ModelViewSet):
    """
    Handles all board actions including member-specific queries.
    Ensures users only see boards they are involved in.
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Returns boards where the user is either the creator or a participant."""
        user = self.request.user
        return ProjectBoard.objects.filter(
            Q(creator=user) | Q(participants=user)
        ).distinct()

    def perform_create(self, serializer):
        """Automatically sets the current user as the board creator on save."""
        serializer.save(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Restricts deletion rights to the board owner only."""
        instance = self.get_object()
        if instance.creator != request.user:
            return Response(
                {"error": "Only the owner can delete this board."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


# --- Task & Comment Management ---
class TaskViewSet(viewsets.ModelViewSet):
    """
    Manages tasks, assignments, and associated comments (TaskNotes).
    """
    serializer_class = KanbanTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = KanbanTask.objects.all()

    def perform_create(self, serializer):
        """
        Fixes the IntegrityError by ensuring the parent_board is set.
        It looks for 'parent_board' or 'parent_board_id' in the request data.
        """
        board_id = self.request.data.get('parent_board') or self.request.data.get('parent_board_id')
        
        if board_id:
            # We fetch the actual board object to ensure it exists
            board = get_object_or_404(ProjectBoard, id=board_id)
            serializer.save(parent_board=board)
        else:
            # If no board ID is provided, we let the serializer validation handle it
            serializer.save()

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """Lists all tasks where the current user is assigned as the worker."""
        tasks = KanbanTask.objects.filter(worker=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """Lists all tasks where the current user is assigned as the reviewer."""
        tasks = KanbanTask.objects.filter(reviewer=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Dispatches comment requests to list or create methods."""
        task = self.get_object()
        if request.method == 'GET':
            return self._list_comments(task)
        return self._create_comment(task, request.data)

    def _list_comments(self, task):
        """Helper to retrieve and serialize all notes for a specific task."""
        notes = task.notes.all().order_by('posted_at')
        serializer = TaskNoteSerializer(notes, many=True)
        return Response(serializer.data)

    def _create_comment(self, task, data):
        """Helper to validate and save a new comment for a task."""
        serializer = TaskNoteSerializer(data=data)
        if serializer.is_valid():
            serializer.save(writer=self.request.user, target_task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        """Deletes a comment if the requesting user is the original author."""
        task = self.get_object()
        comment = get_object_or_404(TaskNote, id=comment_id, target_task=task)

        if comment.writer != request.user:
            return Response(
                {"error": "Only the author can delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Utility Views ---
class EmailCheckView(APIView):
    """
    Endpoint to validate existing users via email for task assignments.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Extracts email from query params and initiates user search."""
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email missing."}, status=status.HTTP_400_BAD_REQUEST)
        return self._find_user_by_email(email)

    def _find_user_by_email(self, email):
        """Searches for a user by email and returns public profile data."""
        try:
            u = User.objects.get(email=email)
            return Response({
                "id": u.id,
                "email": u.email,
                "fullname": f"{u.first_name} {u.last_name}".strip() or u.username
            })
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)