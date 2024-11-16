from rest_framework import serializers
from .models import Message, Chat , ChatRoom
from django.contrib.auth import get_user_model
from EGT.models import Enterprise, get_employee_matriculation_number

class SentMessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.IntegerField(allow_null=True)
    enterprise_name = serializers.CharField(max_length=255)
    class Meta:
        model = Message
        fields = ["chat_id", "recipient", "message_content", "enterprise_name"]

    def create(validated_data):
        chat_id = validated_data.pop("chat_id")
        enterprise_name = validated_data.pop("enterprise_name")
        return super().create(validated_data)
    

class MessageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"

class ChatListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="chat-detail", lookup_field="pk")
    class Meta:
        model = Chat
        fields = [ "pk", "name", "url", "is_group", "participants", "enterprise"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Access context data using self.context
        context_value = self.context.get('user')  # Replace 'key' with the actual context key
        if context_value and representation["is_group"] == False and representation["name"] is None:
            # Use the context value if it exists
            participants = representation['participants']
            for id in participants:
                if id != context_value.id:
                    user = get_user_model().objects.get(id=id)
                    enterprise = Enterprise.objects.get(id=representation["enterprise"])
                    new_value = get_employee_matriculation_number(user, enterprise)
                    if new_value:
                        representation['name'] = new_value
                        return representation
                    
        return representation

