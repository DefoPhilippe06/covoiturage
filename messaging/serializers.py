from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "conversation", "sender", "sender_username", "content", "is_read", "created_at")
        read_only_fields = ("sender",)


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    participants_usernames = serializers.StringRelatedField(source="participants", many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "trip", "participants", "participants_usernames", "messages", "created_at", "updated_at")