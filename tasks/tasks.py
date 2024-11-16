from employee_goal_tracker.celery import app


@app.task
def repeat_daily(self):
    """
    goal every 
    """
    from tasks.models import Goal, Activities, RepeatOption  # Adjust app and model names
    from logging import getLogger

    logger = getLogger(__name__)

    for goal in Goal.objects.all():
        if goal.repeat == RepeatOption.DAILY:
            try:
                goal.repeat_management()
                logger.info(f"Successfully executed repeat_management() for goal {goal.id}")
            except Exception as e:
                logger.error(f"Error executing repeat_management() for goal {goal.id}: {e}")
        

    for activity in Activities.objects.all():
        if activity.repeat == RepeatOption.DAILY:
            try:
                activity.repeat_management()
                logger.info(f"Successfully executed repeat_management() for goal {goal.id}")
            except Exception as e:
                logger.error(f"Error executing repeat_management() for goal {goal.id}: {e}")


@app.task
def repeat_weekly(self):
    """
    goal every 
    """
    from tasks.models import Goal, Activities, RepeatOption   # Adjust app and model names
    from logging import getLogger

    logger = getLogger(__name__)

    for goal in Goal.objects.all():
        if goal.repeat == RepeatOption.WEEKLY:
            try:
                goal.repeat_management()
                logger.info(f"Successfully executed repeat_management() for goal {goal.id}")
            except Exception as e:
                logger.error(f"Error executing repeat_management() for goal {goal.id}: {e}")

    for activity in Activities.objects.all():
        if activity.repeat == RepeatOption.WEEKLY:
            try:
                activity.repeat_management()
                logger.info(f"Successfully executed repeat_management() for goal {goal.id}")
            except Exception as e:
                logger.error(f"Error executing repeat_management() for goal {goal.id}: {e}")


@app.task
def repeat_monthly(self):
    """
    goal every 
    """
    from tasks.models import Goal, Activities, RepeatOption   # Adjust app and model names
    from logging import getLogger

    logger = getLogger(__name__)

    for goal in Goal.objects.all():
        if goal.repeat == RepeatOption.MONTHLY:
            try:
                goal.repeat_management()
                logger.info(f"Successfully executed repeat_management() for goal {goal.id}")
            except Exception as e:
                logger.error(f"Error executing repeat_management() for goal {goal.id}: {e}")

    for activity in Activities.objects.all():
        if activity.repeat == RepeatOption.MONTHLY:
            try:
                activity.repeat_management()
                logger.info(f"Successfully executed repeat_management() for goal {goal.id}")
            except Exception as e:
                logger.error(f"Error executing repeat_management() for goal {goal.id}: {e}")

