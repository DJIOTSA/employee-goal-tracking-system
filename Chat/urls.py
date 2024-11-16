from django.urls import path
from .views import CreateMessage, ChatList, ChatMessageList, MessageDetails

urlpatterns = [
    path("send/message/", CreateMessage.as_view(), name="send-message"),
    path("list/", ChatList.as_view(), name="discussion-list"),
    path("<int:pk>/messages/", ChatMessageList.as_view(), name="chat-detail"),
    path("message/<int:pk>/detail/", MessageDetails.as_view(), name="message-detail"),
]
