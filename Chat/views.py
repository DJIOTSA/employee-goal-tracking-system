from django.db import models

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from EGT.permissions import checkAdministratorEmployeeGroupMixin, checkAdministratorGroupMixin
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Message, Chat, ChatRoom

from rest_framework.views import Response, status, APIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from EGT.models import Enterprise, user_belong_to_enterprise, check_user_enterprise_status, Status
from .serializers import SentMessageSerializer, ChatListSerializer, MessageDetailSerializer


EMPTY = ["", " "]

def getChatRoom_name(chat: Chat,user: get_user_model()):
    """ 
    Return the name of the group if chat.is_group= True or
    another participant different from the one sending the 
    message
    """

    if chat.is_group:
        # for group discussion
        return chat.name
    
    # get message
    elif chat.participants.all().count() == 2:
        for u in chat.participants.all():
            if u != user:
                return u.email

    return None



class CreateMessage(APIView):
    """ 
    Sent a message TO A GROUP or to a single user.
    For now user cannot create chat group
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class= SentMessageSerializer

    def post(self, request, format=None):
        checkAdministratorEmployeeGroupMixin(self)

        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        #  get data  
        chat_id = serializer.validated_data["chat_id"]
        recipient = serializer.validated_data["recipient"]
        message_content = serializer.validated_data["message_content"]
        enterprise_name = serializer.validated_data["enterprise_name"].upper()
        created_at = timezone.now()
        sender = request.user

        if chat_id is None and recipient is None:
            content={
                "detail": _("Invalid inputs! Please specify the group discussion or a receiver")
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        if message_content is None or message_content in EMPTY:
            content={
                "detail": _("Invalid inputs! Empty message are not allowed.")
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
    
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _("Invalid enterprise name")
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        # in case chat and recipient i=are sent
        if chat_id is not None and  recipient is not None:
           
            #  authenticate recipient user
            if not user_belong_to_enterprise(recipient, enterprise):
                content={
                    "detail": _("Recipient user is not a member of this enterprise.")
                }
                return Response(content, status.HTTP_400_BAD_REQUEST)
            if check_user_enterprise_status(recipient, enterprise) not in [Status.ACTIVE]:
                content={
                    "detail": _("Recipient user is not active.")
                }
                return Response(content, status.HTTP_400_BAD_REQUEST)
            
            try:
                chat = Chat.objects.get(id=chat_id, is_group=False, enterprise=enterprise)
            except Chat.DoesNotExist:
                content = {
                    "detail": _("Chat not found! chat_id and recipient don't match.")
                }
                return Response(content, status.HTTP_404_NOT_FOUND)
            
            if chat.participants.all().count() == 2 and chat.participants in [request.user, recipient]:
                # create message
                message = Message.objects.create(
                    sender = request.user,
                    recipient= recipient,
                    message_content= message_content,
                    created_at = created_at
                )

                # create chatRoom instance
                chat_room = ChatRoom.objects.create(chat= chat, message=message)

                content={
                    "detail": _("created.")
                }
                return Response(content, status.HTTP_201_CREATED)

            content = {
                "detail": _("Invalid inputs!")
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get/create chat and create message
        if chat_id is None:
            #  authenticate recipient user
            if not user_belong_to_enterprise(recipient, enterprise):
                content={
                    "detail": _("Recipient user is not a member of this enterprise.")
                }
                return Response(content, status.HTTP_400_BAD_REQUEST)
            if check_user_enterprise_status(recipient, enterprise) not in [Status.ACTIVE]:
                content={
                    "detail": _("Recipient user is not active.")
                }
                return Response(content, status.HTTP_400_BAD_REQUEST)

            try:
                # get or create chat
                participants = [request.user, recipient]
                chat , created= Chat.objects.get_or_create(Q(is_group=False) & Q(participants__in=participants) & Q(enterprise=enterprise))
                print(chat)
                if created:
                    chat.participants.add(*participants)
                    chat.save()
                # create message
                message = Message.objects.create(
                    sender = request.user,
                    recipient= recipient,
                    message_content= message_content,
                    created_at = created_at
                )

                # create chatRoom instance
                chat_room = ChatRoom.objects.create(chat= chat, message=message)

                content={
                    "detail": _("created.")
                }
                return Response(content, status.HTTP_201_CREATED)
            
            except Exception as e:
                content={
                    "detail": _(f"An error occur: {e}")
                }
                return Response(content, status.HTTP_400_BAD_REQUEST)
                

        if recipient is None:
            try:
                if request.user.role != "ADMINISTRATOR":
                    chat = Chat.objects.get(id=chat_id, participants__in = [request.user], enterprise=enterprise)
                chat = Chat.objects.get(id=chat_id, enterprise=enterprise)
            except Chat.DoesNotExist:
                content = {
                    "detail": _("Chat not found")
                }
                return Response(content, status.HTTP_404_NOT_FOUND)
                
            # create message
            message = Message.objects.create(
                sender = request.user,
                recipient= recipient,
                message_content= message_content,
                created_at = created_at
            )

            # create chatRoom instance
            chat_room = ChatRoom.objects.create(chat= chat, message=message)

            content={
                "detail": _("created.")
            }
            return Response(content, status.HTTP_201_CREATED)            



class ChatList(generics.ListAPIView):
    """ list of discussions of user """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class =  ChatListSerializer
    pagination_class = PageNumberPagination
    queryset = Chat.objects.all()
    lookup_field = "pk"
    
    def get(self, request, format=None):
        checkAdministratorEmployeeGroupMixin(self)

        # get enterprise name
        enterprise_name= request.GET.get("enterprise_name", '').upper()

        if enterprise_name == "":
            content = {
                "detail": _("Enterprise name parameter require!")
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail":_('Invalid enterprise name.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  chat list 
        chat_ids = [c.id for c in Chat.objects.filter(enterprise=enterprise, participants__in=[request.user])]
        if request.user.role == "ADMINISTRATOR":
            enterprise_groups = [c.id for c in Chat.objects.filter(enterprise=enterprise, is_group=True) if c.id not in chat_ids]
            chat_ids.extend(enterprise_groups)
        
        queryset= Chat.objects.filter(id__in = chat_ids)
        page = self.paginate_queryset(queryset)

        if page:
            serializer_data = self.serializer_class(page, context={"request": request, "user":request.user}, many=True)
            return self.get_paginated_response(serializer_data.data)


class CustomPagination(PageNumberPagination):
    page_size = 100

class ChatMessageList(generics.RetrieveAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class =  ChatListSerializer
    pagination_class = CustomPagination
    queryset = Chat.objects.all()
    lookup_field = "pk"


    def get(self, request, *args, **kwargs):
        checkAdministratorEmployeeGroupMixin(self)

        obj = self.get_object()

        enterprise = obj.enterprise
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        if request.user.role != "ADMINISTRATOR" and request.user not in obj.participants.all():
            raise PermissionDenied


        messages = [cr.message.id for cr in ChatRoom.objects.filter(chat=obj)]
        queryset = Message.objects.filter(id__in=messages)
        page = self.paginate_queryset(queryset)
        if page:

            serialized_data = MessageDetailSerializer(page, many=True)
            
            return self.get_paginated_response(serialized_data.data)


class MessageDetails(generics.RetrieveAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all()
    serializer_class = MessageDetailSerializer
    lookup_field = "pk"

    def get(self, request , *args, **kwargs):
        checkAdministratorEmployeeGroupMixin(self)

        return super().get(request, *args, **kwargs)

