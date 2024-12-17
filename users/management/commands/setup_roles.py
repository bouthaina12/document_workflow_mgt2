'''from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from documents.models import Document

#from users.models import CustomUser  # Replace with the actual path if different

class Command(BaseCommand):
    help = 'Sets up initial roles and permissions'

    def handle(self, *args, **kwargs):
        # Create groups
        admin_group, created = Group.objects.get_or_create(name='Administrator')
        manager_group, created = Group.objects.get_or_create(name='Manager')
        employee_group, created = Group.objects.get_or_create(name='Employee')

        # Create custom permissions (ensure they match your model definition)
        content_type = ContentType.objects.get(app_label='documents', model='document')

        permission_add_document, created = Permission.objects.get_or_create(
            codename='custom_add_document',
            name='Can custom add document',
            content_type=content_type
        )
        permission_view_document, created = Permission.objects.get_or_create(
            codename='custom_view_document',
            name='Can custom view document',
            content_type=content_type
        )

        # Assign permissions to the groups
        admin_group.permissions.add(permission_add_document, permission_view_document)
        manager_group.permissions.add(permission_view_document)

        self.stdout.write(self.style.SUCCESS('Roles and permissions have been set up successfully!'))'''

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group, User
from django.contrib.contenttypes.models import ContentType
from documents.models import Document, Workflow

class Command(BaseCommand):
    help = 'Initialiser les rôles et ajouter un utilisateur aux groupes'

    def handle(self, *args, **kwargs):
        # Créer les groupes s'ils n'existent pas
        admin_group, _ = Group.objects.get_or_create(name='Administrator')
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        employee_group, _ = Group.objects.get_or_create(name='Employee')

        # Créer l'utilisateur ou le récupérer s'il existe déjà
        user, created = User.objects.get_or_create(
            username='bouthaina',  # Remplace par le vrai nom d'utilisateur
            defaults={
                'email': 'bouthainabouchagraoui@gmail.com',  # Remplace par l'email réel
                'password': 'changeme'  # Utilise une méthode sécurisée pour définir le mot de passe
            }
        )
        
        # Set up content types
        document_ct = ContentType.objects.get_for_model(Document)
        workflow_ct = ContentType.objects.get_for_model(Workflow)
        
        # Fetch permissions
        admin_permissions = Permission.objects.filter(content_type__in=[document_ct, workflow_ct])

        # Manager permissions: Can manage workflows, but also change documents
        manager_permissions = Permission.objects.filter(
            content_type=document_ct,
            codename='change_document'
        ) | Permission.objects.filter(content_type=workflow_ct)  # Add workflow-related permissions

        # Employee permissions: Limited to uploading, viewing, changing, and deleting their own documents
        employee_permissions = Permission.objects.filter(
            content_type=document_ct,
            codename__in=['add_document', 'view_document', 'change_document', 'delete_document']
        )

        # Set permissions for each group
        admin_group.permissions.set(admin_permissions)
        manager_group.permissions.set(manager_permissions)
        employee_group.permissions.set(employee_permissions)

        print("Permissions and groups have been set up successfully.")

        # Assigner l'utilisateur au groupe Administrators
        user.groups.add(admin_group)

        # Afficher le résultat
        self.stdout.write(self.style.SUCCESS(f"Utilisateur {'créé' if created else 'récupéré'} et ajouté au groupe Administrators."))