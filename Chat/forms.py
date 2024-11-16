from django import forms
from .models import Chat

# Chat
class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ("receiver", "sender", "message", "url", "time")

