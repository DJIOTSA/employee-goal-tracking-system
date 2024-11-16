from django.db import models
from django.utils import timezone
from EGT.models import (
    Employee,
    Administrator,
    Status,
    Enterprise,
    check_user_enterprise_status,
)
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from Chat.models import create_group_chat, Chat

ACTIVITY = 'A'
GOAL = 'G'
import time

"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
GOAL SECTIONS

"""

class Rate(models.IntegerChoices):
    """ For report rate field"""
    NULL = 0, 'Null'
    ACCEPTABLE = 100, 'Acceptable'
    GOOD = 200, 'Good'
    VERY_GOOD = 300, 'Very Good'
    EXCELLENT = 400, 'Excellent'
    PERFECT = 500, 'Perfect'


class RepeatOption(models.IntegerChoices):
    """ For goal and activities """
    NO = 0, "No"
    DAILY = 1, "Daily"
    WEEKLY = 2, "Weekly"
    MONTHLY = 3, "Monthly"


class GoalImportance(models.IntegerChoices):
    """ for goal and activities """
    NORMAL = 1, "NORMAL"
    IMPORTANT = 2, "IMPORTANT"
    VERY_IMPORTANT = 3, "VERY_IMPORTANT"


class ReportStatus(models.IntegerChoices):
    """ For Activities, reports and goals status field. """
    REJECTED        = 0, "REJECTED"
    ACCEPTED        = 1, "ACCEPTED"
    PENDING         = 2, "PENDING"
    PAID            = 3, "PAID"


class TaskCompletionStatus(models.IntegerChoices):
    """ task completion status for activities and goal """
    SUBMIT      = 0, "SUBMIT"
    COMPLETED   = 1, "COMPLETED"


class Goal(models.Model):
    """ This models if responsible of goals of every enterprise. """
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, to_field='email', related_name='creator')
    title = models.CharField(max_length=200, default="some text")
    description = models.TextField(max_length= 10000, default="some text")
    attached_file = models.FileField(blank=True, null=True, upload_to='goals/files')
    attached_file1 = models.FileField(blank=True, null=True, upload_to='goals/files')
    attached_file2 = models.FileField(blank=True, null=True, upload_to='goals/files')
    starting_date= models.DateTimeField(default=timezone.now)
    ending_date = models.DateTimeField(blank=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, to_field='name')
    users_in_charge = models.ManyToManyField(
        get_user_model(), 
        verbose_name=_("users_in_charge"),
        blank=True,
        help_text=_(
            "Enterprise user's in charge of the the goal. Those users will get goal assertion permissions"
        ),
        related_name="users_in_charge_set",
        related_query_name="users_in_charge",
    )
    goal_manager = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, to_field='email', related_name="manager", null=True)
    bonus = models.DecimalField(max_digits=10, decimal_places=3, default=0.0, null=True )
    date_of_registration = models.DateTimeField(default=timezone.now)
    important = models.IntegerField(choices=GoalImportance.choices, default=GoalImportance.NORMAL)
    is_done = models.IntegerField(choices=TaskCompletionStatus.choices, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    repeat = models.IntegerField(choices=RepeatOption.choices, default=RepeatOption.NO)
    status = models.IntegerField(choices=ReportStatus.choices, null=True, blank=True)
    repetition_num = models.IntegerField(null=True, blank=True)

    def get_repetition_num(self):
        return self.repetition_num
    
    def get_repeat_option(self):
        return self.repeat
    
    def get_goal_enterprise(self):
        """Get goal enterprise """
        return self.enterprise
    
    def get_task_bonus(self):
        """ Return the bonus field of a goal or an activity"""
        return (float) or 0.0

    def get_goal_id(self):
        return self.id
    
    def get_users_in_charge(self):
        return self.users_in_charge.all()
    
    def get_absolute_url(self):
        return reverse('goal-detail', kwargs={"pk": self.pk})
    
    # obj.get_absolute_url(self):
    #     return reverse("model_detail", kwargs={"pk": self.pk})
    
    
    def get_repeat_target_next_start_end_date(self):
        """ 
        This view calculate and return the next starting and ending date of a target
        """
        if self.repeat == RepeatOption.NO:
            return None, None, None
        
        prev_starting_date = self.starting_date
        prev_ending_date= self.ending_date
        prev_repetition_num= self.repetition_num if self.repetition_num != None else 0

        next_starting_date: datetime
        next_ending_date: datetime
        next_repetition_num: int

        if self.repeat == RepeatOption.DAILY:
            next_starting_date = prev_starting_date + timedelta(days=1)
            next_ending_date = prev_ending_date + timedelta(days=1)
            next_repetition_num  = prev_repetition_num + 1

            return next_starting_date, next_ending_date, next_repetition_num
        if self.repeat == RepeatOption.WEEKLY:
            next_starting_date = prev_starting_date + timedelta(weeks=1)
            next_ending_date = prev_ending_date + timedelta(weeks=1)
            next_repetition_num  = prev_repetition_num + 1

            return next_starting_date, next_ending_date, next_repetition_num
        if self.repeat == RepeatOption.MONTHLY:
            next_starting_date = add_one_month(prev_starting_date)
            next_ending_date = add_one_month(prev_ending_date)
            next_repetition_num  = prev_repetition_num + 1
        
            return next_starting_date, next_ending_date, next_repetition_num

    
    def repeat_management(self):
        try:
            next_starting_date, next_ending_date, next_repetition_num = self.get_repeat_target_next_start_end_date()
            option = self.repeat
            if option not in  [RepeatOption.NO, None]:
                if option == RepeatOption.DAILY:
                    self.starting_date = next_starting_date
                    self.ending_date = next_ending_date
                    self.repetition_num = next_repetition_num
                    self.save()

                if option == RepeatOption.WEEKLY:
                    self.starting_date = next_starting_date
                    self.ending_date = next_ending_date
                    self.repetition_num = next_repetition_num
                    self.save()

                if option == RepeatOption.MONTHLY:
                    self.starting_date = next_starting_date
                    self.ending_date = next_ending_date
                    self.repetition_num = next_repetition_num
                    self.save()
        except Exception as e:
            print(f"exception {e}")


                

    class Meta:
        db_table= "Goals"


class Activities(models.Model):
    """ This models is responsible for activities of every goal."""
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE,)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='created_by')
    employees = models.ManyToManyField(
        get_user_model(),
        verbose_name=_("employees"),
        blank=True,
        help_text=_(
            "Enterprise employee's in charge of the the activity. Those users will get activity assertion permissions"
        ),
        related_name="employees_set",
        related_query_name="employees",
    )
    submit_employees =  models.ManyToManyField(
        get_user_model(),
        verbose_name=_("submit_employees"),
        blank=True,
        help_text=_(
            "Enterprise employee's whom submit the activity."
        ),
        related_name="submit_employees_set",
        related_query_name="submit_employees",
    )
    sold_to =  models.ManyToManyField(
        get_user_model(),
        verbose_name=_("sold_to"),
        blank=True,
        help_text=_(
            "Enterprise employee's whom submit the activity."
        ),
        related_name="sold_to_set",
        related_query_name="sold_to",
    )
    title = models.CharField(max_length=200, default="some text")
    description = models.TextField(max_length= 10000, null=True)
    starting_date= models.DateTimeField(default=timezone.now)
    ending_date = models.DateTimeField(blank=True)
    attached_file = models.FileField(blank=True, null=True, upload_to='activities/files')
    attached_file1 = models.FileField(blank=True, null=True, upload_to='activities/files')
    attached_file2 = models.FileField(blank=True, null=True, upload_to='activities/files')
    bonus = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    date_of_registration = models.DateTimeField(default=timezone.now)
    is_done = models.IntegerField(choices=TaskCompletionStatus.choices, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    repeat = models.IntegerField(choices=RepeatOption.choices, default=RepeatOption.NO)
    status = models.IntegerField(choices=ReportStatus.choices, null=True, blank=True)
    repetition_num = models.IntegerField(null=True, blank=True)

    def get_repetition_num(self):
        return self.repetition_num
    
    def get_repeat_option(self):
        return self.repeat
    
    def get_activity_enterprise(self):
        """Return activity enterprise belonging."""
        return self.goal.enterprise
    
    def get_employees(self):
        """ receive a list of user add add them into employees field"""
        return self.employees.all()
        
        
    def get_task_bonus(self):
        """ Return the bonus field of a goal or an activity"""
        return float(self.bonus) or 0.0
    
    def get_repeat_target_next_start_end_date(self):
        """ 
        This view calculate and return the next starting and ending date of a target
        """
        if self.repeat == RepeatOption.NO:
            return None, None, None
        
        prev_starting_date = self.starting_date
        prev_ending_date= self.ending_date
        prev_repetition_num= self.repetition_num if self.repetition_num != None else 0

        next_starting_date: datetime
        next_ending_date: datetime
        next_repetition_num: int

        if self.repeat == RepeatOption.DAILY:
            next_starting_date = prev_starting_date + timedelta(days=1)
            next_ending_date = prev_ending_date + timedelta(days=1)
            next_repetition_num  = prev_repetition_num + 1

            return next_starting_date, next_ending_date, next_repetition_num
        if self.repeat == RepeatOption.WEEKLY:
            next_starting_date = prev_starting_date + timedelta(weeks=1)
            next_ending_date = prev_ending_date + timedelta(weeks=1)
            next_repetition_num  = prev_repetition_num + 1

            return next_starting_date, next_ending_date, next_repetition_num
        if self.repeat == RepeatOption.MONTHLY:
            next_starting_date = add_one_month(prev_starting_date)
            next_ending_date = add_one_month(prev_ending_date)
            next_repetition_num  = prev_repetition_num + 1
        
            return next_starting_date, next_ending_date, next_repetition_num

    def repeat_management(self):
        try:
            next_starting_date, next_ending_date, next_repetition_num = self.get_repeat_target_next_start_end_date()
            option = self.repeat
            if option not in  [RepeatOption.NO, None]:
                if option == RepeatOption.DAILY:
                    self.starting_date = next_starting_date
                    self.ending_date = next_ending_date
                    self.repetition_num = next_repetition_num
                    self.save()

                if option == RepeatOption.WEEKLY:
                    self.starting_date = next_starting_date
                    self.ending_date = next_ending_date
                    self.repetition_num = next_repetition_num
                    self.save()

                if option == RepeatOption.MONTHLY:
                    self.starting_date = next_starting_date
                    self.ending_date = next_ending_date
                    self.repetition_num = next_repetition_num
                    self.save()
        except Exception as e:
            print(f"exception {e}")
        

    def get_absolute_url(self):
        return reverse('activity-detail', kwargs={"pk": self.pk})

    class Meta:
        db_table = 'Activities'


@receiver(post_save, sender=Activities)
def goal_activity_user_syn(sender, created, instance, **kwargs):
    """
    Ensures that employees associated with an activity are reflected in
    the corresponding goal's user assignments.
    """
    if not created:
        if instance.employees:
            users = instance.employees.exclude(pk__in = instance.goal.users_in_charge.all())
            if users:
                instance.goal.users_in_charge.add(*users)
        elif instance.employee and instance.employee not in instance.goal.users_in_charge.all():
            instance.goal.users_in_charge.add(instance.employee)



class Report(models.Model):
    option=(
        ("G", "GOAL"),
        ("A", "ACTIVITY")
    )
    
    report = models.FileField(null=True, blank=True, upload_to='reports/files')
    date_of_submission = models.DateTimeField(auto_now_add=True)
    option = models.CharField(max_length=1, choices=option)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, blank=True, null=True)
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
    rate = models.IntegerField(choices=Rate.choices, blank=True, null=True)
    submit_late = models.BooleanField(null=True, blank=True)
    submit_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, to_field="email")
    comment = models.TextField(max_length=2000, blank=True, null=True)
    rated_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, to_field="email", related_name="evaluator", null=True)
    report_status = models.IntegerField(choices=ReportStatus.choices, null=True)
    is_bonus_credited = models.BooleanField(default= False)
    is_deleted = models.BooleanField(default=False)
    transaction_id = models.IntegerField(blank=True, null=True)
    repetition_num = models.IntegerField(blank=True, null=True)
    repeat_option = models.IntegerField(choices=RepeatOption.choices, blank=True, null=True)
    
    def get_report_option(self):
        return self.option

    def get_enterprise_name(self):  # Instance method for enterprise name
        return self.goal.enterprise.name if self.option == GOAL else self.activity.goal.enterprise.name

    def get_report_task(self):
        """ Return a goal or an activity of a Report """
        return self.goal if self.option == GOAL else self.activity

    def get_report_enterprise(self):
        """ Return report Enterprise """
        return self.goal.enterprise if self.option==GOAL else self.activity.goal.enterprise

    def get_bonus(self):  # Instance method for bonus
        return float(self.goal.bonus) or 0.0 if self.option == GOAL else float(self.activity.bonus) or 0.0

    def get_report_submit_late(self):
        return self.submit_late
    
    def get_report_is_bonus_credited(self):
        return self.is_bonus_credited
    
    def get_report_status(self):
        return self.report_status

    def get_report_submit_by(self):
        return self.submit_by

    def get_goal_task(self):
        """ Return the report goal object if exists """
        if self.option==GOAL:
            return self.goal 

    def get_activity_task(self):
        """ Return the report activity object if exists """
        if self.option==ACTIVITY:
            return self.activity 
        
    # def get_absolute_url(self):
    #     return reverse('report-detail', kwargs={"pk": self.pk})
    
    def get_absolute_url(self):
        "get absolute url "
        return reverse('report-detail', kwargs={"pk": self.pk})
    
    class Meta:
        db_table = 'Reports'



def is_user_in_charge_of_goal(user: get_user_model(), goal: Goal): # type: ignore
    """ Check if the user have permission to access the goal"""
    try:
        administrator = Administrator.objects.get(email=user.email)
    except:
        administrator = user

    # user is the goal creator
    if goal.created_by == user:
        return True
    # user is amounts users in charge
    elif user in goal.users_in_charge.all():
        return True
    # user is the goal manager
    elif goal.goal_manager == user:
        return True
    # user is the enterprise PDG
    elif goal.enterprise.PDG == administrator:
        if check_user_enterprise_status(user, goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user is the enterprise administrator
    elif administrator in goal.enterprise.admins.all():
        if check_user_enterprise_status(user, goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user have nothing to do with the goal
    else:
        return False


def is_goal_managers(user: get_user_model(), goal: Goal): # type: ignore
    try:
        administrator = Administrator.objects.get(email=user.email)
    except:
        administrator = user

    if goal.created_by == user:
        return True
    # user is the goal manager
    elif goal.goal_manager == user:
        return True
    # user is the enterprise PDG
    elif goal.enterprise.PDG == administrator:
        if check_user_enterprise_status(user, goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user is the enterprise administrator
    elif administrator in goal.enterprise.admins.all():
        if check_user_enterprise_status(user, goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user have nothing to do with the goal
    else:
        return False


def is_user_in_charge_of_activity(user: get_user_model(), activity: Activities): # type: ignore
    """ Check if the user have permission to access the activity"""
    try:
        administrator = Administrator.objects.get(email=user.email)
    except Administrator.DoesNotExist:
        administrator = user
        
    # user is the activity creator
    if activity.created_by == user:
        return True
    elif user in activity.employees.all():
        if check_user_enterprise_status(user, activity.goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user is the goal manager
    elif activity.goal.goal_manager == user:
        return True
    # user is the enterprise PDG
    elif activity.goal.enterprise.PDG == administrator:
        if check_user_enterprise_status(user, activity.goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user is the enterprise administrator
    elif administrator in activity.goal.enterprise.admins.all():
        if check_user_enterprise_status(user, activity.goal.enterprise) in [Status.ACTIVE]:
            return True
        return False
    # user have nothing to do with the goal
    else:
        return False


def get_current_week():
    """
    This function returns the current week as a tuple of three elements:
    - Start date of the week
    - End date of the week
    - Week number
    """
    # convert offset-naive (date that does not include time zone and UTC offset) to offset-aware
    today = datetime.today().astimezone()
    # Get the weekday (0 = Monday, 6 = Sunday)
    weekday = today.weekday()
    # Calculate the offset to get to Monday
    offset = timedelta(days=-weekday)
    # Get the start and end of the week
    start_of_week = today + offset
    end_of_week = start_of_week + timedelta(days=6)
    # Get the week number
    week_number = today.isocalendar()[1]
    #   return start_of_week, end_of_week, week_number
    return {
       'start_of_week': start_of_week,
       'end_of_week': end_of_week,
       'week_number': week_number
    }


def is_event_in_current_week(event_start_date, event_end_date):
    """
    This function checks if an event falls within the current week.
    """
    week=get_current_week()
    current_week_start =  week['start_of_week']
    current_week_end = week['end_of_week']
    number = week['week_number']
    return (event_start_date >= current_week_start and event_start_date <= current_week_end) or \
           (event_end_date >= current_week_start and event_end_date <= current_week_end) or \
           (event_start_date <= current_week_start and event_end_date >= current_week_end)


def is_event_in_week(event_start_date, event_end_date, year:int, month:int, week:int):
    """
    This function checks if an event falls within the a given week.
    """
    week=get_current_week()
    current_week_start =  week['start_of_week']
    current_week_end = week['end_of_week']
    number = week['week_number']
    return (event_start_date >= current_week_start and event_start_date <= current_week_end) or \
           (event_end_date >= current_week_start and event_end_date <= current_week_end) or \
           (event_start_date <= current_week_start and event_end_date >= current_week_end)

def get_repeat_target_next_start_end_date(self):
    """ 
    This view calculate and return the next starting and ending date of a target
    """
    if self.repeat == RepeatOption.NO:
        return None, None, None
    
    prev_starting_date = self.starting_date
    prev_ending_date: self.ending_date
    prev_repetition_num: self.repetition_num

    next_starting_date: datetime
    next_ending_date: datetime
    next_repetition_num: int

    if self.repeat == RepeatOption.DAILY:
        next_starting_date = prev_starting_date + timedelta(days=1)
        next_ending_date = prev_ending_date + timedelta(days=1)
        next_repetition_num  = prev_repetition_num + 1
    if self.repeat == RepeatOption.WEEKLY:
        next_starting_date = prev_starting_date + timedelta(weeks=1)
        next_ending_date = prev_ending_date + timedelta(weeks=1)
        next_repetition_num  = prev_repetition_num + 1
    if self.repeat == RepeatOption.MONTHLY:
        next_starting_date = add_one_month(prev_starting_date)
        next_ending_date = add_one_month(prev_ending_date)
        next_repetition_num  = prev_repetition_num + 1
    
    return next_starting_date, next_ending_date, next_repetition_num


def add_one_month(current_date):
    # Calculate the next month
    year = current_date.year + (current_date.month // 12)
    month = current_date.month % 12 + 1

    # Handle leap year
    if month == 2 and current_date.day == 29:
        day = 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28
    else:
        day = min(current_date.day, [31, 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])

    return current_date.replace(year=year, month=month, day=day)



