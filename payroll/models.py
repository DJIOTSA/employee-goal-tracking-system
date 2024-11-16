from django.db import models
from django.contrib.auth import get_user_model
from EGT.models import Enterprise, user_belong_to_enterprise, check_user_enterprise_status, Status
from django.db.models.signals import post_save
from django.dispatch import receiver
from tasks.models import Report, ReportStatus, Rate, TaskCompletionStatus, Goal, Activities
from EGT.models import (
    _get_user_profile,
    return_jsonfield_value,
)
from django.urls import reverse

from django.db.models import Q, QuerySet
import json
import numpy as np

from rest_framework.views import Response, status, PermissionDenied

EMPLOYEE = 'EMPLOYEE'
GOAL = "G"
ACTIVITY = "A"  
INSUFFICIENT_BALANCE = f"Your balance amount is insufficient. The balance must be at least 500 XAF" 
USER_HAS_NO_BONUS = f"USER HAS NO COMPLETION BONUS."

# Create your models here.

class TransactionStatus(models.IntegerChoices):
    REJECTED = 0, 'REJECTED'
    ACCEPTED = 1, 'ACCEPTED'
    PENDING = 2, 'PENDING'
    PAID = 3, 'PAID'

class TransactionType(models.IntegerChoices):
    DEPOSIT = 1, 'DEPOSIT'
    WITHDRAWAL = 0, 'WITHDRAWAL'
    TRANSFER  = 2, 'TRANSFER'

class Transaction(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, to_field='email')
    amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    date = models.DateTimeField(auto_now_add=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, to_field='name')
    remaining_salary = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    transaction_type = models.IntegerField(choices=TransactionType.choices)
    status = models.IntegerField(choices= TransactionStatus.choices)
    is_deleted = models.BooleanField(default= False)

    def get_transaction_enterprise(self):
        return self.enterprise
    
    def get_transaction_is_deleted(self):
        return self.is_deleted
    
    def get_transaction_user(self):
        return self.user

    def get_absolute_url(self):
        return reverse('transaction-detail', kwargs={"pk": self.pk})

    class Meta:
        db_table= 'Transactions'

class PaymentPeriod(models.IntegerChoices):
    DAILY = 0, "DAILY"
    WEEKLY= 1, "WEEKLY"
    MONTHLY = 2, "MONTHLY"




"""
----------------------------------------------------------------------------------------------------

PAYROLL SECTION      PAYROLL SECTION      PAYROLL SECTION      PAYROLL SECTION       PAYROLL SECTION
                
-----------------------------------------------------------------------------------------------------
"""


def tasks_bonus_management(report_instance):
    """
        For activities and goal targets, 
        the target completion bonus will be assigned:
            -  If the report_instance of the target is not submit late, 
            -  If the report_instance rate is amount [100, 200, 300, 400, 500],
            -  If the user submitting the report_instance have the authorization 
            -  And of course if the completion bonus have not been assigned yet.

        And for activities assigned to multiple users, the activities will be mark
        as done when all the users, have submit their targets report_instance.
    """
    try:
        target = report_instance.get_report_task()
        submit_by = report_instance.submit_by  # Choose target based on option
        user_profile = _get_user_profile(submit_by)
        report_instance_status  = report_instance.report_status
        is_bonus_credited = report_instance.is_bonus_credited
        rate = report_instance.rate

        # check if user meet hte requirement
        if rate in [100, 200, 300, 400, 500] and report_instance_status == ReportStatus.ACCEPTED and is_bonus_credited == False:
            # check target type
            is_goal_or_activity_employee: bool
            is_activity_employees: bool
            if report_instance.option == GOAL:
                is_goal_or_activity_employee =True
            elif report_instance.option == ACTIVITY and target.employee == submit_by:
                is_goal_or_activity_employee = True
            else:
                is_goal_or_activity_employee = False

            is_activity_employees = True if (report_instance.option==ACTIVITY and submit_by in target.employees.all()) else False
            print(f"is_goal_or_activity_employee: {is_goal_or_activity_employee}")
            print(f"is_activity_employees; {is_activity_employees}")
            # for activities with single employee and goals
            if is_goal_or_activity_employee and target.status== ReportStatus.ACCEPTED:
                
                _update_completion_bonus(user_profile, report_instance)  # Refactored bonus logic 
                report_instance.is_bonus_credited = True
                report_instance.save()
                target.is_done = TaskCompletionStatus.COMPLETED
                target.save()
                return True
                

            # for activity with multiple employees
            if is_activity_employees and submit_by in target.submit_employees.all():
                _update_completion_bonus(user_profile, report_instance)  # Refactored bonus logic 
                report_instance.is_bonus_credited = True
                report_instance.save()
                return True
        
    except Exception as e:
        print(f"An error occur: {e}")
        return False
        
    return False


def tasks_bonus_subtraction_management(report_instance):
    """
        For activities and goal targets that is not yet paid, 
        the target completion bonus will be subtracted:
            -  If the report_instance rate is not amount [100, 200, 300, 400, 500],
            -  or of course if the completion bonus have been assigned.

        And for activities assigned to multiple users, the activities will be mark
        as done when all the users, have submit their targets report_instance.
    """
    target = report_instance.goal if report_instance.option == GOAL else report_instance.activity
    submit_by = report_instance.submit_by  # Choose target based on option
    user_profile = _get_user_profile(submit_by)
    report_instance_status  = report_instance.report_status
    is_bonus_credited = report_instance.is_bonus_credited
    rate = report_instance.rate
    transaction_id = report_instance.transaction_id

    # check if user meet hte requirement
    if rate not in [100, 200, 300, 400, 500] and report_instance_status == ReportStatus.REJECTED and is_bonus_credited == True:
        # check target type
        is_goal_or_activity_employee: bool
        is_activity_employees: bool
        if report_instance.option == GOAL:
            is_goal_or_activity_employee =True
        elif report_instance.option == ACTIVITY and target.employee == submit_by:
            is_goal_or_activity_employee = True
        else:
            is_goal_or_activity_employee = False
        is_activity_employees = True if (report_instance.option==ACTIVITY and submit_by in target.employees.all()) else False
        # for activities with single employee and goals
        if is_goal_or_activity_employee and target.status == ReportStatus.REJECTED:
            _subtract_completion_bonus(user_profile, report_instance)  # Refactored bonus logic 
            report_instance.is_bonus_credited = False
            report_instance.save()
            target.is_done = TaskCompletionStatus.SUBMIT
            target.save()
            return True
            

        # for activity with multiple employees
        if is_activity_employees and submit_by in target.submit_employees.all():
            _subtract_completion_bonus(user_profile, report_instance)  # Refactored bonus logic 
            report_instance.is_bonus_credited = False
            report_instance.save()
            return True
        
    return False


def _update_completion_bonus(user_profile, report_instance):
    """ ADD COMPLETION BONUS"""
    try:
        if user_profile.completion_bonus != None:
            data = json.loads(user_profile.completion_bonus)
            enterprise_name = report_instance.get_enterprise_name()  # Store for clarity
            total = data.get(enterprise_name, 0) + report_instance.get_bonus()
            data[enterprise_name] = total
            user_profile.completion_bonus = json.dumps(data)  # Only serialize if necessary
            user_profile.save()
        else:
            enterprise_name = report_instance.get_enterprise_name()
            data = return_jsonfield_value(enterprise_name, report_instance.get_bonus())
            user_profile.completion_bonus = data
            user_profile.save()
        return True
    except Exception as e:
        # Handle errors gracefully, log or raise appropriate exceptions
        return e


def _subtract_completion_bonus(user_profile, report_instance):
    """ SUBTRACT COMPLETION BONUS """
    try:
        if user_profile.completion_bonus != None:
            data = json.loads(user_profile.completion_bonus)
            enterprise_name = report_instance.get_enterprise_name()  # Store for clarity
            total = data.get(enterprise_name, 0) - report_instance.get_bonus()
            data[enterprise_name] = total
            user_profile.completion_bonus = json.dumps(data)  # Only serialize if necessary
            user_profile.save()
        else:
            enterprise_name = report_instance.get_enterprise_name()
            data = return_jsonfield_value(enterprise_name, (-1 * report_instance.get_bonus()))
            user_profile.completion_bonus = data
            user_profile.save()
        return True
    except Exception as e:
        # Handle errors gracefully, log or raise appropriate exceptions
        return e


# gpt
# def withdrawal_request(user: get_user_model(), enterprise: Enterprise):
#     reports = Report.objects.filter(
#         (Q(option=GOAL) & Q(goal__enterprise=enterprise) & Q(goal__bonus__gt=0.0)) | (Q(option=ACTIVITY) & Q(activity__goal__enterprise=enterprise) & Q(activity__goal__bonus__gt=0.0)),
#         submit_by=user,
#         report_status=ReportStatus.ACCEPTED,
#         is_bonus_credited=True
#     )

#     goal_targets = Goal.objects.filter(id__in=[e.goal.id for e in reports if e.option == GOAL])
#     activity_targets = Activities.objects.filter(id__in=[e.activity.id for e in reports if e.option == ACTIVITY])
#     activity_employee_targets = activity_targets.filter(employee=user)
#     activity_employees_targets = activity_targets.filter(employees=user)

#     user_profile = _get_user_profile(user)
#     total = vectorized_goal_bonus_sum(goal_targets) + vectorized_goal_bonus_sum(activity_targets)

#     if total >= 500:
#         status_pending = _withdrawal_pending_completion_bonus(user_profile=user_profile, enterprise_name=enterprise.name, amount=total)

#         if status_pending:
#             reports.update(report_status=ReportStatus.PENDING)
#             goal_targets.update(status=ReportStatus.PENDING)
#             activity_employee_targets.update(status=ReportStatus.PENDING)

#             transaction, created = Transaction.objects.get_or_create(
#                 user=user,
#                 amount=total,
#                 enterprise=enterprise,
#                 transaction_type=TransactionType.WITHDRAWAL,
#                 status=TransactionStatus.PENDING
#             )

#             try:
#                 # Perform the transaction here
#                 transaction_status = True
#                 status = _withdrawal_status(
#                     user_profile=user_profile,
#                     enterprise_name=enterprise.name,
#                     status=transaction_status,
#                     transaction=transaction,
#                     reports=reports,
#                     goal_targets=goal_targets,
#                     activity_employee_targets=activity_employee_targets,
#                     activity_employees_targets=activity_employees_targets
#                 )
#                 return status
#             except Exception as e:
#                 return e
#         else:
#             return status_pending
#     else:
#         return INSUFFICIENT_BALANCE

# me
def withdrawal_request(user: get_user_model(), enterprise: Enterprise): # type: ignore
    """ 
    This operation will be use to handle the user completion bonus 
    during withdrawal request.
    
    set target and their report status to pending and subtract the total user completion bonus
    amount to the total completion bonus.  
    Or refund if the
    """

    try:
        #  filter unpaid report 
        reports = Report.objects.filter(
            (Q(option=GOAL) & Q(goal__enterprise = enterprise) & Q(goal__bonus__gt = 0.0)) | (Q(option=ACTIVITY) & Q(activity__goal__enterprise = enterprise) & Q(activity__goal__bonus__gt = 0.0)),
            submit_by = user,
            report_status = ReportStatus.ACCEPTED,
            is_bonus_credited = True    
        )
        # create a list of selected report id
        report_ids = [r.id for r in reports]
        # get targets queryset
        goal_targets = Goal.objects.filter(id__in =[e.get_goal_task().id for e in reports if e.option==GOAL])
        activity_targets = Activities.objects.filter(id__in =[e.get_activity_task().id for e in reports if e.option==ACTIVITY]) # all activities targets
        activity_employee_targets = Activities.objects.filter(id__in =[e.id for e in activity_targets if e.employee ==user]) # activities with single employee
        activity_employees_targets = Activities.objects.filter(id__in =[e.id for e in activity_targets if user in e.employees.all()]) # activities with multiple employees(list type)
        # get user profile
        user_profile = _get_user_profile(user)
        # subtract it from the total bonus (total bonus amount of the selected reports) from the user completion bonus
        goal_total = vectorized_goal_bonus_sum(goal_targets)
        activity_total = vectorized_goal_bonus_sum(activity_targets)
        total = goal_total + activity_total
        
        if total >= 500.0:  # NOTE: The default currency if XAF
            # perform withdrawal request
            status_pending = _withdrawal_pending_completion_bonus(user_profile=user_profile, enterprise_name=enterprise.name, amount=total)
            if status_pending == True:  
                
                # create the transaction raw
                try:
                    transaction = Transaction.objects.create(
                        user=user,
                        amount=total,
                        enterprise=enterprise,
                        transaction_type=TransactionType.WITHDRAWAL,
                        status=TransactionStatus.PENDING
                    )
                    transaction.save()

                    transaction_id = transaction.id
                    # update the report status to pending
                    reports.update(report_status=ReportStatus.PENDING, transaction_id=transaction_id)
                    goal_targets.update(status=ReportStatus.PENDING)
                    activity_employee_targets.update(status=ReportStatus.PENDING)

                except Exception as e:
                    print(f"THIS ERROR OCCUR during TRANSACTION INSTANCE CREATION: {e}")
                    return e

                # perform the transaction here 
                # transaction_status = False
                transaction_status = True #for successful

                #if successful update report and targets status to PAID else credit the money back and update report and targets status to  ACCEPTED
                status = _withdrawal_status(
                    user_profile=user_profile,
                    enterprise_name= enterprise.name,
                    amount= total,
                    status=transaction_status,
                    transaction=transaction,
                    reports=report_ids,
                    goal_targets=goal_targets,
                    activity_employee_targets= activity_employee_targets,
                    activity_employees_targets= activity_employees_targets
                    
                )
                return status # True for success, Literal string for failure and Exception for error
            else:
                return status_pending
        else:
            return INSUFFICIENT_BALANCE
        
    except Exception as e:
        print(f"This error occur in withdrawal_request request: {e}")
        return e
    


def _withdrawal_pending_completion_bonus(user_profile, enterprise_name: str, amount: float):
    try:
        if user_profile.completion_bonus != None:
            data = json.loads(user_profile.completion_bonus)
            enterprise_name = enterprise_name.upper() # capitalize
            if enterprise_name not in data:
                """ Check if the user has completion bonus under the given enterprise """
                return USER_HAS_NO_BONUS
            total = float(data.get(enterprise_name, 0.0))
            if total < amount:
                return INSUFFICIENT_BALANCE
            total -= amount
            data[enterprise_name] = total  # subtract the   amount
            user_profile.completion_bonus = json.dumps(data)  
            user_profile.save()
            return True # for success
        else:
            return USER_HAS_NO_BONUS

    except Exception as e:
        # Handle errors gracefully, log or raise appropriate exceptions
        print(f"THIS ERROR OCCUR AFTER TRANSACTION INSTANCE CREATION IN _WITHDRAWAL PENDING COMPLETION BONUS FUNCTION: {e}")
        return e


def _withdrawal_status(
        user_profile, 
        enterprise_name: str, 
        amount: float, 
        status: bool, 
        transaction: Transaction,
        reports: list, # list of selected report ids
        goal_targets,
        activity_employee_targets,
        activity_employees_targets
    ):
    """ 
    This check if the transaction was successful or not and update , report, targets and transaction status
    status must be a boolean and represent wether the withdrawal was successful or not
    """
    report_queryset = Report.objects.filter(id__in = reports)
    if status:
        try:
            # update the report status to PAID
            report_queryset.update(report_status = ReportStatus.PAID)
            goal_targets.update(status=ReportStatus.PAID)
            activity_employee_targets.update(status=ReportStatus.PAID) # activities with single employee
            for a in activity_employees_targets:
                #for activity with multiple user
                a.sold_to.add(user_profile.user)
                a.save()
            transaction.status = TransactionStatus.PAID
            transaction.save()
            return True    # for withdrawal success
            print(f"status change to paid and user added in sold_to")
        except Exception as e:
            print(f"THIS ERROR OCCUR DURING TRANSACTION STATUS UPDATE TO PAID IN WITHDRAWAL STATUS FUNCTION: {e}")
            return e 
        
    else:
        try:
            if user_profile.completion_bonus != None:
                data = json.loads(user_profile.completion_bonus)
                enterprise_name = enterprise_name.upper() # capitalize
                if enterprise_name not in data:
                    """ Check if the user has completion bonus under the given enterprise """
                    return USER_HAS_NO_BONUS
                total  = data[enterprise_name]
                data[enterprise_name] = total + amount # subtract the   amount
                user_profile.completion_bonus = json.dumps(data)  
                user_profile.save()
                try:
                    # update the report status to ACCEPTED
                    report_queryset.update(report_status=ReportStatus.ACCEPTED)
                    goal_targets.update(status=ReportStatus.ACCEPTED)
                    activity_employee_targets.update(status=ReportStatus.ACCEPTED) # activities with single employee
                    for a in activity_employees_targets:
                        #for activity with multiple user
                        a.sold_to.remove(user_profile.user)
                        a.save()
                    # reports.bulk_update([ReportStatus.ACCEPTED], fields=['report_status'])
                    # goal_targets.bulk_update([ReportStatus.ACCEPTED], fields=['status'])
                    # activity_employee_targets.bulk_update([ReportStatus.ACCEPTED], fields=['status'])
                    transaction.status = TransactionStatus.REJECTED
                    transaction.save()
                    return False # for rejected transaction
                except Exception as e:
                    print(f"This error occur during the transaction update to REJECTED in WITHDRAWAL STATUS FUNCTION: {e}")
                    return e
                
            else:
                return USER_HAS_NO_BONUS # for withdrawal failure
            
        except Exception as e:
            print(f" THIS ERROR OCCUR IN WITHDRAWAL STATUS FUNCTION: {e}")
            # Handle errors gracefully, log or raise appropriate exceptions
            return e


def vectorized_goal_bonus_sum(queryset):
    """
    Calculates the vectorized sum of bonuses for a given queryset of Goal objects.

    Args:
        goals_queryset (QuerySet): A queryset of Goal objects.

    Returns:
        float: The total sum of bonuses in the queryset.

    Raises:
        TypeError: If the `get_task_bonus` method of a Goal/Activities object doesn't return a numerical value.
    """

    if not queryset.exists():
        return 0.0

    try:
        # Convert queryset to NumPy array directly and access bonus field
        bonuses_array = np.array(queryset.values_list('bonus', flat=True))
        return float(np.sum(bonuses_array))
    except (AttributeError, TypeError):
        # Fallback to non-vectorized method if conversion or access fails
        bonuses = [target.get_task_bonus() for target in queryset]
        return float(sum(bonuses))


def check_user_transaction_permission(user: get_user_model(), enterprise: Enterprise, transaction: Transaction): # type: ignore
    """ 
    This function check user permission over an instance of Transaction.
     
        And Raise PermissionDenied for non authorized user
        And None for authorized user
    """
    if transaction.enterprise != enterprise:
        raise PermissionDenied
    if not user_belong_to_enterprise(user, enterprise):
        raise PermissionDenied
    if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
        raise PermissionDenied
    if user.role == EMPLOYEE and transaction.user != user:
        raise PermissionDenied
    
def user_transaction_permission(user: get_user_model(), enterprise: Enterprise, transaction: Transaction): # type: ignore
    """ 
    This function check user permission over an instance of Transaction 
        and return False if non-authorized user 
        and return True if authorized user
    """
    if transaction.enterprise != enterprise:
        return False
    if not user_belong_to_enterprise(user, enterprise):
        return False
    if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
        return False
    if user.role == EMPLOYEE and transaction.user != user:
        return False

    return True # for has permission
    
    

    



