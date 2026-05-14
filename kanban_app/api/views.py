from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import ProjectBoard, KanbanTask, TaskNote
from .serializers import (
    BoardSerializer,
    BoardUpdateResponseSerializer,
    KanbanTaskSerializer,
    TaskNoteSerializer
)
from .permissions import IsBoardMemberOrOwner
from .permissions import IsBoardMember
from rest_framework.exceptions import PermissionDenied
# --- Board Management ---


class BoardViewSet(viewsets.ModelViewSet):
    """
    Handles all board actions including member-specific queries.
    Ensures users only see boards they are involved in or throws 403.
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsBoardMemberOrOwner]

    def get_queryset(self):
        """
        Returns boards based on action. 
        Filters list view, but allows all for detail view to trigger 403 instead of 404.
        """
        user = self.request.user

        if self.action == 'list':
            return ProjectBoard.objects.filter(
                Q(creator=user) | Q(participants=user)
            ).distinct()

        return ProjectBoard.objects.all()

    def perform_create(self, serializer):
        """Automatically sets the current user as the board creator on save."""
        serializer.save(creator=self.request.user)

    def create(self, request, *args, **kwargs):
       
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Use the standard serializer.data to ensure the flat response format
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
      
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return serializer.data to match the required documentation format
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Restricts deletion rights to the board owner only.
        The 403 here is now handled via the Permission Class or this explicit check.
        """
        instance = self.get_object()
        if instance.creator != request.user:
            return Response(
                {"detail": "You do not have permission to delete this board."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

# --- Task & Comment Management ---

class TaskViewSet(viewsets.ModelViewSet):
    """
    Manages tasks, assignments, and associated comments (TaskNotes).
    Integrates board-level permission checks to ensure data security.
    """
    serializer_class = KanbanTaskSerializer
    # Added IsBoardMember to enforce access control based on board membership
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    queryset = KanbanTask.objects.all()

    def perform_create(self, serializer):
        """
        Ensures the parent_board is correctly linked and validates user membership.
        Throws 403 Forbidden if the user is not a participant or creator of the board.
        """
        board_id = self.request.data.get('parent_board') or self.request.data.get('board')

        if board_id:
            board = get_object_or_404(ProjectBoard, id=board_id)
            
            # Explicit membership check to trigger 403 Forbidden for unauthorized users
            if self.request.user != board.creator and self.request.user not in board.participants.all():
                raise PermissionDenied("You do not have permission to create tasks in this board.")
                
            serializer.save(parent_board=board)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        Validates that the parent_board cannot be changed during an update.
        Ensures consistency of task-to-board relationships.
        """
        # Check if a board ID was provided in the request
        new_board_id = self.request.data.get('parent_board') or self.request.data.get('board')
        
        if new_board_id is not None:
            instance = self.get_object()
            # Compare requested board ID with the current board ID in the database
            if int(new_board_id) != instance.parent_board.id:
                raise ValidationError({
                    "board": "Changing the board ID is not allowed!"
                })
        
        serializer.save()

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """
        Lists all tasks where the current user is assigned as worker or reviewer.
        """
        user = request.user
        tasks = KanbanTask.objects.filter(
            Q(worker=user) | Q(reviewer=user)
        ).distinct()

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """
        Lists all tasks where the current user is assigned specifically as a reviewer.
        """
        tasks = KanbanTask.objects.filter(reviewer=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """
        Dispatches comment requests to retrieve or create notes for a specific task.
        """
        task = self.get_object()
        if request.method == 'GET':
            return self._list_comments(task)
        return self._create_comment(task, request.data)

    def _list_comments(self, task):
        """
        Retrieves and serializes all notes associated with a specific task.
        """
        notes = task.notes.all().order_by('posted_at')
        serializer = TaskNoteSerializer(notes, many=True)
        return Response(serializer.data)

    def _create_comment(self, task, data):
        """
        Validates and saves a new comment, linking it to the task and the current user.
        """
        serializer = TaskNoteSerializer(data=data)
        if serializer.is_valid():
            serializer.save(writer=self.request.user, target_task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        """
        Deletes a specific comment only if the requesting user is the original author.
        """
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
        email = request.query_params.get('email')
        if not email:
            # Die Dokumentation nutzt oft "detail" statt "error" bei Standard-DRF-Fehlern
            return Response({"detail": "Email missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            u = User.objects.get(email=email)
            return Response({
                "id": u.id,
                "email": u.email,
                # Wir nutzen hier die gleiche Logik wie in deinem UserMinimalSerializer
                "fullname": f"{u.first_name} {u.last_name}".strip() or u.username
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Wichtig für den 404-Nachweis in deiner Doku
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
