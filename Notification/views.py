from django.shortcuts import render
from .serializers import  NotificationSerializer
from .models import Notification, NotificationStatus
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from rest_framework import generics
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response, status
from EGT.permissions import (
    PermissionDenied,
    checkAdministratorEmployeeGroupMixin,
)

DOMAIN_NAME = "127.0.0.1:8000/"

"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    Notification VIEW SECTION
"""
# Create Notification
class NotificationCreateView(generics.CreateAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = 'pk'
    # "statistic", "month"

    def perform_create(self, serializer):
        receiver = serializer.validated_data.get("receiver")
        sender = serializer.validated_data.get("sender")
        message = serializer.validated_data.get("message")
        url = serializer.validated_data.get("url")
        time = serializer.validated_data.get("time")
       
        return serializer.save()
    

# list Notification
class NotificationList(generics.ListAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        checkAdministratorEmployeeGroupMixin(self)

        un_reads = Notification.objects.filter(Q(user=request.user))
        data = NotificationSerializer(un_reads, context={"request": request}, many=True)

        x  = _("successful!") if data.data is not None else _("YOU DON'T HAVE NEW NOTIFICATIONS")
        return Response(
            {
                "detail": x,
                "status": _("SUCCESS"),
                "notifications": data.data
            },
            status.HTTP_200_OK
        )

class UnReadNotificationList(generics.ListAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        checkAdministratorEmployeeGroupMixin(self)

        un_reads = Notification.objects.filter(user=request.user, status=NotificationStatus.UNREAD)
        data = NotificationSerializer(un_reads, context={"request": request}, many=True)
        x  = _("successful!") if data.data != None else _("YOU DON'T HAVE NEW NOTIFICATIONS")
        return Response(
            {
                "detail":x,
                "status": _("SUCCESS"),
                "notifications": data.data
            },
            status.HTTP_200_OK
        )

# detail Notification
class NotificationDetails(generics.RetrieveAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        checkAdministratorEmployeeGroupMixin(self)

        obj = self.get_object() 
        obj.mark_as_read()
        
        return super().get(request, *args, **kwargs)


# updateNotification
class NotificationUpdate(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        checkAdministratorEmployeeGroupMixin(self)
        receiver = serializer.validated_data.get("receiver")
        sender = serializer.validated_data.get("sender")
        message = serializer.validated_data.get("message")
        url = serializer.validated_data.get("url")
        time = serializer.validated_data.get("time")
       
        return serializer.save()

# delete Notification
class NotificationDelete(generics.RetrieveUpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        checkAdministratorEmployeeGroupMixin(self)
        is_deleted = serializer.validated_data["is_deleted"]

        serializer.save(is_deleted=True)














