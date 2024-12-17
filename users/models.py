# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

''' class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('Administrator', 'Administrator'),
        ('Manager', 'Manager'),
        ('Employee', 'Employee'),
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Employee')
    user_role = models.OneToOneField('UserRole', on_delete=models.CASCADE, related_name='user')

    def save(self, *args, **kwargs):
        if not self.role:
            self.role = 'Employee'
        super().save(*args, **kwargs)

    def has_permission(self, permission_name):
        # Custom method to check user permissions (implement logic as needed)
        return permission_name in [perm.codename for perm in self.user_permissions.all()]


class UserRole(models.Model):
    group_name = models.CharField(max_length=100)
    permissions = models.ManyToManyField('auth.Permission')

    def add_permission(self, permission):
        self.permissions.add(permission)

    def remove_permission(self, permission):
        self.permissions.remove(permission)
        '''