from rest_framework import serializers
from .models import Workflow, Document, WorkflowStage, WorkflowInstance, StageTransition

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'type', 'status', 'uploaded_by', 'workflow_instance','file_path','created_at']
        read_only_fields = ['uploaded_by','type', 'content','synced_to_nextcloud','nextcloud_url']


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = '__all__'


class WorkflowStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStage
        fields = '__all__'


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowInstance
        fields = '__all__'


class StageTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StageTransition
        fields = '__all__'