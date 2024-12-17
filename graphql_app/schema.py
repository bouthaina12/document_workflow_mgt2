import graphene
from graphene_django.types import DjangoObjectType
from documents.models import Document, Workflow, WorkflowStage, WorkflowInstance, StageTransition
from django.contrib.auth.models import User
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, PromptNode
from haystack.pipelines import Pipeline
from haystack.schema import Document as HaystackDocument
from haystack.nodes.prompt.invocation_layer.hugging_face import HFLocalInvocationLayer
from transformers import GPTNeoForCausalLM

import logging
logging.basicConfig(level=logging.DEBUG)
import torch

from documents.services.haystack_service import handle_query  # Updated import
from documents.services.haystack_service import document_store  # Updated import

#shema
# Define User Type
class UserType(DjangoObjectType):
    class Meta:
        model = User

# Define WorkflowInstance Type
class WorkflowInstanceType(DjangoObjectType):
    class Meta:
        model = WorkflowInstance

# Define Document Type
class DocumentType(DjangoObjectType):
    class Meta:
        model = Document

    workflow_instance = graphene.Field(WorkflowInstanceType)  # Match snake_case field name

    def resolve_workflow_instance(self, info):
        # Debugging
        print(f"Resolving workflow_instance for document ID: {self.id}")
        return self.workflow_instance  # ORM uses snake_case

# Define Workflow Type
class WorkflowType(DjangoObjectType):
    class Meta:
        model = Workflow
    createdBy = graphene.Field(UserType)  # Use camelCase for created_by
    documents = graphene.List(DocumentType)

    def resolve_createdBy(self, info):
        return self.created_by

    def resolve_documents(self, info):
        workflow_instances = self.workflowinstance_set.all()
        documents = Document.objects.filter(workflow_instance__in=workflow_instances)
        return documents

# Define WorkflowStage Type
class WorkflowStageType(DjangoObjectType):
    class Meta:
        model = WorkflowStage

# Define StageTransition Type
class StageTransitionType(DjangoObjectType):
    class Meta:
        model = StageTransition
##########################################################################################################################


# Define RelevantDocumentType for structured document metadata
class RelevantDocumentType(graphene.ObjectType):
    content = graphene.String()
    metadata = graphene.JSONString()  # This can handle the dynamic nature of metadata

# Define QueryDocumentsResponseType to represent the structure of the response
class QueryDocumentsResponseType(graphene.ObjectType):
    query = graphene.String()
    response = graphene.String()
    relevant_documents = graphene.List(RelevantDocumentType) # Use the new RelevantDocumentType

# Queries
class Query(graphene.ObjectType):
    workflows = graphene.List(WorkflowType)
    documents = graphene.List(DocumentType)
    workflow_instances = graphene.List(WorkflowInstanceType)
    users = graphene.List(UserType)

    documents_by_status = graphene.List(DocumentType, status=graphene.String())
    workflow_with_users = graphene.Field(WorkflowType, id=graphene.Int())
###########################################################################



    query_documents = graphene.Field(QueryDocumentsResponseType, query=graphene.String(required=True))  # Return structured response

##############################################################################################""


    # Existing resolvers
    def resolve_workflows(self, info):
        return Workflow.objects.prefetch_related('created_by', 'workflowinstance_set').all()

    def resolve_documents(self, info):
        doc = Document.objects.get(id=5)
        print(doc.workflow_instance)
        return Document.objects.all()

    def resolve_workflow_instance(self, info):
        instance = self.workflow_instance
        print(f"Resolving workflow_instance: {instance}")
        if instance is None:
            print(f"Document ID {self.id} has no workflow_instance.")
        return instance

    def resolve_users(self, info):
        return User.objects.all()

    def resolve_documents_by_status(self, info, status):
        return Document.objects.filter(status=status)

    def resolve_workflow_with_users(self, info, id):
        return Workflow.objects.prefetch_related('created_by').get(id=id)

    def resolve_query_documents(self, info, query):
        logging.debug(f"Processing query: {query}")
        
        # Call the function with document_store
        response = handle_query(query)
        
        logging.debug(f"Response: {response}")
        
        return QueryDocumentsResponseType(
            query=query,
            response=response['response'],
            relevant_documents=[
                RelevantDocumentType(content=doc.content, metadata=doc.meta)
                for doc in response['relevant_documents']
            ],
        )

"""# Step 3: Initialize the Retriever and PromptNode (with OpenLLAMA)
retriever = BM25Retriever(document_store=document_store)
prompt_node = PromptNode(
    model_name_or_path="OpenLLAMA",  # Switch to OpenLLAMA as required
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
    invocation_layer_class=HFLocalInvocationLayer
)"""

# Mutations
class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)

    def mutate(self, info, username, email, password):
        user = User(username=username, email=email)
        user.set_password(password)  # Hash the password
        user.save()
        return CreateUser(user=user)


class UpdateUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        username = graphene.String()
        email = graphene.String()
        password = graphene.String()

    user = graphene.Field(UserType)

    def mutate(self, info, id, username=None, email=None, password=None):
        user = User.objects.get(pk=id)
        if username:
            user.username = username
        if email:
            user.email = email
        if password:
            user.set_password(password)  # Update hashed password
        user.save()
        return UpdateUser(user=user)


class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = User.objects.get(pk=id)
        user.delete()
        return DeleteUser(success=True)
    

class CreateWorkflow(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()

    workflow = graphene.Field(WorkflowType)

    def mutate(self, info, name, description="Default description"):
        workflow = Workflow(name=name, description=description)
        workflow.save()
        return CreateWorkflow(workflow=workflow)


class UpdateWorkflow(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()

    workflow = graphene.Field(WorkflowType)

    def mutate(self, info, id, name=None, description=None):
        workflow = Workflow.objects.get(pk=id)
        if name:
            workflow.name = name
        if description:
            workflow.description = description
        workflow.save()
        return UpdateWorkflow(workflow=workflow)


class DeleteWorkflow(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        workflow = Workflow.objects.get(pk=id)
        workflow.delete()
        return DeleteWorkflow(success=True)
class CreateDocument(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        content = graphene.String()
        type = graphene.String()

    document = graphene.Field(lambda: DocumentType)

    def mutate(self, info, title, content, type):
        document = Document.objects.create(title=title, content=content, type=type)
        return CreateDocument(document=document)

class UpdateDocument(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        title = graphene.String()
        content = graphene.String()

    document = graphene.Field(lambda: DocumentType)

    def mutate(self, info, id, title=None, content=None):
        document = Document.objects.get(pk=id)
        if title:
            document.title = title
        if content:
            document.content = content
        document.save()
        return UpdateDocument(document=document)

class DeleteDocument(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            document = Document.objects.get(pk=id)
            document.delete()
            return DeleteDocument(success=True)
        except Document.DoesNotExist:
            return DeleteDocument(success=False)

class Mutation(graphene.ObjectType):
# workflow mutations

    create_workflow = CreateWorkflow.Field()
    update_workflow = UpdateWorkflow.Field()
    delete_workflow = DeleteWorkflow.Field()
# User mutations
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
# doc mutations

    create_document = CreateDocument.Field()
    update_document = UpdateDocument.Field()
    delete_document = DeleteDocument.Field()

# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)



"""query {
  workflows {
    id
    name
    description
    createdBy {
      id
      username
    }
    documents {
      id
      title
      status
      content
      createdAt
      updatedAt
      workflowInstance {
        id
        # Any other fields from the WorkflowInstance model can be queried here
      }
    }
  }
}
query
{
  workflowWithUsers(id: 1) {
    id
    name
    users {
      id
      username
    }
  }
  documentsByStatus(status: "pending") {
    id
    name
    status
  }
}

query {
  queryDocuments(query: "What is the status of project X?") {
    query
    response
    relevant_documents {
      content
      metadata
    }
  }
}
"""