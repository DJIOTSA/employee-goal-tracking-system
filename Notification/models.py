from sys import api_version
from django.db import models
from django.contrib.auth import get_user_model
from datetime import timezone
from django.utils.translation import gettext_lazy as _
from EGT.models import Enterprise
from django.dispatch import receiver
from django.db.models.signals import post_save
from tasks.models import Goal, Activities, Report, ReportStatus, TaskCompletionStatus
from payroll.models import Transaction
from EGT.models import user_belong_to_enterprise, check_user_enterprise_status, Status
from datetime import datetime
from django.urls import reverse, path
from employee_goal_tracker.celery import app

GOAL= _("G")
ACTIVITY =_('A')
DOMAIN_NAME = "127.0.0.1:8000/"

class NotificationStatus(models.IntegerChoices):
    UNREAD = 0, 'UNREAD'
    READ = 1, 'READ'


class Notification(models.Model):
    """
    Model for managing user notifications.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.TextField()
    status = models.IntegerField(choices= NotificationStatus.choices, default=NotificationStatus.UNREAD)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=True)
    target = models.URLField(null=True, blank=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, to_field="id")

    def get_absolute_url(self):
        return reverse('notification-detail', kwargs={"pk": self.pk})

    def mark_as_read(self):
        if self.status != NotificationStatus.READ:
            self.status = NotificationStatus.READ
            self.read_at = datetime.now()
            self.save()

@app.task
def create_notification(user: get_user_model(), message:str, target, enterprise: Enterprise): # type: ignore
    notification = Notification.objects.create(
        user = user,
        message = message,
        enterprise= enterprise,
        status  = NotificationStatus.UNREAD,
        target = target
    )
    return notification
    


""" 
    NOTIFICATION FOR TASKs MODULE NOTIFICATION 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

"""\\\\\\\\\\\\\\\\\\\\\\\\\\\ GOAL NOTIFICATION FOR CREATION AND UPDATE \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"""               

@receiver(post_save, sender=Goal)
def goal_notification_handler(sender, created, instance, *args, **kwargs):
    if created:
        if instance.users_in_charge.all().count() >= 1:
            print(instance.users_in_charge.all())

            for user in instance.users_in_charge.all():
               print(f"type of use at goal_notification_handler {type(user)}")
               create_notification( 
                    user = user,
                    message = _("New goal added"),
                    enterprise=instance.enterprise,
                    target = instance.get_absolute_url()
                )

  

    if not created:
        if instance.users_in_charge.all().count() >= 1 and instance.is_done in [TaskCompletionStatus.COMPLETED]:
            for user in instance.users_in_charge.all():
                create_notification( 
                    user = user,
                    message = _(f"Target {instance.title} completed."),
                    enterprise=instance.enterprise,
                    target = instance.get_absolute_url()
                )
        
        if instance.users_in_charge.all().count() >= 1 and instance:
            for user in instance.users_in_charge.all():
                create_notification( 
                    user = user,
                    message = _(f"Target {instance.title} updated."),
                    enterprise=instance.enterprise,
                    target = instance.get_absolute_url()
                )


            



"""\\\\\\\\\\\\\\\\\\\\\\\\\\\ TRANSACTION NOTIFICATION FOR CREATION  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"""               

@receiver(post_save, sender=Transaction)
def transaction_notification_handler(sender, created, instance, **kwargs):
    if created:
        admins, employees = get_enterprise_active_administrator(instance.enterprise)
        create_notification(
            user = instance.user,
            message = _("New withdrawal record"),
            enterprise=instance.enterprise,
            target = instance.get_absolute_url()
        )


"""\\\\\\\\\\\\\\\\\\\\\\\\\\\ REPORT NOTIFICATION FOR CREATION AND UPDATE \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"""               
@receiver(post_save, sender=Report)
def report_notification_handler(sender, created, instance, *args, **kwargs):
    if created:
        enterprise = instance.get_report_enterprise()
        administrator, employee_admins = get_enterprise_active_administrator(enterprise)
        
        if len(administrator) >= 1:
            for user in administrator:
                create_notification(
                    user = user,
                    message = _("New task added."),
                    enterprise=enterprise,
                    target = instance.get_absolute_url()
                )
        if len(employee_admins) >= 1:
            for user in employee_admins:
                create_notification(
                    user = user,
                    message = _("New task added."),
                    enterprise=enterprise,
                    target = instance.get_absolute_url()
                )
                

    if not created and instance.rate or instance.report_status:
        if instance.report_status in [ReportStatus.ACCEPTED, ReportStatus.PAID, ReportStatus.REJECTED]:
            enterprise = instance.get_report_enterprise()
            administrator, s = get_enterprise_active_administrator(enterprise)
            administrator.append(instance.get_report_submit_by())
            x = ""
            if instance.report_status == ReportStatus.ACCEPTED:
                x = "ACCEPTED!"
            elif instance.report_status == ReportStatus.REJECTED:
                x = "REJECTED!"
            elif instance.report_status == ReportStatus.PAID:
                x = "PAID!"
            
            if len(administrator)>=1:
                for user in administrator:
                    print(f"User type in notification models 153:{type(user)}: {user.email}")
                    print(f"user type in notification models 153:{type(get_user_model())}")
                    create_notification(
                        user = user,
                        message = _(f"Report updated. {x}"),
                        enterprise=enterprise,
                        target = instance.get_absolute_url()
                    )
                

        
""""  HELPER FUNCTIONS SECTION  """
def get_enterprise_active_administrator(enterprise:Enterprise):
    """ Return a tuple of administrator and administrator employees"""
    administrator = []
    employee_admins = []
    if check_user_enterprise_status(enterprise.PDG, enterprise) in [Status.ACTIVE]:
        administrator.append(get_user_model().objects.get(id = enterprise.PDG.id))
    elif enterprise.admins.all().count() >= 1:
        boss = enterprise.admins.all()
        for u in boss:
            if check_user_enterprise_status(u, enterprise) in [Status.ACTIVE]:
                administrator.append(get_user_model().objects.get(id=u.id))

    # get employee_admins
    if enterprise.employee_admins.all().count() >= 1:
        for u in enterprise.employee_admins.all():
            if check_user_enterprise_status(u, enterprise) in [Status.ACTIVE]:
                employee_admins.append(get_user_model().objects.get(id=u.id))


    return administrator, employee_admins



