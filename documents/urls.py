from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (WorkflowViewSet, DocumentViewSet, 
                    WorkflowStageViewSet, WorkflowInstanceViewSet, 
                    StageTransitionViewSet)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-stages', WorkflowStageViewSet, basename='workflowstage')
router.register(r'workflow-instances', WorkflowInstanceViewSet, basename='workflowinstance')
router.register(r'stage-transitions', StageTransitionViewSet, basename='stagetransition')


urlpatterns = [
    path('', include(router.urls)),

]