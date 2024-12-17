
from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

class Workflow(models.Model): 
    name = models.CharField(max_length=255) 
    description = models.CharField(max_length=255, default="Default description")
    created_by = models.ForeignKey(User, related_name='created_workflows', on_delete=models.SET_NULL, null=True) 
    def __str__(self): return self.name




class Document(models.Model):
    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]
    
    TYPE_CHOICES = [
        ('Invoice', 'Invoice'),
        ('Report', 'Report'),
        ('Contract', 'Contract')
    ]
    
    uploaded_by = models.ForeignKey(
        User, related_name='uploaded_documents', on_delete=models.SET_NULL, null=True, blank=True
    )
    content = models.TextField(default='waiting for IA')
    title = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='documents/', default='default/path/to/file.txt')
    status = models.CharField(choices=STATUS_CHOICES, max_length=10,default='Submitted')
    type = models.CharField(choices=TYPE_CHOICES, max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_to_nextcloud = models.BooleanField(default=False)
    nextcloud_url = models.URLField(blank=True, null=True)
    workflow_instance = models.OneToOneField(
    'WorkflowInstance', 
    on_delete=models.CASCADE, 
    null=True,  # Allow null values for existing rows
    blank=True  # Allow this field to be blank in forms
)

    def __str__(self):
        return self.title




class WorkflowStage(models.Model):
    workflow = models.ForeignKey(Workflow, related_name='stages', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    stage_order = models.IntegerField()
    action_required = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.workflow.name} - {self.name}'




class WorkflowInstance(models.Model):
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ]

    workflow = models.ForeignKey(Workflow, related_name='instances', on_delete=models.CASCADE)
    current_stage = models.ForeignKey(WorkflowStage, related_name='current_instances', on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, related_name='performed_transitions', on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return f'Workflow for {self.workflow.name} - {self.status}'




class StageTransition(models.Model):
    workflow_instance = models.ForeignKey(WorkflowInstance, related_name='transitions', on_delete=models.CASCADE)
    from_stage = models.ForeignKey(WorkflowStage, related_name='from_transitions', on_delete=models.CASCADE)
    to_stage = models.ForeignKey(WorkflowStage, related_name='to_transitions', on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.workflow_instance.document.title} - {self.from_stage.name} to {self.to_stage.name}'


