from django.urls import path
# Notification views
from .views import  NotificationList, NotificationDetails, NotificationDelete, UnReadNotificationList



urlpatterns = [
    # Notification
    path("list/", NotificationList.as_view(), name="list-of-all-notification"),
    path("<int:pk>/detail/", NotificationDetails.as_view(), name="notification-detail"),
    path("delete/<int:pk>/", NotificationDelete.as_view(), name="delete-notification"),
    path("un_read/", UnReadNotificationList.as_view(), name="un_read-notification")
]
