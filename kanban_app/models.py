from django.db import models
from django.contrib.auth.models import User

class ProjectBoard(models.Model):
    """
    Zentrale Instanz für die Projektverwaltung.
    Convention: PascalCase, sprechende Namen.
    """
    name = models.CharField(max_length=120, verbose_name="Projektname")
    summary = models.TextField(max_length=400, blank=True, verbose_name="Zusammenfassung")
    creator = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_projects',
        verbose_name="Ersteller"
    )
    participants = models.ManyToManyField(
        User, 
        related_name='joined_projects',
        verbose_name="Mitglieder"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")

    class Meta:
        verbose_name = "Projekt-Board" #
        verbose_name_plural = "Projekt-Boards" #
        ordering = ['-timestamp'] #

    def __str__(self): #
        return f"Projekt: {self.name}"


class KanbanTask(models.Model):
    """
    Detaillierte Aufgabensteuerung.
    Convention: Keine Logik in Modellen.
    """
    class Status(models.TextChoices):
        BACKLOG = 'bk', 'Backlog'
        DOING = 'dg', 'In Arbeit'
        TESTING = 'ts', 'Qualitätskontrolle'
        COMPLETED = 'cp', 'Abgeschlossen'

    class Urgency(models.IntegerChoices):
        LOW = 1, 'Niedrig'
        NORMAL = 2, 'Normal'
        HIGH = 3, 'Hoch'
        CRITICAL = 4, 'Kritisch'

    label = models.CharField(max_length=200, verbose_name="Titel")
    info_text = models.TextField(blank=True, verbose_name="Beschreibung")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Fälligkeitsdatum")
    current_status = models.CharField(
        max_length=2, 
        choices=Status.choices, 
        default=Status.BACKLOG,
        verbose_name="Status"
    )
    priority_level = models.IntegerField(
        choices=Urgency.choices, 
        default=Urgency.NORMAL,
        verbose_name="Priorität"
    )
    
    parent_board = models.ForeignKey(
        ProjectBoard, 
        on_delete=models.CASCADE, 
        related_name='all_tasks', #
        verbose_name="Zugehöriges Board"
    )
    worker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='tasks_todo', #
        verbose_name="Bearbeiter"
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='tasks_to_check', #
        verbose_name="Prüfer"
    )

    class Meta:
        verbose_name = "Aufgabe" #
        verbose_name_plural = "Aufgaben" #
        ordering = ['deadline', 'priority_level'] #

    def __str__(self): #
        return f"{self.label} [{self.get_current_status_display()}]"


class TaskNote(models.Model):
    """
    Kommentarfunktion für Aufgaben.
    """
    target_task = models.ForeignKey(
        KanbanTask, 
        on_delete=models.CASCADE, 
        related_name='notes', #
        verbose_name="Ziel-Aufgabe"
    )
    writer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="written_notes",
        verbose_name="Autor"
    )
    message = models.TextField(verbose_name="Inhalt")
    posted_at = models.DateTimeField(auto_now_add=True, verbose_name="Gepostet am")

    class Meta:
        verbose_name = "Notiz" #
        verbose_name_plural = "Notizen" #
        ordering = ['-posted_at'] #

    def __str__(self): #
        return f"Notiz von {self.writer.username} zu {self.target_task.label}"