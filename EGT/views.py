from django.shortcuts import render, HttpResponse, redirect
from .serializers import (
    EnterpriseSerializer, 
    CategorySerializer, 
    UserSerializer,
    EmployeeProfileSerializer,
    AdministratorProfileSerializer,
    EnterpriseUpdateSerializer,
    DeactivateEmployeeSerializer,
    EnterpriseEmployeeListSerializer,
    EmployeeCategorySerializer,
    EnterpriseCreateSerializer,
    EnterpriseSetEmployeeAdminSerializer,
    EmployeeProfileChangeSalarySerializer,
    UserUpdate2Serializer,
    UserDetailSerializer,
    CategoryEnterpriseSerializer,

)

from .models import (
    MyUser,
    Enterprise, 
    Category, 
    EmployeeProfile,
    AdministratorProfile,
    Administrator,
    Employee,
    Status,
    SignupCode,
    SignupCodeEmployee,
    EmailChangeCode, 
    PasswordResetCode,
    send_multi_format_email,
)

from .models import (
    add_new_employee,
    add_new_administrator,
    set_enterprise_code,
    user_belong_to_enterprise,
    check_user_enterprise_status,
    send_multi_format_email,
    deactivate_enterprise_pdg_admin_and_add_admin,
    check_user_status,
    deactivate_user,
    set_employee_category,
    _get_user_profile,
    get_employee_enterprise_salary,
    activate_user,
    return_jsonfield_value, 
)

import json
from django.forms.models import model_to_dict
from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate, login, logout
# from django.core.exceptions import PermissionDenied

from rest_framework.pagination import PageNumberPagination

User = get_user_model()

from django.views.generic import ListView
from .permissions import (
    checkAdministratorGroupMixin, 
    checkEmployeeAdminGroupMixin,
    checkAdministratorEmployeeGroupMixin,
    IS_EMPLOYEE_ADMIN,
)
from django.contrib.auth.models import Group

import datetime
from django.db.models import Q
from datetime import date
from ipware import get_client_ip

from django.conf import settings

from django.utils.translation import gettext as _

from rest_framework import  authentication, permissions, generics
from rest_framework import status
from rest_framework.authtoken.models import Token

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from employee_goal_tracker.celery import app 


from django.core.exceptions import PermissionDenied

from EGT.serializers import (
    SignupSerializer, 
    LoginSerializer,
    PasswordResetSerializer,
    PasswordResetVerifiedSerializer,
    EmailChangeSerializer,
    UserSerializer,
    SignupEmployeeSerializer,
    ChangePdgOrAdministratorSerializer,
    UserUpdateSerializer,

)
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from rest_framework import serializers

import string
import random

domain_name = "localhost:8000/"
def generate_password():
    """ 
    This function randomly create a string password of 8 characters containing uppercase and 
    lowercase of english alphabet and 
    """
    password_length = 8
    password_characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(password_characters) for i in range(password_length))
    print(password)
    return password


"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    User and authentication view section 
"""

class SignupAdministrator(APIView):
    """ Sign Up as ADMINISTRATOR USER."""
    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']
            password = serializer.data['password']
            first_name = serializer.data['first_name']
            last_name = serializer.data['last_name']
            
            must_validate_email = getattr(settings, "AUTH_EMAIL_VERIFICATION", True)

            try:
                user = get_user_model().objects.get(email=email)
                if user.is_verified:
                    content = {'detail': _('Email address already taken.')}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Delete old signup codes
                    signup_code = SignupCode.objects.get(user=user)
                    signup_code.delete()
                except SignupCode.DoesNotExist:
                    pass

            except get_user_model().DoesNotExist:
                user = get_user_model().objects.create_user(email=email, role= MyUser.Role.ADMINISTRATOR, status = Status.ACTIVE)

            # Set user fields provided
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.is_administrator = True
            user.is_employee = False

            if not must_validate_email:
                user.is_verified = True
                send_multi_format_email.delay('welcome_email',
                                        {'email': user.email, },
                                        target_email=user.email)
            user.save()

            if must_validate_email:
                # Create and associate signup code
                client_ip = get_client_ip(request)[0]
                if client_ip is None:
                    client_ip = '0.0.0.0'    # Unable to get the client's IP address
                signup_code = SignupCode.objects.create_signup_code(user, client_ip)
                signup_code.send_signup_email()

            content = {'email': email, 'first_name': first_name,
                       'last_name': last_name, 'role': MyUser.Role.ADMINISTRATOR}
            return Response(content, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignupEmployee(APIView):
    """ 
    Sign Up as Employee USER this operation can only be perform
    by an administrator user. 
    """
    serializer_class= SignupEmployeeSerializer
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def post(self, request, format=None):
        # check user group permission
        checkAdministratorGroupMixin(self)

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # remove extra data from the serializer
        password = generate_password()
        enterprise_name = serializer.validated_data['enterprise_name']
        enterprise_name = enterprise_name.upper()
        email = serializer.validated_data['user_email']
        
        try:
            if Enterprise.objects.filter(name=enterprise_name).exists() == False and  Enterprise.objects.get(name=enterprise_name).status != Status.ACTIVE:
                content = {'detail': _(f"This enterprise '{enterprise_name}' is not active or does not exists.")}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            
            enterprise = Enterprise.objects.get(name=enterprise_name)
            
        except Enterprise.DoesNotExist:
            content ={'detail': _(f'Enterprise {enterprise_name} does not exists.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        first_name = serializer.data['first_name']
        last_name = serializer.data['last_name']

        # set default value of must_validate_email to true
        must_validate_email = getattr(settings, "AUTH_EMAIL_VERIFICATION", True)

        try:
            user = get_user_model().objects.get(email=email)
            if user.is_verified and user.role == MyUser.Role.EMPLOYEE:
                client_ip = get_client_ip(request)[0]
                if client_ip is None:
                    client_ip = '0.0.0.0'    # Unable to get the client's IP address
                signup_code = SignupCodeEmployee.objects.create_signup_code(user=user, ipaddr= client_ip)
                signup_code.enterprise_name= enterprise_name
                signup_code.employee_password = password
                signup_code.added_by = request.user.email
                signup_code.save()
                signup_code.send_add_employee_email()

                # add_new_employee(user, Enterprise.objects.get(name=enterprise_name), '')
                content = {'detail': _('Employee was successfully added. We are now waiting for user confirmation.')}
                return Response(content, status=status.HTTP_200_OK)

            try:
                # Delete old signup codes
                signup_code = SignupCodeEmployee.objects.get(user=user)
                signup_code.delete()
            except SignupCodeEmployee.DoesNotExist:
                pass
                    
        except get_user_model().DoesNotExist:
            user = get_user_model().objects.create_user(email=email, role=MyUser.Role.EMPLOYEE, status=Status.ACTIVE)

        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.is_administrator = False
        user.is_employee = True
        if not must_validate_email:
            user.is_verified = True
            send_multi_format_email.delay('welcome_email',
                                    {'email': user.email, },
                                    target_email=user.email),
        user.save()

        if must_validate_email:
            # Create and associate signup code
            client_ip = get_client_ip(request)[0]
            if client_ip is None:
                client_ip = '0.0.0.0'    # Unable to get the client's IP address
            signup_code = SignupCodeEmployee.objects.create_signup_code(user=user, ipaddr= client_ip)
            signup_code.enterprise_name= enterprise_name
            signup_code.employee_password = password
            signup_code.added_by = request.user.email
            signup_code.save()
            signup_code.send_add_employee_email()

            content = {
                'email': email, 
                'first_name': first_name,
                'last_name': last_name, 
                'role': MyUser.Role.EMPLOYEE, 
                'enterprise_name': enterprise_name, 
                
            }
            
            return Response(content, status=status.HTTP_201_CREATED)



class SignupVerify(APIView, TemplateView):
    authentication_classes = []
    permission_classes = (AllowAny,)
    template_name = 'EGT/signup_verified.html'

    def get(self, request, format=None):
        code = request.GET.get('code', '')
        verified = SignupCode.objects.set_user_is_verified(code)

        if verified:
            try:
                signup_code = SignupCode.objects.get(code=code)
                signup_code.send_signup_verify('welcome_email')
                signup_code.delete()
                
            except SignupCodeEmployee.DoesNotExist:
                pass

            content = {'detail': _('Email address verified.')}
            # return Response(content, status=status.HTTP_200_OK)
            return HttpResponseRedirect(reverse('signup-verified'), content)
            
        else:
            content = {'detail': _('Unable to verify user.')}
            # return Response(content, status=status.HTTP_400_BAD_REQUEST)
            return HttpResponseRedirect(reverse('signup-not-verified'), content)


class AddEmployeeVerified(TemplateView):
    template_name= 'EGT/add_employee_verified.html'


class AddEmployeeNotVerified(TemplateView):
    template_name = 'EGT/add_employee_not_verified.html'


class SignupVerifyEmployee(APIView, TemplateView):
    authentication_classes = []
    permission_classes = (AllowAny,)
    template_name = 'EGT/signup_verified.html'

    def get(self, request, format=None):
        code = request.GET.get('code', '')
        verified = SignupCodeEmployee.objects.set_user_is_verified(code)
        
        if verified:
            try:
                signup_code = SignupCodeEmployee.objects.get(code=code)
                # signup_code.add_employee()
                enterprise_name = signup_code.enterprise_name
                employee_password = signup_code.employee_password
                user = signup_code.user
                added_by = signup_code.added_by
                company = Enterprise.objects.get(name=enterprise_name.upper())
                if add_new_employee(user, company, employee_password, added_by):
                    signup_code.send_signup_verify('welcome_email')
                    signup_code.delete()
                    content = {'detail': _('Email address verified.')}
                    # return Response(content, status=status.HTTP_200_OK)
                    return HttpResponseRedirect(reverse('add-employee-verified'))
                else:
                    content = {'detail': _('An Error occur.')}
                    # return Response(content, status=status.HTTP_400_BAD_REQUEST)
                    return HttpResponseRedirect(reverse('add-employee-not-verified'))

            except SignupCodeEmployee.DoesNotExist:
                pass

            
        content = {'detail': _('Unable to verify user.')}
        # return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return HttpResponseRedirect(reverse('add-employee-not-verified'))


class UserUpdate(generics.RetrieveUpdateAPIView):
    """ User Update picture, name and cv """
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = get_user_model().objects.all()
    serializer_class  = UserUpdateSerializer
    lookup_key = "pk"

    def perform_update(self, serializer):
        # check user group permission
        checkAdministratorEmployeeGroupMixin(self)

        obj = self.get_object()

        if obj != self.request.user:
            raise PermissionDenied
        
        picture = serializer.validated_data["picture"]
        first_name = serializer.validated_data["first_name"]
        last_name = serializer.validated_data["last_name"]
        cv = serializer.validated_data["cv"]

        return serializer.save()


class SignupVerifiedFrontEnd(TemplateView):
    template_name = 'EGT/signup_verified.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_variable'] = 'my_value'
        return context


class SignupNotVerifiedFrontEnd(TemplateView):
    template_name = 'EGT/signup_not_verified.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_variable'] = 'my_value'
        return context


class Login(APIView):
    """ Authenticated the user and assign user Authorizations """
    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']
            password = serializer.data['password']
            user = authenticate(email=email, password=password)

            if user:
                if user.is_verified:
                    if user.is_active:
                        login(request, user)
                        token, created = Token.objects.get_or_create(user=user)
                        return Response({'token': token.key},
                                        status=status.HTTP_200_OK)
                    else:
                        content = {'detail': _('User account not active.')}
                        return Response(content,
                                        status=status.HTTP_401_UNAUTHORIZED)
                else:
                    content = {'detail':
                               _('User account not verified.')}
                    return Response(content, status=status.HTTP_401_UNAUTHORIZED)
            else:
                content = {'detail':
                           _('Unable to login with provided credentials.')}
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class Logout( APIView):
    queryset = User.objects.all()
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication )
    permission_classes = (AllowAny, )

    def get(self, request, format=None):
        """
        Remove all auth tokens owned by request.user.
        """
        tokens = Token.objects.filter(user=request.user)
        for token in tokens:
            token.delete()
        logout(request)
        content = {'success': _('User logged out.')}
        return Response(content, status=status.HTTP_200_OK)


class PasswordReset( APIView,):
    """ 
    This view check if the user is active and then create a passwordResetCode
    With the for that user that will be used to identify the user and to change his password with 
    the new one sent by the user
    """
    queryset = User.objects.all()
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    serializer_class = PasswordResetSerializer

    def post(self, request, format=None):
        """Sends a password reset email to the user specified in the request."""
         # check user group permission
        checkAdministratorEmployeeGroupMixin(self)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = self.request.user.email
            new_password = serializer.data['new_password']

            try:
                user = get_user_model().objects.get(email=email)

                # Delete all unused password reset codes
                PasswordResetCode.objects.filter(user=user).delete()

                if user.is_verified and user.is_active:
                    password_reset_code = \
                        PasswordResetCode.objects.create_password_reset_code(user=user, new_password=new_password)
                    password_reset_code.send_password_reset_email()
                    content = {'email': email}
                    return Response(content, status=status.HTTP_201_CREATED)

            except get_user_model().DoesNotExist:
                content = {'detail': _('User with email address "{email}" does not exist.').format(email=email)}
                return Response(content, status=status.HTTP_404_NOT_FOUND)

            # Since this is AllowAny, don't give away error.
            content = {'detail': _('Password reset not allowed.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerify(APIView, TemplateView):
    authentication_classes = []
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.GET.get('code', '')

        try:
            password_reset_code = PasswordResetCode.objects.get(code=code)

            # Delete password reset code if older than expiry period
            delta = date.today() - password_reset_code.created_at.date()
            if delta.days > PasswordResetCode.objects.get_expiry_period():
                password_reset_code.delete()
                raise PasswordResetCode.DoesNotExist()
            
            if password_reset_code.set_user_is_verified(code):
                password_reset_code.change_user_password()
                password_reset_code.delete()

            content = {'success': _('Email address verified.')}
            # return Response(content, status=status.HTTP_200_OK)
            return HttpResponseRedirect(reverse('password-reset-verified'))
        except PasswordResetCode.DoesNotExist:
            content = {'detail': _('Unable to verify user.')}
            # return Response(content, status=status.HTTP_400_BAD_REQUEST)
            return HttpResponseRedirect(reverse('password-reset-not-verified'))


class PasswordResetVerified(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetVerifiedSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            code = serializer.data['code']
            password = serializer.data['password']

            try:
                password_reset_code = PasswordResetCode.objects.get(code=code)
                password_reset_code.user.set_password(password)
                password_reset_code.user.save()

                # Delete password reset code just used
                password_reset_code.delete()

                content = {'success': _('Password reset.')}
                # return Response(content, status=status.HTTP_200_OK)
                return HttpResponseRedirect(reverse('password-reset-verified'))
            except PasswordResetCode.DoesNotExist:
                content = {'detail': _('Unable to verify user.')}
                # return Response(content, status=status.HTTP_400_BAD_REQUEST)
                return HttpResponseRedirect(reverse('password-reset-not-verified'))

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerifiedFrontEnd(TemplateView):
    template_name = 'EGT/password_verified.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_variable'] = 'my_value'
        return context


class PasswordResetNotVerifiedFrontEnd(TemplateView):
    template_name = 'EGT/password_not_verified.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_variable'] = 'my_value'
        return context


class EmailChange( APIView):
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = EmailChangeSerializer

    def post(self, request, format=None):
         # check user group permission
        checkAdministratorEmployeeGroupMixin(self)
        serializer = self.serializer_class(data=request.data)

        #  filter active user
        if check_user_status(request.user) == False:
            raise PermissionDenied

        if serializer.is_valid():
            user = request.user

            # Delete all unused email change codes
            EmailChangeCode.objects.filter(user=user).delete()

            email_new = serializer.data['email']

            try:
                user_with_email = get_user_model().objects.get(email=email_new)
                if user_with_email.is_verified:
                    content = {'detail': _('Email address already taken.')}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # If the account with this email address is not verified,
                    # give this user a chance to verify and grab this email address
                    raise get_user_model().DoesNotExist

            except get_user_model().DoesNotExist:
                email_change_code = EmailChangeCode.objects.create_email_change_code(user, email_new)

                email_change_code.send_email_change_emails()

                content = {'email': _(f" A verification email have been sent to '{email_new}'.")}
                return Response(content, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class EmailChangeVerify(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.GET.get('code', '')

        try:
            # Check if the code exists.
            email_change_code = EmailChangeCode.objects.get(code=code)
            user = email_change_code.user
            new_email = email_change_code.email

            # Check if the code has expired.
            delta = date.today() - email_change_code.created_at.date()
            if delta.days > EmailChangeCode.objects.get_expiry_period():
                email_change_code.delete()
                raise EmailChangeCode.DoesNotExist()

            # Check if the email address is being used by a verified user.
            try:
                user_with_email = get_user_model().objects.get(email=email_change_code.email)
                if user_with_email.is_verified:
                    # Delete email change code since won't be used
                    email_change_code.delete()

                    content = {'detail': _('Email address already taken.')}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # If the account with this email address is not verified,
                    # delete the account (and signup code) because the email
                    # address will be used for the user who just verified.
                    user_with_email.delete()
            except get_user_model().DoesNotExist:
                pass
            

            # If all is well, change the email address.
            user.email = new_email
            user.save()

            # Delete email change code just used
            email_change_code.delete()
 
            content = {'success': _('Email address changed.')}
            # return Response(content, status=status.HTTP_200_OK)
            return HttpResponseRedirect(reverse('email-change-verified'))
        except EmailChangeCode.DoesNotExist:
            content = {'detail': _('Unable to verify user.')}
            # return Response(content, status=status.HTTP_400_BAD_REQUEST)
            return HttpResponseRedirect(reverse('email-change-not-verified'))


class EmailChangeVerifiedFrontEnd(TemplateView):
    template_name = 'EGT/email_change_verified.html'


class EmailChangeNotVerifiedFrontEnd(TemplateView):
    template_name = 'EGT/email_change_not_verified.html'


class UserMe( APIView):
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, format=None):
         # check user group permission
        checkAdministratorEmployeeGroupMixin(self)
        return Response(self.serializer_class(request.user).data)


class AdministratorList(generics.ListAPIView):
    authentication_classes =(authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAdminUser,)
    queryset = Administrator.objects.all()

    # change the queryset to only query un-deactivated objects (delete)
    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = UserSerializer
    lookup_field ="pk"
    

    def get(self, request, format=None):
         # check user group permission
        checkAdministratorGroupMixin(self)
        return super(AdministratorList, self).get(request, format=None)


class AdministratorDetails(generics.RetrieveAPIView):
    queryset = Administrator.objects.all()
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    lookup_field ="pk"
    

    def get(self, request, *args, **kwargs):
         # check user group permission
        checkAdministratorGroupMixin(self)
        return super().get(request, *args, **kwargs)


class AdministratorUpdate(generics.RetrieveUpdateAPIView):
    queryset = Administrator.objects.all()

    
    serializer_class = UserSerializer
    lookup_field = "pk"
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permissions_classes = (IsAuthenticated,)

    def perform_update(self, serializer):
         # check user group permission
        checkAdministratorGroupMixin(self)

        firstname = serializer.validated_data.get("firstname")
        lastname = serializer.validated_data.get("lastname")
        cv = serializer.validated_data.get('cv')
        email = serializer.validated_data.get("email")
        recovery_email = serializer.validated_data.get("recovery_email")
        password = serializer.validated_data.get("password")
        picture = serializer.validated_data.get("picture")
        date_joined = serializer.validated_data.get("date_joined")
        is_staff = serializer.validated_data.get("staff")
        is_active = serializer.validated_data.get('is_active')
        is_employee = serializer.validated_data.get('is_employee')
        is_administrator = serializer.validated_data.get('is_administrator')
        status = serializer.validated_data.get("status")
        role = serializer.validated_data.get('role')

        return serializer.save()


class AdministratorDelete(generics.UpdateAPIView):
    queryset = Administrator.objects.all()
    # change the queryset to only query un-deactivated objects (delete)
    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = UserSerializer
    lookup_field = "pk"
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication, )
    permission_classes = (permissions.IsAdminUser,)

    def put(self, request, *args, **kwargs):
        # check if the user is active
        if check_user_status(request.user) == False:
            raise PermissionDenied
        
    def patch(self, request, *args, **kwargs):
        # check if the user is active
        if check_user_status(request.user) == False:
            raise PermissionDenied

    def perform_update(self, serializer):
        firstname = serializer.validated_data.get("firstname")
        lastname = serializer.validated_data.get("lastname")
        cv = serializer.validated_data.get('cv')
        email = serializer.validated_data.get("email")
        recovery_email = serializer.validated_data.get("recovery_email")
        password = serializer.validated_data.get("password")
        picture = serializer.validated_data.get("picture")
        date_joined = serializer.validated_data.get("date_joined")
        is_staff = serializer.validated_data.get("staff")
        is_active = serializer.validated_data.get('is_active')
        is_employee = serializer.validated_data.get('is_employee')
        is_administrator = serializer.validated_data.get('is_administrator')
        status = serializer.validated_data.get("status")
        role = serializer.validated_data.get('role')
        
        if is_active is not True:
            is_active = False
            status = 2
        return serializer.save( is_active = is_active, status=status)



"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    ENTERPRISE VIEW SECTION
"""

class EnterpriseCreateView( generics.CreateAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterpriseCreateSerializer
    lookup_field = 'pk'
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
         # check user group permission
        checkAdministratorGroupMixin(self)
        
        PDG = serializer.validated_data.get("PDG")
        name = serializer.validated_data.get("name")
        city = serializer.validated_data.get("city")
        country = serializer.validated_data.get("country")
        location = serializer.validated_data.get("location")
        logo = serializer.validated_data["logo"]
        status = serializer.validated_data.get("status")
        if not check_user_status(self.request.user):
            raise PermissionDenied
        
        if self.request.user.role == MyUser.Role.EMPLOYEE:
            raise PermissionDenied

        return serializer.save(name = name.upper(), logo =logo, code= set_enterprise_code(name),  PDG=self.request.user)


class EnterpriseList( generics.ListAPIView):
    """
    List all the enterprise of an administrator
    """
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Enterprise.objects.all() 
    serializer_class = EnterpriseSerializer
    lookup_field ="pk"
    

    def get_queryset(self):
        """Filter the queryset to only include the objects that are associated with the active user."""
         # check user group permission
        checkAdministratorEmployeeGroupMixin(self)
        queryset = super().get_queryset()
        user = self.request.user
        if user.role== "EMPLOYEE":
            user = Employee.objects.get(id = user.id) if user.role == "EMPLOYEE" else user
            queryset = queryset.filter(
                Q(employees__in=[user,])
            ).prefetch_related('employees')
            
            return queryset
        else:
            queryset = queryset.filter(
                Q(PDG=self.request.user) | Q(admins__in=[user,])
            ).prefetch_related('admins')
            
        for enterprise in queryset:
            if check_user_enterprise_status(user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None] :
                queryset= queryset.exclude(name=enterprise.name)

        return queryset

    

class EnterpriseDetails( generics.RetrieveAPIView):
    queryset = Enterprise.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = EnterpriseSerializer
    lookup_field ="pk"
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        # check user group permissions
        checkAdministratorGroupMixin(self)
        obj = self.get_object()
        if check_user_enterprise_status(request.user, obj) not in [Status.ACTIVE]:
            raise PermissionDenied
        return super(EnterpriseDetails, self).get(request, format=None)


class EnterpriseUpdate(generics.RetrieveUpdateAPIView):
    queryset = Enterprise.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = EnterpriseUpdateSerializer
    lookup_field = "pk"
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


    def perform_update(self, serializer):
        # check user group permission
        checkAdministratorGroupMixin(self)

        name = serializer.validated_data.get("name")
        city = serializer.validated_data.get("city")
        country = serializer.validated_data.get("country")
        city = serializer.validated_data.get("city")
        location = serializer.validated_data.get("location")
        logo = serializer.validated_data.get("logo")
        employees = serializer.validated_data.get('employees')
    
        if not user_belong_to_enterprise(self.request.user, self.get_object()):
            raise PermissionDenied
        
        if check_user_enterprise_status(self.request.user, self.get_object()) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied
        name= name.upper()
        return serializer.save(name=name)


class EnterpriseDelete( generics.UpdateAPIView):
    queryset = Enterprise.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = EnterpriseSerializer
    lookup_field = "pk"
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

   
    def perform_update(self, serializer): 
        # check user group permission
        checkAdministratorGroupMixin(self)

        PGG = serializer.validated_data.get("PGG")
        name = serializer.validated_data.get("name")
        city = serializer.validated_data.get("city")
        country = serializer.validated_data.get("country")
        location = serializer.validated_data.get("location")
        code = serializer.validated_data.get("code")
        logo = serializer.validated_data.get("logo")
        dateOfRegistration = serializer.validated_data.get("dateOfRegistration")
        status = serializer.validated_data.get("status")
        admins = serializer.validated_data.get('admins')

        if not user_belong_to_enterprise(self.request.user, self.get_object()):
            raise PermissionDenied
        
        if check_user_enterprise_status(self.request.user, self.get_object()) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied
        
        return serializer.save(status=2)


class ChangePdgOrAdmin( APIView):
    """ Change the PDG or the Administration of the enterprise """
    serializer_class = ChangePdgOrAdministratorSerializer
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # check user group permission
        checkAdministratorGroupMixin(self)
        serializer = self.serializer_class(data = request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pdg = request.user
        new_administrator_email = serializer.data['new_administrator_email']
        enterprise_name = str(serializer.data['enterprise_name']).upper()

        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content ={'detail': _(f'Enterprise with name "{enterprise_name}" does not exists.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        if check_user_enterprise_status(pdg, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied

        try:
            new_administrator = get_user_model().objects.get(email=new_administrator_email)
        except get_user_model().DoesNotExist:
            content ={'detail': _(f'User with email {new_administrator_email} does not exists.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
            
        if check_user_status(new_administrator) == False and user_belong_to_enterprise(new_administrator, enterprise) == True:
            raise PermissionDenied

        deactivate_enterprise_pdg_admin_and_add_admin(pdg, enterprise, new_administrator)

        content = {'detail': _(f'Administrator {pdg.email} was changed successfully and the new administrator is {new_administrator_email}.')}
        return Response(content, status=status.HTTP_200_OK)


class DeactivateEmployee( APIView):
    """ Deactivate employee form and enterprise """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [IsAuthenticated, ]
    serializer_class = DeactivateEmployeeSerializer

    def post(self, request, format=None):
        # check user group permission
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)

        # check if the serialized data is valid
        if not serializer.is_valid():
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        
        employee_email = serializer.data['employee_email']
        enterprise_name = serializer.data['enterprise_name'].upper()

        try:
            # check if the user exists and if he's an employee
            user = Employee.objects.get(email = employee_email, role=MyUser.Role.EMPLOYEE)
        except get_user_model().DoesNotExist:
            content ={'detail': _(f'User "{employee_email}" is not an employee or does not exist.')}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        
        try:
            # check if the user exists and if he's an employee
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except get_user_model().DoesNotExist:
            content ={'detail': _(f'Enterprise "{enterprise_name}" does not exist.')}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)


        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if user_belong_to_enterprise(user, enterprise) == False:
            content = {'detail': _(f'User "{employee_email}" does not belong to "{enterprise_name}".')}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        
        #  check if the user is an active employee
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response({"detail": _(f"User {user.email} is not  an active employee of {enterprise_name.upper()}")})
        
        deactivate_user(user, enterprise)

        return Response({'detail': _('employee deactivated')}, status=status.HTTP_200_OK)


class EnterpriseEmployeeList( APIView):
    """
    Enterprise employee list. 
    
    This class start by receiving the posted enterprise name, then, process 
    it and return the list of employees whom belong to the enterprise
    """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [IsAuthenticated, ]

    serializer_class = EnterpriseEmployeeListSerializer

    def post(self, request, format=None):
        # check user group permission
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        enterprise_name = serializer.data['enterprise_name'].upper()
        
        try:
            # check if the enterprise exists
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content={'detail':_(f"Enterprise '{enterprise_name}' does not exist.")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        # check if the administrator or employee admin belong to the enterprise
        if user_belong_to_enterprise(request.user, enterprise) == False:
            raise PermissionDenied
        
        # check if the user if an active administrator
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        items = []
        
        # filter all employees who have a relationship with the enterprise
        employees = enterprise.employees.all()
        for employee in employees:
            employee_profile = _get_user_profile(employee)
            user_codes = json.loads(employee_profile.user_enterprise_code)
            code: str

            # set user code
            if enterprise_name in user_codes:
                code = user_codes[enterprise_name]
            else:
                code = None

            if employee_profile.categories != None:
                user_categories = json.loads(employee_profile.categories)
                if enterprise_name in user_categories:
                    category = user_categories[enterprise_name]
            else:
                category = None
            if employee_profile.user_enterprise_salary != None:
                salaries = json.loads(employee_profile.user_enterprise_salary)
                salary = salaries[enterprise_name]
            else:
                salary = None

            if enterprise_name in user_codes:
                new = {
                    'code': code,
                    'email': employee_profile.user.email,
                    'full_name': employee_profile.user.get_full_name(),
                    'date_joined': employee_profile.user.date_joined,
                    'category': category,
                    "salary": salary,
                    'status': check_user_enterprise_status(employee_profile.user, enterprise),
                    # # "url": f"{domain_name}/EGT/user/{employee_profile.user.id}/detail/"
                    "url": employee_profile.user.get_absolute_url()
                }
                items.append(new)

        content = {'employees': items}
        serializer_data = self.serializer_class(items, many=True)

        return Response(items  , status=status.HTTP_200_OK)

       
class EnterpriseCategoryList( APIView):
    """ 
    This view list all the categories of employee under an enterprise.
    """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [IsAuthenticated, ]

    serializer_class = EnterpriseEmployeeListSerializer
    queryset = Category.objects.all()


    
    def post(self, request, format=None):
        # check user group permission
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        enterprise_name = serializer.data['enterprise_name'].upper()

        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content ={'detail': _(f"Enterprise '{enterprise_name}' does not exist.")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if user_belong_to_enterprise(request.user, enterprise) == False:
            raise PermissionDenied
        
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        categories = Category.objects.filter(enterprise=enterprise)
        list = []

        for category in categories:
            new = model_to_dict(category)
            new["url"] = _(f"127.0.0.1:8000/EGT/enterprise/category/{category.pk}/detail/")
            list.append(new)

        

        content = {
            "detail": _(f"List of categories for {enterprise_name}."),
            "status":_("SUCCESS"),
            "categories": list,
        }
        return Response(content, status=status.HTTP_200_OK)
    

class EnterpriseEmployeeCategory( APIView):
    """ Set user category """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [IsAuthenticated, ]

    serializer_class = EmployeeCategorySerializer

    def post(self, request, format=None):
        # check user group permissions
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        employee_email = serializer.data['employee_email'].lower()
        category_name = serializer.data['category'].upper()
        enterprise_name = serializer.data['enterprise_name'].upper()

        # check enterprise existence
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={'detail': _(f"Enterprise {enterprise_name} does not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        # authenticate the user
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        # check category existence
        try:
            category = Category.objects.get(Q(name=category_name) & Q(enterprise=enterprise))
            # category = categories.first()
        except Exception as e:
            content = {'detail': _(f"An error occur: '{e}'")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        # check employee status enterprise status
        try:
            employee = get_user_model().objects.get(email=employee_email)

            if employee.role != MyUser.Role.EMPLOYEE or check_user_enterprise_status(employee, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
                content={'detail': _(f"User '{employee_email}' is not an employee of '{enterprise.name}'.")}
                return Response(content, status.HTTP_400_BAD_REQUEST)

        except get_user_model().DoesNotExist:
            content={'detail': _('User does not exists or is not active')}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        # check if the category belong to the enterprise
        if category.enterprise != enterprise:
            content={'detail': _(f"Invalid category '{category.name}'")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # set employee category
        result = set_employee_category(employee, enterprise, category_name)
        if result == True:
            # set employee total salary
            
            employee_profile = _get_user_profile(employee)
            if employee_profile.categories != None:
                total_salary: float = 0.0
                data = json.loads(employee_profile.categories)
                for item in data:
                    employee_category = Category.objects.get(Q(name=data[item]) & Q(enterprise=Enterprise.objects.get(name=item)))
                    total_salary += float(employee_category.salary)

                employee_profile.total_salary = total_salary
                employee_profile.save()
            content ={'detail': _(f"Employee '{employee.get_full_name()}' category was successfully set to '{category.name}'.")}
            return Response(content, status=status.HTTP_201_CREATED)
        
        else:
            return Response({'detail': result}, status=status.HTTP_400_BAD_REQUEST)
            

class EnterpriseSetEmployeeAdmin( APIView):
    """
    Set Enterprise sub-administration.
    This operation consist of setting an active employee to be granted some permissions
    like:
    - creating goals, activities, 
    - Rating goal/activities result, 
    - And view goal progression


    employees_list structure
            employees_list = {
                "employees": [<list of employee emails int string>]
            }
    """
    queryset = Enterprise.objects.all()
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication, ]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnterpriseSetEmployeeAdminSerializer

    def post(self, request, format = None):
        # check if the user if active
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data= request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        
        """
            employees_list structure
            employees_list = {
                "employees": [<list of employee emails>]
            }

        """
        employees_list = serializer.data['employees_list']
        enterprise_name = serializer.data['enterprise_name'].upper()

        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            return Response({"detail":_(f"Enterprise {enterprise_name} does not exist")}, status.HTTP_400_BAD_REQUEST)
    

        # check if the user is an active enterprise administrator
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        data = employees_list['employees']
        employee_admins = []
        for e in data:
            try:
                user = Employee.objects.get(email= e.lower())
                if check_user_enterprise_status(user, enterprise) in [Status.ACTIVE]:
                    enterprise.employee_admins.add(user)
                    enterprise.save()
                    group = Group.objects.get(name="Admins")
                    user.groups.add(group)
                    # notify the user

                    employee_admins.append(e)
            except Exception as e:
                print(f"error:{e} and {status.HTTP_400_BAD_REQUEST}")
                pass
            
        content = {"Granted to admin permissions": employee_admins}
        return Response(content, status.HTTP_400_BAD_REQUEST)


class EnterpriseRemoveEmployeeAdmin( APIView):
    """
    Remove Enterprise sub-administration.
    This operation consist of downgrade a list of active employees from sud-administration to 
    normal employee authorization.
    """
    queryset = Enterprise.objects.all()
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication, ]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnterpriseSetEmployeeAdminSerializer

    def post(self, request, format = None):
        # check if the user if active
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data= request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        
        """
            employees_list structure
            employees_list = {
                "employees": [<list of employee emails>]
            }

        """
        employees_list = serializer.data['employees_list']
        enterprise_name = serializer.data['enterprise_name'].upper()

        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            return Response({"detail":_(f"Enterprise {enterprise_name} does not exist")}, status.HTTP_400_BAD_REQUEST)
    

        # check if the user is an active enterprise administrator
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        data = employees_list['employees']
        employee_admins = []
        for e in data:
            try:
                user = Employee.objects.get(email= e.lower())
                if user in enterprise.employee_admins.all():
                    enterprise.employee_admins.remove(user)
                    enterprise.save()

                    is_user_admin_in_other_enterprise = False
                    if Enterprise.objects.filter(Q(employees=user) & Q(employee_admins=user)).exists():
                        is_user_admin_in_other_enterprise = True
                    
                    if not is_user_admin_in_other_enterprise:
                        group = Group.objects.get(name="Admins")
                        user.groups.remove(group)

                    employee_admins.append(e)
            except Exception as e:
                return Response({"error":_(f"{e}")}, status.HTTP_400_BAD_REQUEST)
                pass
            
        content = {"ungraded to employee authorizations": employee_admins}
        return Response(content, status.HTTP_400_BAD_REQUEST)


class ActivateEmployee( APIView):
    """ Deactivate employee form and enterprise """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [IsAuthenticated, ]
    serializer_class = DeactivateEmployeeSerializer

    def post(self, request, format=None):
        # check user group permission
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)

        # check if the serialized data is valid
        if not serializer.is_valid():
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        
        employee_email = serializer.data['employee_email']
        enterprise_name = serializer.data['enterprise_name'].upper()

        try:
            # check if the user exists and if he's an employee
            user = Employee.objects.get(email = employee_email, role=MyUser.Role.EMPLOYEE)
        except get_user_model().DoesNotExist:
            content ={'detail': _(f'User "{employee_email}" is not an employee or does not exist.')}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        
        try:
            # check if the user exists and if he's an employee
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except get_user_model().DoesNotExist:
            content ={'detail': _(f'Enterprise "{enterprise_name}" does not exist.')}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        
     
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        #  check if the user is a  non-active employee
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
           raise PermissionDenied
        

        if not user_belong_to_enterprise(user, enterprise):
            content = {'detail': _(f'User "{employee_email}" does not belong to "{enterprise_name}".')}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        #  check if the user is a  non-active employee
        if check_user_enterprise_status(user, enterprise) in [Status.ACTIVE]:
            return Response({"detail": _(f"User {user.email} is an active employee of {enterprise_name.upper()}")})
        
        
        activate_user(user, enterprise)

        return Response({'detail': _('employee activated')}, status=status.HTTP_200_OK)


class EmployeeProfileChangeSalary( APIView):
    """ Change employee profile enterprise salary"""
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmployeeProfileChangeSalarySerializer

    def post(self, request, format=None):
        #  check user permission group
        checkAdministratorGroupMixin(self)

        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        enterprise_name = serializer.data["enterprise_name"].upper()
        user_id = serializer.data["user_id"]
        salary = float(serializer.data["salary"])

        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({"detail": _("Invalid user")})
        
        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            return Response({"detail": _("Invalid enterprise.")})

        #  authenticate the administrator
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        # authenticate the user
        if not user_belong_to_enterprise(user, enterprise):
            return Response({"detail": _("Invalid user")})
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response({"detail": _("Invalid user")})
        
        # get user employee profile
        employee_profile = _get_user_profile(user)

        if employee_profile.user_enterprise_salary is None:
            data = return_jsonfield_value(enterprise_name, salary)
            employee_profile.user_enterprise_salary = data
            employee_profile.save()
        else:
            data = json.loads(employee_profile.user_enterprise_salary)
            data[enterprise_name] = salary
            employee_profile.user_enterprise_salary = json.dumps(data)
            employee_profile.save()

        return Response({"detail": _("changed successfully.")}, status.HTTP_200_OK)

            



    
"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    CATEGORY VIEW SECTION
"""

class CategoryCreateView(generics.CreateAPIView):
    """ 
    This view create enterprise categories .
    And ensure that an enterprise can not have two categories with the same name
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'pk'
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


    def perform_create(self, serializer):
        # check user permission group
        checkAdministratorGroupMixin(self)

        salary = serializer.validated_data.get("salary")
        name = serializer.validated_data.get("name")
        enterprise = serializer.validated_data.get('enterprise')
        state = serializer.validated_data.get('status')
        payment_period = serializer.validated_data.get('payment_period')


        if user_belong_to_enterprise(self.request.user, enterprise) == False:
            raise PermissionDenied
        
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        try:
            category = Category.objects.get(name=name.upper(), enterprise=enterprise)
            return Response({'detail': _(f'This category "{name.upper()}" already exists.')}, status= status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            serializer.save(name=name.upper(), status=state)
            return serializer.save(name=name.upper(), status=state)
    

class CategoryList(generics.ListAPIView):
    """ List all the categories of all enterprises. """
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field ="pk"
    
    def get(self, request, *args, **kwargs):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)


        return super().get(request, *args, **kwargs)
        

class CategoryDetails( generics.RetrieveAPIView):
    """ Retrieve the details of a specific category."""
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field ="pk"



    def get(self, request, *args, **kwargs):
        # check user group permissions
        checkAdministratorEmployeeGroupMixin(self)

        obj = self.get_object()
        enterprise = obj.enterprise

        if not user_belong_to_enterprise(self.request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        return super().get(request,  *args, **kwargs)


class CategoryUpdate( generics.RetrieveUpdateAPIView):
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Category.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)

    serializer_class = CategorySerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        # check user permission group
        checkAdministratorGroupMixin(self)

        obj = self.get_object()
        enterprise = obj.enterprise

        if not user_belong_to_enterprise(self.request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        name = serializer.validated_data.get("name")
        salary = serializer.validated_data.get("salary")
        enterprise = serializer.validated_data.get('enterprise')
        status = serializer.validated_data.get('status')

        return serializer.save(name=name.upper())


class CategoryDelete(generics.UpdateAPIView):
    queryset = Category.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = CategorySerializer
    lookup_field = "pk"

    

    def perform_update(self, serializer):
        # check user permission group
        checkAdministratorGroupMixin(self)

        obj = self.get_object()
        enterprise = obj.enterprise

        if not user_belong_to_enterprise(self.request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        name = serializer.validated_data.get("name")
        salary = serializer.validated_data.get("salary")
        enterprise = serializer.validated_data.get('enterprise')
        status = serializer.validated_data.get('status')

        return serializer.save(status=Status.SUSPENDED)


"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    EMPLOYEE VIEW SECTION
""" 

class EmployeeList( generics.ListAPIView):
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAdminUser, IsAuthenticated,)
    serializer_class= UserDetailSerializer
    queryset = Employee.objects.all()

    def get(self, request, *args, **kwargs):
        # check user group permission
        checkAdministratorGroupMixin(self)
        return super().get(request, *args, **kwargs)

    


class EmployeeDetails( generics.RetrieveAPIView):
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    queryset = Employee.objects.all()
    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = UserSerializer
    lookup_field ="pk"

    def get(self, request, *args, **kwargs):
        # check user group permission
        checkAdministratorEmployeeGroupMixin(self)
        return super().get(request, *args, **kwargs)


class EmployeeUpdate( generics.RetrieveUpdateAPIView):
    authentication_classes = ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    queryset = get_user_model().objects.all()
    serializer_class = UserUpdate2Serializer
    lookup_field = "pk"

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)

    def perform_update(self, serializer):
        # check if the user is active
        checkAdministratorEmployeeGroupMixin(self)

        obj = self.get_object()

        enterprise_name = serializer.validated_data["enterprise_name"].upper()

        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            return Response(
                {
                    "detail": _("Invalid enterprise name."),
                    "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        #  authenticate the user
        user = self.request.user
        if user != obj or user != enterprise.PDG or user not in enterprise.admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        firstname = serializer.validated_data.get("firstname")
        lastname = serializer.validated_data.get("lastname")
        cv = serializer.validated_data.get('cv')
        recovery_email = serializer.validated_data.get("recovery_email")
        picture = serializer.validated_data.get("picture")

        return serializer.save()


class EmployeeDelete( generics.UpdateAPIView):
    
    queryset = Employee.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(status = 1)
    
    serializer_class = UserSerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        # check permission group
        checkAdministratorGroupMixin(self)

        status = serializer.validated_data('status')

        return serializer.save(status = Status.SUSPENDED)






"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    EMPLOYEE PROFILE VIEW SECTION
"""
class EmployeeProfileRetrieveUpdate(generics.RetrieveAPIView):
    """ Retrieve employee profile only the  """
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = EmployeeProfileSerializer
    queryset = EmployeeProfile.objects.all()
    lookup_field = "pk"

    def get(self, request, *args, **kwargs):
        # check user group permission
        checkAdministratorEmployeeGroupMixin(self)

        if self.request.user != self.get_object().user:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)

   

class EmployeeProfileCreate(generics.CreateAPIView):
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
    lookup_field = "pk"
    
    def perform_create(self, serializer):
        user = serializer.validated_data.get('user')
        category = serializer.validated_data.get('category')
        salary = serializer.validated_data.get('salary')
        user_enterprise_code = serializer.validated_data.get('user_enterprise_code')
        is_admin = serializer.validated_data.get('is_admin')
    
        if category is not None:
            category_obj = Category.objects.get(name=category)
            salary = category_obj.salary
            code = category_obj.enterprise

            date = datetime.datetime.now()
            x = str(date)
            y = x.split('-')
            year = y[0]

            employee_number = str(len(Employee.objects.all()) + 1)

            enterprise_code = code + year + employee_number
            user_enterprise_code = enterprise_code.upper()
        
        serializer.save(salary = salary, user_enterprise_code = user_enterprise_code)


class EmployeeProfileRetrieve(generics.UpdateAPIView):
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
    lookup_field = "pk"


    def perform_update(self, serializer):
        # user authentication
        checkAdministratorGroupMixin(self)
        
        user = serializer.validated_data.get('user')
        category = serializer.validated_data.get('category')
        salary = serializer.validated_data.get('salary')
        user_enterprise_code = serializer.validated_data.get('user_enterprise_code')
        is_admin = serializer.validated_data.get('is_admin')

        if category is not None:
            category_obj = Category.objects.get(name=category)
            salary = category_obj.salary
            code = category_obj.enterprise

            date = datetime.datetime.now()
            x = str(date)
            y = x.split('-')
            year = y[0]

            employee_number = str(len(Employee.objects.all()))

            enterprise_code = str(code) + year+ 'E' + employee_number
            user_enterprise_code = enterprise_code.upper()
        
        serializer.save(salary = salary, user_enterprise_code = user_enterprise_code)


class EmployeeProfileList(generics.ListAPIView):
    """ Get all employee profile list"""
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAdminUser, permissions.IsAdminUser, ]
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
    lookup_field = "pk"


"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    Administrator PROFILE VIEW SECTION
"""
class AdministratorProfileCreate(generics.CreateAPIView):
    queryset = AdministratorProfile.objects.all()
    serializer_class = AdministratorProfileSerializer
    lookup_field = "pk"

    def perform_create(self, serializer):
        user = serializer.validated_data.get('user')
        records = serializer.validated_data.get('records')
        enterprise_status = serializer.validated_data.get('enterprise_status')
        return serializer.save()
 

# class AdministratorProfileUpdate( generics.UpdateAPIView):
#     authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
#     permission_classes = [permissions.IsAdminUser]
#     queryset = AdministratorProfile.objects.all()
#     serializer_class = AdministratorProfileSerializer
#     lookup_field = "pk"


#     def perform_update(self, serializer):
#         # check user authentication permissions
#         checkAdministratorEmployeeGroupMixin(self)

#         user = serializer.validated_data.get('user')
#         records = serializer.validated_data.get('records')
#         enterprise_status = serializer.validated_data.get('enterprise_status')

#         return serializer.save()
    

class AdministratorProfileRetrieve(generics.RetrieveAPIView):
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = AdministratorProfile.objects.all()
    serializer_class = AdministratorProfileSerializer
    lookup_field="user"

    def get(self, request, *args, **kwargs):

        obj = self.get_object()

        if obj.user != request.user:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)
    
    

class AdministratorProfileList(generics.ListAPIView):
    authentication_classes =  ( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAdminUser ,permissions.IsAuthenticated,)
    serializer_class = AdministratorProfileSerializer
    queryset = AdministratorProfile.objects.all()

    lookup_field = "pk"    

    def get(self, request, *args, **kwargs):
        # check user group permission
        checkAdministratorGroupMixin(self)
        return super().get(request, *args, **kwargs)


class UsersList(generics.ListAPIView):
    authentication_classes = [ authentication.SessionAuthentication, authentication.TokenAuthentication,]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset= User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'pk'


    def get(self, request, *args, **kwargs):
        # check user group permission
        checkAdministratorEmployeeGroupMixin(self)


        return super().get(request, *args, **kwargs)



class UserDetail(generics.RetrieveAPIView):
    authentication_classes = [ authentication.SessionAuthentication, authentication.TokenAuthentication,]
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset= User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        # check user group permission
        checkAdministratorEmployeeGroupMixin(self)

        obj = self.get_object()
        
        if request.user == obj:
            return super().get(request, *args, **kwargs)

        if request.user.role == "EMPLOYEE" and request.user != obj:
            raise PermissionDenied
        
        if request.user.role == "GOAL" and request.user != obj:
            raise PermissionDenied
        
        # else:
        #     if obj.role != "EMPLOYEE" :
        #         raise PermissionDenied
        #     user_profile = _get_user_profile(obj)
        #     if user_profile.user_enterprise_code == None:
        #         raise PermissionDenied
        #     data = json.loads(user_profile.user_enterprise_code)
        #     for i in data:
        #         print(i)
        #         try:
        #             enterprise = Enterprise.objects.get(name = i)
        #             if check_user_enterprise_status(obj, enterprise) in [Status.ACTIVE]:
        #                 return super().get(request, *args, **kwargs)
        #         except:
        #             pass

        #     raise PermissionDenied
        return super().get(request, *args, **kwargs)
                    

        
        