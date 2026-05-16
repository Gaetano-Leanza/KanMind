from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.http import Http404

from ..models import ProjectBoard, KanbanTask, TaskNote
from .serializers import (
    BoardDetailSerializer,
    BoardSerializer,
    BoardUpdateResponseSerializer,
    KanbanTaskSerializer,
    TaskNoteSerializer
)
from .permissions import IsBoardMemberOrOwner
from .permissions import IsBoardMember


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

    def get_serializer_class(self):
        """
        Dynamically assigns the correct serializer based on the request action.
        Uses a detailed serializer for single retrievals and a flat one for listing.
        """
        if self.action == 'retrieve':
            return BoardDetailSerializer
        return BoardSerializer

    def perform_create(self, serializer):
        """Automatically sets the current user as the board creator on save."""
        serializer.save(creator=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Creates a new board and returns the response in a flat JSON structure.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Updates an existing board (PUT/PATCH) and utilizes a custom response 
        serializer to ensure the returned data strictly matches frontend requirements.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = BoardUpdateResponseSerializer(instance)

        return Response(response_serializer.data)

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
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    queryset = KanbanTask.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Intercepts the creation process to manually validate board existence.
        Immediately raises a 404 Not Found if the board ID is invalid, 
        preventing the default 400 Bad Request from the serializer.
        """
        board_id = request.data.get('board') or request.data.get('parent_board')

        if board_id is not None:
            # Handle edge cases where the ID might be wrapped in a list (e.g., [4000])
            if isinstance(board_id, list):
                board_id = board_id[0]

            # Bulletproof check: Does a board with this ID actually exist?
            if not ProjectBoard.objects.filter(id=board_id).exists():
                # Raise a 404 immediately before serializer validation occurs
                raise Http404("This board does not exist.")

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Ensures the parent_board is correctly linked and validates user membership.
        Throws 403 Forbidden if the user is not a participant or creator of the board.
        """
        board = serializer.validated_data.get('parent_board')

        if board:
            if self.request.user != board.creator and self.request.user not in board.participants.all():
                raise PermissionDenied(
                    "You do not have permission to create tasks in this board.")

        serializer.save()

    def perform_update(self, serializer):
        """
        Validates that the parent_board cannot be changed during an update.
        Ensures consistency of task-to-board relationships.
        """
        new_board_id = self.request.data.get('parent_board') or self.request.data.get('board')

        if new_board_id is not None:
            instance = self.get_object()

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
        """
        Retrieves a user by email and returns their basic profile data.
        Returns 404 if the email does not correspond to an existing user.
        """
        email = request.query_params.get('email')
        if not email:
            return Response({"detail": "Email missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            u = User.objects.get(email=email)
            return Response({
                "id": u.id,
                "email": u.email,
                "fullname": f"{u.first_name} {u.last_name}".strip() or u.username
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Crucial for the 404 requirement in the API documentation
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)