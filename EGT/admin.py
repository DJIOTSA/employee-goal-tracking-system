from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    AdministratorProfile, 
    EmployeeProfile, 
    Enterprise, 
    Category,
    SignupCodeEmployee,
    )

from .forms import MyUserCreationForm, MyUserChangeForm
from EGT.models import SignupCode, PasswordResetCode, EmailChangeCode
from django.contrib.auth.models import Group

from django.contrib.auth import get_user_model
MyUser = get_user_model()


class SignupCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'ipaddr', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'code', 'ipaddr')

    def has_add_permission(self, request, obj=None):
        return False


class SignupCodeInline(admin.TabularInline):
    model = SignupCode
    fieldsets = (
        (None, {
            'fields': ('code', 'ipaddr', 'created_at')
        }),
    )
    readonly_fields = ('code', 'ipaddr', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False
    
class SignupCodeInlineEmployee(admin.TabularInline):
    model = SignupCodeEmployee
    fieldsets = (
        (None, {
            'fields': ('code', 'ipaddr', 'created_at', 'enterprise_name', 'employee_password', "added_by")
        }),
    )
    readonly_fields = ('code', 'ipaddr', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'code')

    def has_add_permission(self, request, obj=None):
        return False


class PasswordResetCodeInline(admin.TabularInline):
    model = PasswordResetCode
    fieldsets = (
        (None, {
            'fields': ('code', 'created_at')
        }),
    )
    readonly_fields = ('code', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


class EmailChangeCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'email', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'code', 'email')

    def has_add_permission(self, request, obj=None):
        return False


class EmailChangeCodeInline(admin.TabularInline):
    model = EmailChangeCode
    fieldsets = (
        (None, {
            'fields': ('code', 'email', 'created_at')
        }),
    )
    readonly_fields = ('code', 'email', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', )}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name',"cv", "picture")}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('User Role'), {'fields': ('role',)}),
        (_('User Status'), {"fields": ('status',)})

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )

    form = MyUserChangeForm
    add_form = MyUserCreationForm
    inlines = [SignupCodeInline, SignupCodeInlineEmployee, EmailChangeCodeInline, PasswordResetCodeInline]
    list_display = ('email', 'is_verified', 'first_name', 'last_name','role',
                    'is_staff')
    search_fields = ('first_name', 'last_name', 'email', 'role')
    ordering = ('date_joined',)
    filter_horizontal = ()


admin.site.register(MyUser, UserAdmin)
admin.site.register(SignupCode, SignupCodeAdmin)
admin.site.register(SignupCodeEmployee, SignupCodeAdmin)
admin.site.register(PasswordResetCode, PasswordResetCodeAdmin)
admin.site.register(EmailChangeCode, EmailChangeCodeAdmin)
admin.site.register(AdministratorProfile)
admin.site.register(Enterprise)
admin.site.register(Category)
admin.site.register(EmployeeProfile)
