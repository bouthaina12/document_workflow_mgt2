from django.http import  HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets
from sklearn.pipeline import Pipeline
from .models import Workflow, Document, WorkflowStage, WorkflowInstance, StageTransition
from .serializers import (WorkflowSerializer, DocumentSerializer,WorkflowStageSerializer, WorkflowInstanceSerializer,StageTransitionSerializer)

import requests
from requests.auth import HTTPBasicAuth
import PyPDF2
from rest_framework.exceptions import ValidationError
from transformers import pipeline
from rest_framework.permissions import IsAuthenticated


from django.contrib.auth.decorators import permission_required
from rest_framework.decorators import action
from rest_framework.response import Response

from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, PromptNode
from haystack import Document as HaystackDocument

from haystack.nodes.prompt.invocation_layer.hugging_face import HFLocalInvocationLayer
import torch






class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


class WorkflowStageViewSet(viewsets.ModelViewSet):
    queryset = WorkflowStage.objects.all()
    serializer_class = WorkflowStageSerializer


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer


class StageTransitionViewSet(viewsets.ModelViewSet):
    queryset = StageTransition.objects.all()
    serializer_class = StageTransitionSerializer




# Initialize the HuggingFace pipelines
classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
summarizer = pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]



    def perform_create(self, serializer):
        """Handles file upload, text extraction, summarization, and classification."""
        # Check if the file is uploaded
        file = self.request.FILES.get('file_path')
        if not file:
            raise ValidationError("A file must be uploaded.")

        # Extract text from the PDF file
        pdf_reader = PyPDF2.PdfReader(file)
        document_content = ""
        for page in pdf_reader.pages:
            document_content += page.extract_text() or ""
        print("Extracted Content:", document_content)

        # Summarize the content using HuggingFace pipeline
        summarized_content = summarizer(document_content, max_length=1000000, min_length=5, do_sample=False)
        summary_text = summarized_content[0]['summary_text']

        # Classify the summarized content
        result = classifier(document_content, candidate_labels=['Invoice', 'Contract', 'Report'])
        document_type = result['labels'][0]  # Get the most likely label

        # Save the document locally with metadata
        document_instance = serializer.save(
            uploaded_by=self.request.user,
            content=summary_text,
            type=document_type,
        )
       # Synchronize with Nextcloud
        try:
            self.synchronize_with_nextcloud(file, document_instance)
        except Exception as e:
            print(f"Nextcloud synchronization error: {str(e)}")
            document_instance.synced_to_nextcloud = False
            document_instance.save()

    def synchronize_with_nextcloud(self, file, document_instance):
        """Uploads the document to Nextcloud."""
        # Nextcloud credentials and upload URL
        NEXTCLOUD_URL = "https://use08.thegood.cloud/remote.php/dav/files"
        NEXTCLOUD_USERNAME = "bouthainabouchagraoui@gmail.com"
        NEXTCLOUD_PASSWORD = "Changeme123***"
        NEXTCLOUD_UPLOAD_DIR = f"{NEXTCLOUD_URL}/{NEXTCLOUD_USERNAME}/uploaded_documents"

        # Step 1: Ensure the Nextcloud folder exists
        folder_path = f"{NEXTCLOUD_UPLOAD_DIR}"
        response = requests.request(
            "MKCOL",
            folder_path,
            auth=HTTPBasicAuth(NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
        )

        # MKCOL responses: 201 = Created, 405 = Already Exists
        if response.status_code not in [201, 405]:
            raise Exception(f"Failed to create Nextcloud folder: {response.status_code}, {response.text}")

        # Step 2: Upload the file
        file_path = f"{NEXTCLOUD_UPLOAD_DIR}/{file.name}"
        upload_response = requests.put(
            file_path,
            data=file,
            auth=HTTPBasicAuth(NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
        )

        if upload_response.status_code in [201, 204]:  # 201 = Created, 204 = Updated
            upload_url = file_path
            print(f"File successfully uploaded to Nextcloud: {upload_url}")
            document_instance.synced_to_nextcloud = True
            document_instance.nextcloud_url = upload_url  # Store Nextcloud URL in the model
            document_instance.save()
        else:
            raise Exception(f"Nextcloud upload failed: {upload_response.status_code}, {upload_response.text}")

    def get_queryset(self):
        """Filter documents by user """
        user = self.request.user
        queryset = Document.objects.all()
        if user.groups.filter(name="Employees").exists():
            queryset = queryset.filter(uploaded_by=user)
        return queryset
    
    @permission_required('documents.change_document', raise_exception=True)
    def update_status(self, request, pk):
        document = get_object_or_404(Document, pk=pk)

        # Only managers and admins can update status
        if request.user.groups.filter(name__in=['Managers', 'Administrators']).exists():
            if request.method == 'POST':
                new_status = request.POST.get('status')
                if new_status in dict(Document.STATUS_CHOICES):
                    document.status = new_status
                    document.save()
                    return redirect('document_list')  # Correctly inside the method
                else:
                    return HttpResponseForbidden("Invalid status selected.")
        return HttpResponseForbidden("You don't have permission to update status.")
    
    @permission_required('documents.delete_document', raise_exception=True)
    def delete_document(request, pk):
        document = get_object_or_404(Document, pk=pk)
        if request.user == document.uploaded_by:
            document.delete()
            return redirect('document_list')
        return HttpResponseForbidden("You don't have permission to delete this document.")
#########################################################################################################################################


    def initialize_haystack_pipeline(self):
            """Initializes the Haystack pipeline."""
            # Step 1: Initialize the Document Store
            document_store = InMemoryDocumentStore()

            # Step 2: Fetch documents from the database and index them
            queryset = Document.objects.all()  
            haystack_documents = [
                HaystackDocument(
                    content=db_doc.content,
                    meta={
                        "title": db_doc.title,
                        "type": db_doc.type,
                        "status": db_doc.status,
                        "created_at": db_doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "uploaded_by": db_doc.uploaded_by.username if db_doc.uploaded_by else "Anonymous",
                    }
                )
                for db_doc in queryset
            ]
            document_store.write_documents(haystack_documents)

            # Step 3: Initialize the Retriever
            retriever = BM25Retriever(document_store=document_store)

            # Step 4: Initialize the PromptNode
            prompt_node = PromptNode(
                model_name_or_path="EleutherAI/gpt-neo-1.3B",  # Use a lighter version or change to a supported model
                model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},  # Use GPU if available
                invocation_layer_class=HFLocalInvocationLayer  # Specify the local invocation layer
            )

            # Step 5: Create a custom pipeline
            pipeline = Pipeline()
            pipeline.add_node(component=retriever, name="Retriever", inputs=["Query"])
            pipeline.add_node(component=prompt_node, name="Generator", inputs=["Retriever"])

            return pipeline

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def query_documents(self, request):
            """
            Custom endpoint to process user queries with the Haystack pipeline.
            """
            user_query = request.data.get("query", "")
            if not user_query:
                return Response({"error": "No query provided"}, status=400)

            # Initialize the Haystack pipeline
            pipeline = self.initialize_haystack_pipeline()

            # Run the pipeline with the user's query
            result = pipeline.run(query=user_query)

            # Format the response
            if result.get("answers"):  # Checking if answers are found in the result
                return Response({
                    "query": user_query,
                    "response": result["answers"][0].answer,  # First answer from the results
                    "relevant_documents": [
                        {
                            "content": doc.content,
                            "metadata": doc.meta if hasattr(doc, 'meta') else None  # Safely access 'meta'
                        }
                        for doc in result["documents"]
                    ]
                })
            else:
                return Response({
                    "query": user_query,
                    "response": "No relevant documents found or unable to generate a response."
                })
#########################################################################################################################################

'''
class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='assign-workflow')
    def assign_to_workflow(self, request, pk=None):
        """Assigns a document to a specified workflow."""
        document = self.get_object()
        workflow_id = request.data.get('workflow_id')

        try:
            workflow = Workflow.objects.get(id=workflow_id)
            document.workflows.add(workflow)
            document.save()
            return Response({'message': f'Document {document.title} assigned to workflow {workflow.name}.'})
        except Workflow.DoesNotExist:
            return Response({'error': 'Workflow not found.'}, status=404)
        '''



























