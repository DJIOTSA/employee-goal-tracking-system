from django import forms
from .models import Notification


# Notification
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ("receiver", "sender", "message", "url", "time")
