from django.db import models
from django.contrib.auth.models import User

class ProjectBoard(models.Model):
    """
    Zentrale Instanz für die Projektverwaltung. 
    Name 'ProjectBoard' statt nur 'Board', um Kollisionen zu vermeiden.
    """
    name = models.CharField(max_length=120)  # 'name' statt 'title'
    summary = models.TextField(max_length=400, blank=True)
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_projects') # 'PROTECT' ist sicherer als 'CASCADE'
    participants = models.ManyToManyField(User, related_name='joined_projects')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Projekt: {self.name}"


class KanbanTask(models.Model):
    """
    Detaillierte Aufgabensteuerung. Nutzt ein anderes System für 
    die Status-Verwaltung als die klassische Liste.
    """
    # Hier nutzen wir Unterklassen für die Auswahl (modernerer Django-Stil)
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

    label = models.CharField(max_length=200) # 'label' statt 'title'
    info_text = models.TextField(blank=True) # 'info_text' statt 'description'
    deadline = models.DateTimeField(null=True, blank=True)
    
    # Die neuen Auswahlfelder
    current_status = models.CharField(
        max_length=2, 
        choices=Status.choices, 
        default=Status.BACKLOG
    )
    priority_level = models.IntegerField(
        choices=Urgency.choices, 
        default=Urgency.NORMAL
    )
    
    # Verknüpfungen
    parent_board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='all_tasks')
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_todo')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_to_check')

    def __str__(self):
        return f"{self.label} [{self.current_status}]"


class TaskNote(models.Model):
    """
    Kommentarfunktion, hier 'TaskNote' genannt.
    """
    target_task = models.ForeignKey(KanbanTask, on_delete=models.CASCADE, related_name='notes')
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)