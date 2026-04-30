from django.db import models
from django.contrib.auth.models import User

class ProjectBoard(models.Model):
    """
    Zentrale Instanz für die Projektverwaltung.
    Erfüllt die Convention: PascalCase, sprechender Name.
    """
    name = models.CharField(max_length=120)
    summary = models.TextField(max_length=400, blank=True)
    creator = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_projects'
    )
    participants = models.ManyToManyField(User, related_name='joined_projects')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Projekt-Board"
        verbose_name_plural = "Projekt-Boards"
        ordering = ['-timestamp']

    def __str__(self):
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

    label = models.CharField(max_length=200)
    info_text = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    current_status = models.CharField(
        max_length=2, 
        choices=Status.choices, 
        default=Status.BACKLOG
    )
    priority_level = models.IntegerField(
        choices=Urgency.choices, 
        default=Urgency.NORMAL
    )
    
    parent_board = models.ForeignKey(
        ProjectBoard, 
        on_delete=models.CASCADE, 
        related_name='all_tasks'
    )
    worker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='tasks_todo'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='tasks_to_check'
    )

    class Meta:
        verbose_name = "Aufgabe"
        verbose_name_plural = "Aufgaben"
        ordering = ['deadline', 'priority_level']

    def __str__(self):
        return f"{self.label} [{self.current_status}]"


class TaskNote(models.Model):
    """
    Kommentarfunktion.
    """
    target_task = models.ForeignKey(
        KanbanTask, 
        on_delete=models.CASCADE, 
        related_name='notes'
    )
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notiz"
        verbose_name_plural = "Notizen"
        ordering = ['-posted_at']

    def __str__(self):
        return f"Notiz von {self.writer.username}"