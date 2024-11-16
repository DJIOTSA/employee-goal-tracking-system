from django.contrib.auth.models import Group
from rest_framework import permissions, authentication

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import check_user_status

IS_EMPLOYEE_ADMIN = "THE USER IS AN EMPLOYEE ADMIN"

class CustomPermission(permissions.DjangoModelPermissions):
    """
    OVERRIDE THE PERMISSIONS MAPPING TO CONFIGURE THE VIEW PERMISSIONS 
    OF DJANGO MODELS
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view)
    
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

class CheckAdministratorGroupMixin:
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name="Administrators").exists():
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
        
class CheckEmployeeGroupMixin:
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name="Employees").exists():
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
        
class CheckAdministratorEmployeeGroupMixin:
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        employee_group = request.user.groups.filter(name='Employees').exists()
        administrator_group = request.user.groups.filter(name='Administrators').exists()
        if employee_group or administrator_group:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
        
        
class CheckEmployeeAdminGroupMixin:
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Administrators').exists() or request.user.groups.filter(name="Admins").exists():
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied
        

        
def checkEmployeeAdminGroupMixin(self):
        if not check_user_status(self.request.user):
            raise PermissionDenied
        if not self.request.user.groups.filter(Q(name="Administrators") | Q(name="Admins") ).exists():
            raise PermissionDenied
        if self.request.user.groups.filter(name="Admins").exists():
            return IS_EMPLOYEE_ADMIN
        
def checkAdministratorEmployeeGroupMixin(self):
        if not check_user_status(self.request.user):
            raise PermissionDenied
        if not self.request.user.groups.filter(Q(name="Administrators") | Q(name="Employees") ).exists():
            raise PermissionDenied
        
def checkAdministratorGroupMixin(self):
        if not check_user_status(self.request.user):
            raise PermissionDenied
        if not self.request.user.groups.filter(Q(name="Administrators")).exists():
            raise PermissionDenied
        

class AdministratorPermissionsAuthentication:
    pass

class AdministratorPermissionsAuthentication:
    pass
