from django.db import models
from django.contrib.auth import get_user_model
from EGT.models import Enterprise
from django.dispatch import receiver
from django.db.models.signals import post_save
from EGT.models import check_user_enterprise_status, Status

class Message(models.Model):
    """
    Model for storing messages.
    """
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='received_messages', null=True)
    message_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    

class Chat(models.Model):
    """ This models represent a discussion """
    name = models.CharField(max_length=255, null=True, blank=True)
    is_group = models.BooleanField(default=False)
    participants = models.ManyToManyField(get_user_model(), related_name='chats')
    messages = models.ManyToManyField(Message, through='ChatRoom')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE)

class ChatRoom(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)



def create_group_chat(name:str, participants:list, enterprise: Enterprise):
    """
    create a group chat. participants is the list user

    returns none if name is None.
    """

    try:
        # validate parameters
        if name is None:
            return None
        chat = Chat.objects.create(name=name, is_group=True, enterprise=enterprise)
        if participants is not None:
            chat.participants.add(*participants)
            chat.save()
        return chat

    except Exception as e:
        return e
    
def get_all_enterprise_active_employees(enterprise:Enterprise):
    users = [get_user_model().objects.get(id= u.id) for u in enterprise.employees.all()]
    active_employees = [ u for u in users if check_user_enterprise_status(u, enterprise) in [Status.ACTIVE]]
    
    return active_employees


@receiver(post_save, sender=Enterprise)
def manage_enterprise_chat(sender, created, instance, **kwargs):
    if created:
        chat = create_group_chat(name=instance.name, participants=None, enterprise= instance)

    if not created and instance.employees:
        chat, create_status = Chat.objects.get_or_create(name=instance.name, is_group=True, enterprise=instance)
        users = get_all_enterprise_active_employees(instance)
        if users:
            chat.participants.add(*[u for u in users if u not in chat.participants.all()])
            chat.save()

    