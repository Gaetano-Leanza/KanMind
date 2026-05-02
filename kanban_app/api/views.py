from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


from ..models import ProjectBoard, KanbanTask, TaskNote
from .serializers import BoardSerializer, KanbanTaskSerializer, TaskNoteSerializer


class BoardViewSet(viewsets.ModelViewSet):
    """
    Verwaltet alle Board-Aktionen inkl. mitgliederspezifischer Abfragen.
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Liefert nur Boards, bei denen der User Creator oder Teilnehmer ist."""
        user = self.request.user
        return ProjectBoard.objects.filter(
            Q(creator=user) | Q(participants=user)
        ).distinct()

    def perform_create(self, serializer):
        """Setzt den aktuellen User automatisch als Board-Eigentümer."""
        serializer.save(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Stellt sicher, dass nur der Eigentümer ein Board löschen darf."""
        instance = self.get_object()
        if instance.creator != request.user:
            return Response(
                {"error": "Nur der Eigentümer kann das Board löschen."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class TaskViewSet(viewsets.ModelViewSet):
    """
    Verwaltet Aufgaben sowie deren Zuweisungen und Kommentare.
    """
    serializer_class = KanbanTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = KanbanTask.objects.all()

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """Gibt alle Tasks zurück, bei denen der User als Bearbeiter gesetzt ist."""
        tasks = KanbanTask.objects.filter(worker=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """Gibt alle Tasks zurück, bei denen der User als Prüfer gesetzt ist."""
        tasks = KanbanTask.objects.filter(reviewer=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Verwaltet das Abrufen und Erstellen von Kommentaren zu einer Task."""
        task = self.get_object()
        if request.method == 'GET':
            return self._list_comments(task)
        return self._create_comment(task, request.data)

    def _list_comments(self, task):
        notes = task.notes.all().order_by('posted_at')
        serializer = TaskNoteSerializer(notes, many=True)
        return Response(serializer.data)

    def _create_comment(self, task, data):
        serializer = TaskNoteSerializer(data=data)
        if serializer.is_valid():
            serializer.save(writer=self.request.user, target_task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        """Löscht einen Kommentar, sofern der User der Autor ist."""
        task = self.get_object()
        comment = get_object_or_404(TaskNote, id=comment_id, target_task=task)

        if comment.writer != request.user:
            return Response(
                {"error": "Nur der Ersteller kann den Kommentar löschen."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailCheckView(APIView):
    """
    Endpoint zur Validierung existierender User via Email.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email fehlt."}, status=status.HTTP_400_BAD_REQUEST)
        return self._find_user_by_email(email)

    def _find_user_by_email(self, email):
        user = KanbanTask.objects.filter(
            models.User.objects.filter(email=email).exists())
        # Hinweis: Hier nutzen wir den direkten Zugriff auf das User-Modell
        from django.contrib.auth.models import User
        try:
            u = User.objects.get(email=email)
            return Response({
                "id": u.id,
                "email": u.email,
                "fullname": f"{u.first_name} {u.last_name}".strip() or u.username
            })
        except User.DoesNotExist:
            return Response({"error": "Nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
