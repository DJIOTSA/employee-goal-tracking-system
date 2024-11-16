from rest_framework import serializers
from .models import Notification
from django.urls import reverse


# notification
class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="notification-detail", lookup_field="pk")
    
    class Meta:
        model = Notification
        fields = "__all__"

    