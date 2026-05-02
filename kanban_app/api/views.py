from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ..models import ProjectBoard, KanbanTask, TaskNote
from .serializers import BoardSerializer, KanbanTaskSerializer, TaskNoteSerializer


class LoginView(APIView):
    """ Authentifiziert einen Benutzer via Email und Passwort. """

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user:
            token, created = Token.get_or_create(user=user)
            return Response({
                "token": token.key,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_200_OK)

        return Response({"error": "Ungültige Anfragedaten."}, status=status.HTTP_400_BAD_REQUEST)


class RegistrationView(APIView):
    """ Erstellt einen neuen Benutzer basierend auf der API-Dokumentation. """

    def post(self, request):
        data = request.data
        fullname = data.get('fullname', '')
        email = data.get('email')
        password = data.get('password')
        repeated_password = data.get('repeated_password')

        if not email or not password or not fullname:
            return Response({"error": "Bitte füllen Sie alle Felder aus."}, status=status.HTTP_400_BAD_REQUEST)

        if password != repeated_password:
            return Response({"error": "Passwörter stimmen nicht überein."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Diese Email ist bereits registriert."}, status=status.HTTP_400_BAD_REQUEST)

        name_parts = fullname.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        token, created = Token.get_or_create(user=user)
        return Response({
            "token": token.key,
            "fullname": fullname,
            "email": user.email,
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)


class BoardViewSet(viewsets.ModelViewSet):
    """
    Verwaltet alle Board-Aktionen:
    GET /api/boards/ (Liste der eigenen/beteiligten Boards)
    POST /api/boards/ (Erstellen eines neuen Boards)
    GET /api/boards/{id}/ (Einzelansicht mit Tasks)
    PATCH /api/boards/{id}/ (Mitglieder/Titel aktualisieren)
    DELETE /api/boards/{id}/ (Board löschen)
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ProjectBoard.objects.filter(
            Q(creator=user) | Q(participants=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator != request.user:
            return Response({"error": "Nur der Eigentümer kann das Board löschen."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class TaskViewSet(viewsets.ModelViewSet):
    """
    Verwaltet alle Task-Aktionen inkl. spezieller Filter und Kommentare.
    """
    serializer_class = KanbanTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = KanbanTask.objects.all()

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        tasks = KanbanTask.objects.filter(worker=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        tasks = KanbanTask.objects.filter(reviewer=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        task = self.get_object()
        
        if request.method == 'GET':
            notes = task.notes.all().order_by('posted_at')
            serializer = TaskNoteSerializer(notes, many=True)
            return Response(serializer.data)

        if request.method == 'POST':
            serializer = TaskNoteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(writer=request.user, parent_task=task)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        task = self.get_object()
        comment = get_object_or_404(TaskNote, id=comment_id, parent_task=task)
        
        if comment.writer != request.user:
            return Response({"error": "Nur der Ersteller kann den Kommentar löschen."}, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailCheckView(APIView):
    """ Prüft, ob eine Email existiert und gibt User-Daten zurück. """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email-Parameter fehlt."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            return Response({
                "id": user.id,
                "email": user.email,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.username
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Email nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)