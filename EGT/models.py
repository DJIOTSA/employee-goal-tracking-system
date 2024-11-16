from django.db import models
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
import uuid
from django.contrib.auth.models import Group
from django.db.models import Q
import json
from django.utils import timezone
import binascii
import os
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail.message import EmailMultiAlternatives
from django.urls import reverse
from employee_goal_tracker.celery import app 

import logging, datetime
import json
from EGT.exceptions import (
    AdministratorProfileDoesNotExistError,
    AdministratorProfileDoesNotExistError,
    EmployeeProfileDoesNotExistError,
    InvalidStatusError,
    InvalidUserRoleError,
    UserDoesNotExist,
)

from django.core.exceptions import ValidationError

import logging, datetime, json

from EGT.exceptions import InvalidStatusError

# Create a logger object
logger = logging.getLogger(__name__)
# Set the logger's level to DEBUG or another appropriate level
logger.setLevel(logging.DEBUG)
# Create a formatter to specify the format of log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Add the formatter to the logger
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)



"""" For path of model that are editable """
EXPIRY_PERIOD = 3    # days

def _generate_code():
    return binascii.hexlify(os.urandom(20)).decode('utf-8')


class UserManager(BaseUserManager):
    """ User Manager for creation of user."""
    def _create_user(self, email, password, is_staff, is_superuser,
                     is_verified, **extra_fields):
        """
        Creates and saves a User with a given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, is_verified=is_verified,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        return self._create_user(email, password, True, True, True,
                                 **extra_fields)


class LowerCaseEmailField(models.EmailField):
    """
    OVERRIDE EMAIL FIELD TO SET IT TO LOWERCASE BEFORE SAVING.
    """

    def to_python(self, value):
        """ 
        convert email to lowercase 
        """
        value = super(LowerCaseEmailField, self).to_python(value)
        # check if value is a string (is not None)
        if isinstance(value, str):
            return value.lower()
        return value


class Status(models.IntegerChoices):
    """
    This class is use as flag allowing to define the status of model
    """
    ACTIVE = 1, _('Active')
    DEACTIVATED = 2, _('Deactivated')
    SUSPENDED = 3, _('Suspend')



class MyUser(AbstractBaseUser, PermissionsMixin):
    """
    User model with admin-compliant permissions.
    email and password are required. Other fields are optional.
    """ 

    class Role(models.TextChoices):
        ADMINISTRATOR = "ADMINISTRATOR", 'Administrator'
        EMPLOYEE = "EMPLOYEE", 'Employee'

    role = models.CharField(
        _('user role'), max_length=15, choices=Role.choices)

    picture = models.ImageField(blank=True,null=True, upload_to='user_pict',)
    cv = models.FileField(blank=True,null=True, upload_to='user_cv')
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = LowerCaseEmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )
    recovery_email = LowerCaseEmailField(
        _("Recovery Email Address"), blank=True, null=True)

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_verified = models.BooleanField(
        _('verified'), default=False,
        help_text=_('Designates whether this user has completed the email '
                    'verification process to allow login.'))
    is_administrator = models.BooleanField(
        _("user is administrator"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as an administrator. "
        ),
        editable=False
    )
    is_employee = models.BooleanField(
        _("user is employee"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as an employee. "
        ),
        editable=False
    )

    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    records = models.JSONField(null=True, blank=True)

    objects = UserManager()

    

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role',]

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        # fields = ['user_status']

    def __str__(self):
        """ user description """
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    # def get_absolute_url(self):
    #     "get absolute url "
    #     return reverse("users:detail", kwargs={"email": self.email})
    
    def get_absolute_url(self):
        return reverse('myuser-detail', args=[str(self.pk)])

    def save(self, *args, **kwargs):
        if not self.role or self.role == None:
            self.role = MyUser.Role.ADMINISTRATOR
        return super().save(*args, **kwargs)


class SignupCodeManager(models.Manager):
    def create_signup_code(self, user, ipaddr):
        code = _generate_code()
        signup_code = self.create(user=user, code=code, ipaddr=ipaddr)

        return signup_code

    def set_user_is_verified(self, code):
        try:
            signup_code = SignupCode.objects.get(code=code)
            signup_code.user.is_verified = True
            signup_code.user.save()
            return True
        except SignupCode.DoesNotExist:
            pass

        return False


class SignupCodeEmployeeManager(models.Manager):
    def create_signup_code(self, user, ipaddr):
        code = _generate_code()
        signup_code = self.create(user=user, code=code, ipaddr=ipaddr)

        return signup_code

    def set_user_is_verified(self, code):
        try:
            signup_code = SignupCodeEmployee.objects.get(code=code)
            signup_code.user.is_verified = True
            signup_code.user.save()
            return True
        except SignupCodeEmployee.DoesNotExist:
            pass

        return False
    
    def check_add_employee(self, code):
        try:
            signup_code = SignupCodeEmployee.objects.get(code=code)

            return True
        except SignupCodeEmployee.DoesNotExist:
            pass

        return False


class PasswordResetCodeManager(models.Manager):
    def create_password_reset_code(self, user, new_password):
        code = _generate_code()
        password_reset_code = self.create(user=user, code=code, new_password=new_password)

        return password_reset_code

    def get_expiry_period(self):
        return EXPIRY_PERIOD


class EmailChangeCodeManager(models.Manager):
    def create_email_change_code(self, user, email):
        code = _generate_code()
        email_change_code = self.create(user=user, code=code, email=email)

        return email_change_code

    def get_expiry_period(self):
        return EXPIRY_PERIOD


class AbstractBaseCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(_('code'), max_length=40, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    enterprise_name = models.CharField(_('enterprise_name'), max_length=255)
    class Meta:
        abstract = True

    def send_email(self, prefix):
        ctxt = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'code': self.code,
            'role': self.user.role,
        }
        send_multi_format_email.delay(prefix, ctxt, target_email=self.user.email)

    def __str__(self):
        return self.code


class AbstractBaseCodeEmployee(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(_('code'), max_length=40, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    enterprise_name = models.CharField(_('enterprise_name'), max_length=255)
    employee_password = models.CharField(_('employee password'), max_length=255)
    added_by  = LowerCaseEmailField(_("added by: email address"), null=True)
    class Meta:
        abstract = True

    def send_email(self, prefix):
        ctxt = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'code': self.code,
            'role': self.user.role,
            'enterprise_name': self.enterprise_name,
            'employee_password': self.employee_password
        }
        send_multi_format_email.delay(prefix, ctxt, target_email=self.user.email)

    def __str__(self):
        return self.code


class SignupCode(AbstractBaseCode):
    ipaddr = models.GenericIPAddressField(_('ip address'))
    objects = SignupCodeManager()

    def send_signup_email(self):
        prefix = 'signup_email'
        self.send_email(prefix)

    def send_signup_verify(self, prefix):
        self.send_email(prefix)


class SignupCodeEmployee(AbstractBaseCodeEmployee):
    ipaddr = models.GenericIPAddressField(_('ip address'))

    objects = SignupCodeEmployeeManager()

    def send_signup_email(self):
        prefix = 'signup_email2'
        self.send_email(prefix)
    
    def send_add_employee_email(self):
        prefix = 'add_employee_email'
        self.send_email(prefix)

    def send_signup_verify(self, prefix):
        self.send_email(prefix)

    def add_employee(self):
        user = self.user
        company = Enterprise.objects.get(name= self.enterprise_name.upper())
        password = self.employee_password
        employer_email = self.added_by
        add_new_employee(user, company, password, employer_email)


class PasswordResetCode(AbstractBaseCode):
    objects = PasswordResetCodeManager()
    new_password = models.CharField(max_length=255)

    def change_user_password(self):
        user = self.user
        password = self.new_password
        user.set_password(password)
        user.save()

    def send_password_reset_email(self):
        prefix = 'password_reset_email'
        self.send_email(prefix)

    def set_user_is_verified(self, code):
        try:
            password_reset_code = PasswordResetCode.objects.get(code=code)
            return True
        except SignupCode.DoesNotExist:
            pass

        return False


class EmailChangeCode(AbstractBaseCode):
    email = models.EmailField(_('email address'), max_length=255)

    objects = EmailChangeCodeManager()

    def send_email_change_emails(self):
        prefix = 'email_change_notify_previous_email'
        self.send_email(prefix)

        prefix = 'email_change_confirm_new_email'
        ctxt = {
            'email': self.email,
            'code': self.code,
            'first_name': self.user.first_name
        }

        send_multi_format_email.delay(prefix, ctxt, target_email=self.email)


class AdministratorManager(BaseUserManager):
    """Filter administrator users """

    def _create_user(self, email, password, is_staff, is_superuser,
                     is_verified, **extra_fields):
        """
        Creates and saves a User with a given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, is_verified=is_verified,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def get_queryset(self, *args, **kwargs):
        list = super().get_queryset(*args, **kwargs)
        return list.filter(role=MyUser.Role.ADMINISTRATOR)


class EmployeeManager(BaseUserManager):
    """Filter employee user"""

    def _create_user(self, email, password, is_staff, is_superuser,
                     is_verified, **extra_fields):
        """
        Creates and saves a User with a given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, is_verified=is_verified,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)

        user.save(using=self._db)
        return user

    def get_queryset(self, *args, **kwargs):
        list = super().get_queryset(*args, **kwargs)
        return list.filter(role=MyUser.Role.EMPLOYEE)


class Administrator(MyUser):
    """
    Administrator user proxy model.
    """
    class Meta:
        proxy = True

    objects = AdministratorManager()

    def save(self, *args, **kwargs):
        self.role == MyUser.Role.ADMINISTRATOR
        self.is_employee = False
        self.is_administrator = True
        return super().save(*args, **kwargs)


class Employee(MyUser):
    """
    Employee user proxy model.
    """
    class Meta:
        proxy = True

    objects = EmployeeManager()

    def save(self, *args, **kwargs):
        self.role = MyUser.Role.EMPLOYEE
        self.is_employee = True
        self.is_administrator = False
        return super().save(*args, **kwargs)


User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=MyUser)
def create_admin_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create the administrator profile when ever an administrator is created.
    And add him into the Administrator group.
    """
    if created and instance.role == "ADMINISTRATOR":
        if not Group.objects.filter(name='Administrators').exists():
            create_group('Administrators')
            create_group('Employees')
            create_group('Admins')

        administrators_group = Group.objects.get(name='Administrators')
        instance.groups.add(administrators_group)
        instance.save()
        AdministratorProfile.objects.create(user=instance)


class Enterprise(models.Model):
    PDG = models.ForeignKey(
        Administrator, on_delete=models.CASCADE, to_field='email')
    admins = models.ManyToManyField(
        'Administrator',
        verbose_name=_("admins"),
        blank=True,
        help_text=_(
            "The admins of the enterprise. this user will get administrator permissions over the enterprise"
            "Only one admin can be active at time, and can exist if and only if the PDG, is suspended to by the enterprise"
        ),
        related_name="admin_set",
        related_query_name="admin",
    )
    employees = models.ManyToManyField(
        Employee,
        verbose_name=_("employees"),
        blank=True,
        help_text=_("Enterprise employees "),
        related_name="employee_set",
        related_query_name="employee",
    )
    employee_admins = models.ManyToManyField(
        Employee,
        verbose_name=_("employee_admins"),
        blank=True,
        help_text=_("Enterprise sub-administrators "),
        related_name="employee_admins_set",
        related_query_name="employee_admins",
    )
    name = models.CharField(max_length=100, default="some text", unique=True)
    country = models.CharField(max_length=100, default="some text")
    city = models.CharField(max_length=100, default="some text")
    location = models.CharField(max_length=100, default="some text")
    code = models.CharField(max_length=20, default="some text", unique=True)
    logo = models.ImageField(null=True, blank=True, upload_to='enterprise_logos')
    dateOfRegistration = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    admin_salary = models.DecimalField(max_digits=10, decimal_places=3, default=0.000)
    fund = models.DecimalField(max_digits=100, decimal_places=3, default=0.000)

    def __str__(self):
        return self.name

    def get_code(self):
        return self.code

    def get_location(self):
        return self.location

    def get_logo(self):
        return self.logo
    
    def get_absolute_url(self):
        return reverse('enterprise-detail', args=[str(self.pk)])

    @property
    def get_owner(self):
        return self.PDG

    class Meta:
        db_table = 'Enterprise'
        permissions = (
            ('add_admin', 'can add enterprise administrator'),
            ('suspend_pdg', 'can suspend the founder of the enterprise'),
            ('activate_pdg', 'can activate the pdg of the enterprise'),
        )


class AdministratorProfile(models.Model):
    """ Administrator """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,  primary_key=True, to_field='email')
    enterprises_status = models.JSONField(blank=True, null=True)
    completion_bonus = models.JSONField(blank=True, null=True)


@receiver(post_save, sender=Enterprise)
def set_pdd_dg_status(sender, instance, created, **kwargs):
    """
    AUTOMATICALLY SET A STATUS OF AN ADMINISTRATOR IN AN ENTERPRISE
    WHENEVER HE/HER CREATED ONE.
    """
    if created:
        
        try:
            pdg = instance.PDG
            user_profile = AdministratorProfile.objects.get(user=instance.PDG)
            file = user_profile.enterprises_status
            if file is None:
                file = set_user_enterprise_status_value(instance.name, Status.ACTIVE)
                if file is not False:
                    user_profile.enterprises_status = file
                    user_profile.save()
                    ctxt = {
                        'email': pdg.email,
                        'first_name': pdg.first_name,
                        'last_name': pdg.last_name,
                        'enterprise_name': instance.name,
                        'role': pdg.role,
                        'password': pdg.password
                    }
                    send_multi_format_email.delay('add_admin', ctxt, target_email=pdg.email)

            else:
                file = json.loads(user_profile.enterprises_status)
                file[str(instance.name)] = Status.ACTIVE
                user_profile.enterprises_status = json.dumps(file)
                user_profile.save()
                ctxt = {
                        'email': pdg.email,
                        'first_name': pdg.first_name,
                        'last_name': pdg.last_name,
                        'enterprise_name': instance.name,
                        'role': pdg.role,
                        'password': pdg.password
                    }
                send_multi_format_email('add_admin', ctxt, target_email=pdg.email)

        except Exception as e:
            return F"An error occur: {e}!"

class payment_period(models.IntegerChoices):
    """ This class """
    TASK = 0, 'TASK'
    WEEK = 1, 'WEEK'
    MONTH = 2, 'MONTH' 

class Category(models.Model):
    name = models.CharField(max_length=100, default="some text")
    salary = models.DecimalField(decimal_places=3, max_digits=10, null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, to_field='name')
    status = models.IntegerField(choices=Status.choices)
    payment_period = models.IntegerField(choices=payment_period.choices)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category-detail', args=[str(self.pk)])

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
            

class EmployeeProfile(models.Model):
    """ EMPLOYEE PROFILE """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    categories = models.JSONField(null=True, blank=True,)
    total_salary = models.DecimalField(decimal_places=3, max_digits=10, blank=True, null=True)
    user_enterprise_code = models.JSONField(null=True, blank=True)
    enterprises_status = models.JSONField(blank=True, null=True)
    user_enterprise_salary = models.JSONField(blank=True, null=True)
    completion_bonus = models.JSONField(blank=True, null=True)
    added_by = models.JSONField(blank=True, null=True) ##user and the date


    def get_absolute_url(self):
        return reverse('employee-detail', args=[str(self.pk)])
   

@receiver(post_save, sender=MyUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "EMPLOYEE":
        Employees_group = Group.objects.get(name='Employees')
        instance.groups.add(Employees_group)
        try:
            if instance.groups.filter(name="Administrators").exists():
                group = Group.objects.get(name="Administrators")
                instance.groups.remove(group)
            else:
                pass
        except:
            pass
        instance.save()
        EmployeeProfile.objects.create(user=instance)


class CustomPermissions(models.Model):
    """Personalized permissions of the system that are not under models are specified here  """
    class Meta:
        # stop database creation
        managed = False
        # stop the auto-creation of default permissions
        default_permissions = ()
        # set customize permissions
        permissions = (
            ('add_employee', 'can add employee to enterprise'),
            ('assign_goal_to_employee', 'can assign goal to employee'),
            ('suspend_employee', 'can suspend employee'),
            ('activate_employee', 'can activate employee'),
            ('report_employee', 'can report employee'),
            ('validate_report', 'can validate report'),
        )

class ActionType(models.IntegerChoices):
    UNKNOWN = 0, 'UNKNOWN'
    ADD = 1, 'ADD'
    DEACTIVATE = 2, 'DEACTIVATE'
    SUSPEND = 3, 'SUSPEND'
    REMOVE = 4, 'REMOVE'
    UPDATE = 5, 'UPDATE'
    WITHDRAW = 6, 'WITHDRAW'
    DEPOSIT = 7, 'DEPOSIT'
    TRANSFER = 8, 'TRANSFER'

class UserRecords(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='email')
    action_time = models.DateTimeField(auto_now_add=True)
    action_type  = models.IntegerField(choices=ActionType.choices)
    related_object = models.CharField(max_length=255, null=True)
    action = models.TextField(_('action performed'), max_length=255, null=True, blank= True)


# \\\\\\\\\\\\\\\\\\\\ Utils function of models  ///////////////////////////
@app.task
def send_multi_format_email(template_prefix, template_ctxt, target_email):
    subject_file = 'EGT/%s_subject.txt' % template_prefix
    txt_file = 'EGT/%s.txt' % template_prefix
    html_file = 'EGT/%s.html' % template_prefix

    subject = render_to_string(subject_file).strip()
    from_email = settings.EMAIL_FROM
    to = target_email
    bcc_email = settings.EMAIL_BCC
    text_content = render_to_string(txt_file, template_ctxt)
    html_content = render_to_string(html_file, template_ctxt)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to], bcc=[bcc_email])
    msg.attach_alternative(html_content, 'text/html')

    msg.send()


def return_jsonfield_value(instance_name: str, value):
    """ set the status value of the user for the specified enterprise name """
    new = {
        instance_name: value,
    }
    return json.dumps(new)
   

def set_record(user: get_user_model(), related_object: str, action_type: ActionType, modification: str): # type: ignore
    """ set user records """
    if not get_user_model().objects.filter().exists():
        #check if the user exists
        raise ValueError(f'The user {user.email} does not exists.')
    
    UserRecords.objects.create(user=user, action_type=action_type, action=modification)


def _get_user_profile(user: get_user_model()): # type: ignore
    """ This helper function return the userprofile of every type of user (employee/administrator) """
    if user.role == MyUser.Role.ADMINISTRATOR:
        return AdministratorProfile.objects.get(user=user)
    elif user.role == MyUser.Role.EMPLOYEE:
        return EmployeeProfile.objects.get(user=user)




#\\\\\\\\\\\\\\\\\\\\\\\\ enterprise user groups ///////////////////////

def check_user_enterprise_status(user: get_user_model(), enterprise: Enterprise): # type: ignore
    # check enterprise status
    if enterprise.status in [Status.DEACTIVATED, Status.SUSPENDED]:
        return None
    #  check user enterprise status
    user_profile = _get_user_profile(user)
    if user_profile.enterprises_status == None:
        logging.warning("The user is not a member of any enterprise.")
        return None

    try:
        data = json.loads(user_profile.enterprises_status)
        status = data[enterprise.name]
        if status not in [Status.ACTIVE, Status.DEACTIVATED, Status.SUSPENDED]:
            logging.error(f"Unknown user status: {status} for enterprise: {enterprise.name}")
            return None
        return status

    except Exception as e:
        logging.error(f"Error checking user status for enterprise: {enterprise.name}: {e}")
        return None


def change_user_enterprise_status(user: get_user_model(), enterprise_name: str, new_status: int): # type: ignore
    """
    This function changes the user's enterprises_status for both employees and administrators.
    """
    # Check if the user exists
    try:
        # Retrieve the user object using the provided email address of the user parameter
        user_object = get_user_model().objects.get(email=user.email)
    except get_user_model().DoesNotExist:
        # If the user doesn't exist, raise an appropriate exception
        # raise UserDoesNotExistError(f"User with email {user.email} does not exist.")
        raise UserDoesNotExist(f"User with email {user.email} does not exist.")
    
    try:
        enterprise = Enterprise.objects.get(name = enterprise_name)
    except Enterprise.DoesNotExist:
        raise ValueError(f'Enterprise {enterprise_name} does not exists.')

  
    # Check the user's role
    if user_object.role == MyUser.Role.ADMINISTRATOR:
        try:
            # Retrieve the administrator profile associated with the user
            admin_profile = AdministratorProfile.objects.get(user=user_object)
        except AdministratorProfile.DoesNotExist:
            # If the administrator profile doesn't exist, raise an appropriate exception
            raise AdministratorProfileDoesNotExistError(f"Administrator profile for user {user.email} does not exists.")

        if admin_profile.enterprises_status == None:
            # Set the enterprise status for the administrator
            item = set_user_enterprise_status_value(enterprise_name, new_status)
            admin_profile.enterprises_status = item
            admin_profile.save()
        else:
            data = json.loads(admin_profile.enterprises_status)
            data[enterprise_name] = new_status
            admin_profile.enterprises_status = json.dumps(data)
            admin_profile.save()

    elif user_object.role == MyUser.Role.EMPLOYEE:
        try:
            # Retrieve the employee profile associated with the user
            employee_profile = EmployeeProfile.objects.get(user=user_object)
        except EmployeeProfile.DoesNotExist:
            # If the employee profile doesn't exist, raise an appropriate exception
            raise EmployeeProfileDoesNotExistError(f"Employee profile for user {user.email} does not exist.")

        # Set the enterprise status for the employee
        item = set_user_enterprise_status_value(enterprise_name, new_status)
        employee_profile.enterprises_status.update(item)
        employee_profile.save()
    else:
        # If the user's role is invalid, raise an appropriate exception
        raise InvalidUserRoleError(f"User with email {user.email} has an invalid role: {user_object.role}.")


def set_user_enterprise_status_value(enterprise_name: str, value: int):
    """ Set the status value of the user for the specified enterprise name. """

    try:
        if value not in [Status.ACTIVE, Status.DEACTIVATED, Status.SUSPENDED]:
            raise InvalidStatusError(f"Invalid status value: {value}.")

        new = {
            str(enterprise_name): value,
        }

        return json.dumps(new)

    except Exception as e:
        # Catch and log any unexpected exceptions
        logger.error(f"Error setting user enterprise status: {e}")
        return False


def set_enterprise_code(name: str) -> str:
    """
    Generate a unique enterprise code using the provided enterprise name.

    Args:
        name (str): The enterprise's name.

    Returns:
        str: The generated enterprise code.
    """

    if not name:
        raise ValueError("Enterprise name cannot be empty.")

    name = name.upper().replace(" ", "")

    if len(name) <= 5:
        code = name
    else:
        start = name[0:2]
        middle = name[int(len(name) / 2)]
        end = name[-2:]
        code = start + middle + end

        if Enterprise.objects.filter(code=code).exists():
            number = len(Enterprise.objects.filter(Q(code=code))) + 1
            code = code + '-' + str(number) + "-"

    return code


def create_group(group_name: str):
    """
    Create a new group if it doesn't exist, otherwise return the existing group.
    """
    try:
        if not Group.objects.filter(name=group_name).exists():
            return Group.objects.create(name=group_name)
        else:
            return Group.objects.get(name=group_name)
    except Exception as e:
        logging.error(f"Error creating group: {e}")
        return False
        

def add_user_to_group(user: get_user_model(), group_name: str): # type: ignore
    """
    Add a user to a specific group if both user and group exist.
    """
    try:
        group_instance = Group.objects.get(name=group_name)
        user.groups.add(group_instance)
        user.save()
        return user
    except Group.DoesNotExist:
        logging.error(f"Group with name '{group_name}' does not exist.")
        return False
    except get_user_model().DoesNotExist:
        logging.error(f"User with email '{user.email}' does not exist.")
        return False
    except Exception as e:
        logging.error(f"Error adding user to group: {e}")
        return False


def remove_user_from_group(user: get_user_model(), group_name: str): # type: ignore
    """
    Remove a user from a specific group if both user and group exist.
    """
    try:
        user_instance = get_user_model().objects.get(email=user.email)
        group_instance = Group.objects.get(name=group_name)
        user_instance.groups.objects.remove(group_instance)
        user_instance.save()
        return user_instance
    except Group.DoesNotExist:
        logging.error(f"Group with name '{group_name}' does not exist.")
        return False
    except get_user_model().DoesNotExist:
        logging.error(f"User with email '{user.email}' does not exist.")
        return False
    except Exception as e:
        logging.error(f"Error removing user from group: {e}")
        return False


def deactivate_enterprise_pdg_admin_and_add_admin(administrator: get_user_model(), enterprise: Enterprise, new_administrator: get_user_model()): # type: ignore
    """
    Deactivate the PDG of the enterprise and add an administrator.

    Or we can deactivate the previous administrator and add a new one,
    since an enterprise can only have one active PDG or one active administrator
    """

    # Verify administrator and new administrator roles
    if administrator.role != MyUser.Role.ADMINISTRATOR or new_administrator.role != MyUser.Role.ADMINISTRATOR:
        raise ValueError("Both administrator and new_administrator must have the ADMINISTRATOR role.")

    if check_user_status(new_administrator) in [Status.DEACTIVATED, Status.SUSPENDED]:
        raise ValueError(f"User {new_administrator.email} is not active.")
    
    # Handle deactivation of PDG and addition for the admin
    if enterprise.PDG == administrator:
        deactivate_user(administrator, enterprise)
        # change_user_enterprise_status(administrator, enterprise.name, Status.DEACTIVATED)
        add_new_administrator(new_administrator, enterprise)

    # Handle deactivation and addition for the administrator
    elif enterprise.admins.last() == administrator and enterprise.PDG == new_administrator:
        if enterprise.PDG == new_administrator:
            deactivate_user(administrator, enterprise)
            # change_user_enterprise_status(administrator, enterprise.name, Status.DEACTIVATED)
            add_new_administrator(new_administrator, enterprise)

    elif enterprise.admins.last() == administrator:
        deactivate_user(administrator, enterprise)
        # change_user_enterprise_status(administrator, enterprise.name, Status.DEACTIVATED)
        add_new_administrator(new_administrator, enterprise)


def deactivate_enterprise_employee(employee: get_user_model(), enterprise: Enterprise): # type: ignore
    """ Deactivate an employee from an enterprise """
    if employee.role != MyUser.Role.EMPLOYEE or user_belong_to_enterprise(employee, enterprise) == False:
        raise ValueError("Employee must have the EMPLOYEE role and must belong to the enterprise.")
    
    try:
        deactivate_user(employee, enterprise)
    except Exception as e:
        logging.error(f"Error deactivating employee {employee.email} from enterprise {enterprise.name}: {e}")


def deactivate_pdg(administrator: get_user_model(), enterprise: Enterprise): # type: ignore
    """ Th"""
    if not user_belong_to_enterprise(administrator, enterprise):
        raise ValueError(f'User {administrator.email} does not belong to the enterprise {enterprise.name}.')
    
    try:
        # Update PDG enterprise status
        pdg_profile = AdministratorProfile.objects.get(user=administrator)
        file = json.loads(pdg_profile.enterprises_status)
        file[enterprise.name] = Status.DEACTIVATED
        pdg_profile.enterprises_status = json.dumps(file)
        pdg_profile.save()

        # Remove the PDG from the enterprise group
        administrator.groups.remove(name=enterprise.name)
        administrator.save()

        # Send deactivation confirmation email to the PDG
        ctxt = {
            'email': administrator.email,
            'first_name': administrator.first_name,
            'last_name': administrator.last_name,
            'enterprise_name': enterprise.name,
            'role': administrator.role,
            'password': administrator.password
        }
        send_multi_format_email.delay('deactivation_admin', ctxt, target_email=administrator.email)

    except Exception as e:
        print(f"Error deactivating PDG: {e}")


def deactivate_user(user: get_user_model(), enterprise: Enterprise): # type: ignore
    """ 
    Deactivate a user from an enterprise. 
    
    Set the user enterprise status to the corresponding to DEACTIVATED.
    Remove the user to the enterprise group and send and email to 
    the user( administrator or employee)
    """
    if user_belong_to_enterprise(user, enterprise) == False:
        raise ValueError(f'User {user.email} does not belong to the enterprise {enterprise.name}.')

    try:
        user_profile = AdministratorProfile.objects.get(user=user)
    except AdministratorProfile.DoesNotExist:
        pass

    try:
        user_profile = EmployeeProfile.objects.get(user=user)
    except EmployeeProfile.DoesNotExist:
        pass

    file = json.loads(user_profile.enterprises_status)
    file[enterprise.name] = Status.DEACTIVATED
    user_profile.enterprises_status = json.dumps(file)
    user_profile.save()

    # Send deactivation confirmation email to the PDG
    ctxt = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'enterprise_name': enterprise.name,
        'role': user.role,
        'password': user.password
    }

    if user.role == MyUser.Role.ADMINISTRATOR:
        send_multi_format_email.delay('deactivation_admin', ctxt, target_email=user.email)
    elif user.role == MyUser.Role.EMPLOYEE:
        send_multi_format_email.delay('deactivation_employee', ctxt, target_email=user.email)


def activate_user(user: get_user_model(), enterprise: Enterprise): # type: ignore
    """ 
    Deactivate a user from an enterprise. 
    
    Set the user enterprise status to the corresponding to DEACTIVATED.
    Remove the user to the enterprise group and send and email to 
    the user( administrator or employee)
    """
    if user_belong_to_enterprise(user, enterprise) == False:
        raise ValueError(f'User {user.email} does not belong to the enterprise {enterprise.name}.')

    try:
        user_profile = AdministratorProfile.objects.get(user=user)
    except AdministratorProfile.DoesNotExist:
        pass

    try:
        user_profile = EmployeeProfile.objects.get(user=user)
    except EmployeeProfile.DoesNotExist:
        pass

    file = json.loads(user_profile.enterprises_status)
    file[enterprise.name] = Status.ACTIVE
    user_profile.enterprises_status = json.dumps(file)
    user_profile.save()

    # Send deactivation confirmation email to the PDG
    ctxt = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'enterprise_name': enterprise.name,
        'role': user.role,
        'password': user.password
    }

    if user.role == MyUser.Role.ADMINISTRATOR:
        send_multi_format_email.delay('add_admin', ctxt, target_email=user.email)
    elif user.role == MyUser.Role.EMPLOYEE:
        send_multi_format_email.delay('activate_employee', ctxt, target_email=user.email)



def add_new_administrator(new_administrator: get_user_model(), enterprise: Enterprise):
    """ This function is add a new administrator user to enterprise.admins field """
    try:
        admin_profile = AdministratorProfile.objects.get(user=new_administrator)
    except AdministratorProfile.DoesNotExist:
        raise ValueError(f"User {new_administrator.email} is not an administrator.")
    
    try:
        """ 
        Since enterprise have a many-to-many relationship with administrator proxy user 
        we have to change the new_administrator: MyUser to new_administrator: Administrator
        """
        n_administrator = Administrator.objects.get(email= new_administrator.email)
    except Administrator.DoesNotExist:
        raise TypeError(f"Administrator user {new_administrator.email} doest not exists.")

    new_administrator = n_administrator
    del n_administrator
    # Add new administrator to enterprise admin field or add the  pdg
    if enterprise.PDG  == new_administrator:
        pass
    else:
        # to avoid adding the the pdg in the administrator list
        enterprise.admins.add(new_administrator)
        enterprise.save()
    
    # Update enterprise status in new administrator's profile
        
    if admin_profile.enterprises_status is not None:
        file = json.loads(admin_profile.enterprises_status)
        file[enterprise.name] = Status.ACTIVE
        admin_profile.enterprises_status = json.dumps(file)
        admin_profile.save()

        # Send email notification to new administrator
        ctxt = {
            'email': new_administrator.email,
            'first_name': new_administrator.first_name,
            'last_name': new_administrator.last_name,
            'enterprise_name': enterprise.name,
            'role': new_administrator.role,
            'password': new_administrator.password
        }
        send_multi_format_email.delay('add_admin', ctxt, target_email=new_administrator.email)

    else:
        file = set_user_enterprise_status_value(enterprise.name, Status.ACTIVE)
        admin_profile.enterprises_status = file
        admin_profile.save()

        # Send email notification to new administrator
        ctxt = {
            'email': new_administrator.email,
            'first_name': new_administrator.first_name,
            'last_name': new_administrator.last_name,
            'enterprise_name': enterprise.name,
            'role': new_administrator.role,
            'password': new_administrator.password
        }
        send_multi_format_email.delay('add_admin', ctxt, target_email=new_administrator.email)


def add_new_employee(employee: get_user_model(), enterprise: Enterprise, employee_password: str, employer):
    try:
        # check if employee has EMPLOYEE role
        if employee.role != MyUser.Role.EMPLOYEE:
            raise ValueError("User must have the EMPLOYEE role.")
        
        #  change the employee type to proxy user object
        employee = Employee.objects.get(email = employee.email)

        # to avoid redundancy this is how we are going to link enterprise and users
        enterprise.employees.add(employee)
        enterprise.save()

        # Update enterprise status of the new employee's profile
        employee_profile = EmployeeProfile.objects.get(user=employee)

        if employee_profile.enterprises_status != None and employee_profile.added_by != None:
            file = json.loads(employee_profile.enterprises_status)
            file[enterprise.name] = Status.ACTIVE
            employee_profile.enterprises_status = json.dumps(file)
            added_by = json.loads(employee_profile.added_by)
            if enterprise.name in added_by:
                result = added_by[enterprise.name]
                info = {
                    "administrator": employer,
                    "date": str(timezone.now())
                }
                result.append(info)
                added_by[enterprise.name] = result
                employee_profile.added_by = json.dumps(added_by)
                employee_profile.save()
            else:
                result = []
                info = {
                    "administrator": employer,
                    "date": str(timezone.now())
                }
                result.append(info)
                added_by[enterprise.name] = result
                employee_profile.added_by = json.dumps(added_by)    
                employee_profile.save()
                # set employee enterprise matriculation number
                set_employee_enterprise_code(employee, enterprise)

            
            
            # get user enterprise matriculation number
            user_code = get_employee_matriculation_number(employee, enterprise)
            # Send email notification to new administrator
            ctxt = {
                'email': employee.email,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'enterprise_name': enterprise.name,
                'role': employee.role,
                'password': employee_password,
                'user_code': user_code
            
            }
            send_multi_format_email.delay('add_employee2', ctxt, target_email=employee.email)
            
        else:
            file = set_user_enterprise_status_value(enterprise.name, Status.ACTIVE)
            employee_profile.enterprises_status = file

            result = []
            info = {
                "administrator": employer,
                "date": str(timezone.now())
            }
            result.append(info)
            added_by = return_jsonfield_value(enterprise.name, result)
            employee_profile.added_by = added_by
            employee_profile.save()

            # add user enterprise code
            set_employee_enterprise_code(employee, enterprise)
            # get user enterprise matriculation number
            user_code = get_employee_matriculation_number(employee, enterprise)
            # Send email notification to new administrator
            ctxt = {
                'email': employee.email,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'enterprise_name': enterprise.name,
                'role': employee.role,
                'password': employee_password,
                'user_code': user_code
            }
            send_multi_format_email.delay('add_employee', ctxt, target_email=employee.email)
        
        return True

    except Exception as e:
        print(ValueError(f"Error adding the new employee: {e}"))
        return False


def user_belong_to_enterprise(user: get_user_model(), enterprise: Enterprise) -> bool:
    """ This function check if the user is a membership of a particular enterprise. """ 

    if user.role == MyUser.Role.ADMINISTRATOR:
        try:
            administrator = Administrator.objects.get(email =user.email)
        except Administrator.DoesNotExist:
            administrator = user

        if enterprise.PDG == administrator:
            return True
        # user is enterprise administrator
        elif administrator in enterprise.admins.all():
            return True
        # user don't belong to the enterprise
        else:
            return False
        
    elif user.role == MyUser.Role.EMPLOYEE:
        try:
            employee = Employee.objects.get(email =user.email)
        except Employee.DoesNotExist:
            employee = user
            
        # user is enterprise employee
        if employee in  enterprise.employees.all():
           return True
        # user don't belong to enterprise
        else:
            return False
        
    # user is guest user
    else:
        return False

    





# \\\\\\\\\\\\\\\\\ user important properties /////////////////

def generate_employee_code(enterprise: Enterprise) -> str:
    """Generates employee's matriculation number based on the enterprise code."""
    code = enterprise.code
    current_date = datetime.datetime.now()
    y = str(current_date.year)
    year = y[-2:]
    employee_number = str(len(get_all_enterprise_employee(enterprise.name)))
    enterprise_code = f"{code}{year}e{employee_number}"
    return enterprise_code.upper()


def set_employee_enterprise_code(user: get_user_model(), enterprise: Enterprise):
    user_profile = EmployeeProfile.objects.get(user=user)

    if user_profile.user_enterprise_code == None:
        enterprise_code = generate_employee_code(enterprise)
        user_profile.user_enterprise_code = return_jsonfield_value(enterprise.name, enterprise_code)
        user_profile.save()

    data = json.loads(user_profile.user_enterprise_code)
    if enterprise.name not in data:
        data[enterprise.name] = generate_employee_code(enterprise)
        user_profile.user_enterprise_code = json.dumps(data)
        user_profile.save()
        return


def employee_is_admin(user: get_user_model(), enterprise: Enterprise, status: bool):
    """ 
    This function set an employee as an enterprise sub-administrator.

    The function return true for success and false for failure.
    """
    if user.role == 'EMPLOYEE':
        user_profile = EmployeeProfile.objects.get(user=user)
        if user_profile.is_admin == None:
            data = {enterprise.name: status}
            user_profile.is_admin = json.dumps(data)
            user_profile.save()
        data = json.loads(user_profile.is_admin)
        data[enterprise.name] = status
        user_profile.is_admin = json.dumps(data)
        user_profile.save()
        return True
    else:
        return False


def check_employee_is_admin(user: get_user_model(), enterprise: Enterprise):
    if user.role == 'EMPLOYEE' and user_belong_to_enterprise(user, enterprise.name) == True:
        user_profile = EmployeeProfile.objects.get(user=user)
        if user_profile.is_admin == None:
            return False
        else:
            data = json.loads(user_profile.is_admin)
            if enterprise.name in data:
                if data[enterprise.name] == False:
                    return False
                else:
                    return True
    return False


def get_employee_matriculation_number(user: get_user_model(), enterprise: Enterprise): 
    """ Return the user enterprise Matricule if exist and the user is active else return None """
    if not user_belong_to_enterprise(user, enterprise):
        return None
    
    if check_user_enterprise_status(user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED]:
        return None

    if user.role == "ADMINISTRATOR":
        return enterprise.code
    
    user_profile = _get_user_profile(user)
    try:
        data = json.loads(user_profile.user_enterprise_code)
        if enterprise.name in data:
            return data[enterprise.name]
    except:
        pass

    return None


def check_user_status(user: get_user_model()):
    if user.status in [Status.ACTIVE]:
        return True
    else:
        return False
    

def set_employee_category(user: get_user_model(), enterprise: Enterprise, category_name: str):
    """ 
    This function set employee category
    
    Returns True if successful, False if failed.
    """
    # check if parameters are valid
    if user.role != MyUser.Role.EMPLOYEE:
        return f"User '{user.email}' is not an employee."
    
    try:
        category = Category.objects.get(Q(name= category_name) & Q(enterprise= enterprise))
    except Category.DoesNotExist:
        return f"Invalid Category '{category.name}'."
    
    salary = float(category.salary)
    
    # check if user belong to the enterprise
    if not user_belong_to_enterprise(user, enterprise):
        return f"User '{user.email}' is not a member of '{enterprise.name}'."
    if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
        return f"User '{user.email}' is not an active member of '{enterprise.name}'."
    
    # get employee profile
    employee_profile = EmployeeProfile.objects.get(user=user)

    # set employee enterprise category
    try:
        if employee_profile.categories == None:
            data = return_jsonfield_value(enterprise.name, category_name)
            employee_profile.categories = data
            # set user_enterprise salary
            if employee_profile.user_enterprise_salary == None:
                data = return_jsonfield_value(enterprise.name, salary)
                employee_profile.user_enterprise_salary = data
            else:
                data = json.loads(employee_profile.user_enterprise_salary)
                data[enterprise.name] = salary
                employee_profile.user_enterprise_salary = json.dumps(data)
            employee_profile.save()
            return True
        else:
            data = json.loads(employee_profile.categories)
            data[enterprise.name] = category_name
            employee_profile.categories = json.dumps(data)
            # set user_enterprise salary
            if employee_profile.user_enterprise_salary == None:
                data = return_jsonfield_value(enterprise.name, salary)
                employee_profile.user_enterprise_salary = data
            else:
                data = json.loads(employee_profile.user_enterprise_salary)
                data[enterprise.name] = salary
                employee_profile.user_enterprise_salary = json.dumps(data)
            employee_profile.save()
            return True
            
    except Exception as e:
        # logging.warning(f"Error setting employee category for {employee_profile.user.email} in enterprise {enterprise.name}: {e}")
        return f"Error setting employee category for {employee_profile.user.email} in enterprise {enterprise.name}: {e}"




# \\\\\\\\\\\\\\\\ users of enterprises ///////////////////////////////////////

def get_all_enterprise_user(enterprise_name: str):
    users = []
    enterprise_name = enterprise_name.upper()
    try:
        enterprise = Enterprise.objects.get(name=enterprise_name)
    except Enterprise.DoesNotExists:
        return None
    
    users.append(enterprise.PDG)
    
    for a in enterprise.admins.all():
        users.append(a)
    
    for e in enterprise.employees.all():
        users.append(e)

    return users


def get_all_enterprise_employee(enterprise_name: str):
    users = []

    enterprise_name = enterprise_name.upper()
    try:
        enterprise = Enterprise.objects.get(name=enterprise_name)
    except Enterprise.DoesNotExists:
        return None
    
    for user in enterprise.employees.all():
        users.append(user)

    return users


def get_all_enterprise_active_employee(enterprise_name: str):
    users = []
    try:
        enterprise = Enterprise.objects.get(name=enterprise_name)
    except Enterprise.DoesNotExist:
        pass

    for user in enterprise.employees.all():
        if user.role == MyUser.Role.EMPLOYEE:
            if check_user_enterprise_status(user, enterprise) not in [Status.DEACTIVATED, Status.SUSPENDED, None]:
                users.append(user)

    return users


def get_all_enterprise_non_active_employee(enterprise_name: str):
    users= []
    try:
        enterprise = Enterprise.objects.get(name=enterprise_name)
    except Enterprise.DoesNotExist:
        pass

    for user in enterprise.employees.all():
        if user.role == MyUser.Role.EMPLOYEE:
            if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
                users.append(user)

    return users

 # to mode


def get_all_enterprise_non_active_administrator(enterprise_name: str):
    users = []
    try:
        enterprise = Enterprise.objects.get(name=enterprise_name)
    except Enterprise.DoesNotExist:
        pass

    list = []
    list.append(enterprise.PDG)
    for a in enterprise.admins.all():
        list.append(a)

    for user in list:
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            users.append(user)

    return users


def get_all_enterprise_active_administrator(enterprise_name: str):
    users = []
    try:
        enterprise = Enterprise.objects.get(name=enterprise_name)
    except Enterprise.DoesNotExist:
        pass

    list = []
    list.append(enterprise.PDG)
    for a in enterprise.admins.all():
        list.append(a)

    for user in list:
        if check_user_enterprise_status(user, enterprise) in [Status.ACTIVE]:
            users.append(user)

    return users


def get_all_enterprise_administrator(enterprise_name: str):
    users = []
    
    for user in get_user_model().objects.all():
        if user.groups.filter(name=enterprise_name).exists() and user.role == MyUser.Role.ADMINISTRATOR:
            users.append(user)

    return users


def get_employee_enterprise_salary(user: get_user_model(), enterprise: Enterprise):
    """ 
    Return the user salary of a specify enterprise if the user belong 
    to that enterprise and is currently active: Status.ACTIVE
    """

    if user_belong_to_enterprise(user, enterprise) == False: 
        # Check if the employee belongs to the enterprise
        raise ValueError(f"The user {user.email} is not an employee of {enterprise.name} enterprise.")
    
    if check_user_enterprise_status(user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED]:
        # check if the user is currently active in that enterprise
        logging.warning(f'This user "{user.email}" is not active.')
        return 0.0
  
    try:
        # Handle the case where the user doesn't have a category
        user_profile = _get_user_profile(user)
    
        if user_profile.categories == None:
            logging.warning(f"Employee {user.email} does not belong to any category of {enterprise.name}.")
            return 0.0
        
        categories = json.loads(user_profile.categories)
        employee_category = Category.objects.get(name=categories[enterprise.name])
        employee_salary = float(employee_category.salary)
        return employee_salary

    except Exception as e:
        logging.error(f"Error retrieving employee salary for {user_profile.user.email} in enterprise {enterprise.name}: {e}")
        return 0.0


def get_total_salary(user: get_user_model()):

    total_salary: float = 0.0

    if user.role == MyUser.Role.ADMINISTRATOR:
        #check if the admin is an active user of the enterprise
        try:
            enterprises = Enterprise.objects.filter(Q(PDG=user) | Q(admins=user))
            for company in enterprises:
                if check_user_enterprise_status(user, company) in [Status.ACTIVE]:
                    total_salary += float(company.admin_salary)
            return total_salary
        except Exception as e:
            return e
        
    elif user.role == MyUser.Role.EMPLOYEE:
        companies = user.groups.all()
        for group in companies:
            if Enterprise.objects.filter(name=str(group)).exists():
                total_salary += get_employee_enterprise_salary(user, Enterprise.objects.get(name=str(group)))

        return total_salary

