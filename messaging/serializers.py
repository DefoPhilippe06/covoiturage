from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "sender_username",
            "is_mine",
            "content",
            "is_read",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("sender", "conversation")

    def get_is_mine(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.sender_id == request.user.id
        return False


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    participants_usernames = serializers.StringRelatedField(
        source="participants", many=True, read_only=True
    )

    class Meta:
        model = Conversation
        fields = (
            "id",
            "trip",
            "participants",
            "participants_usernames",
            "messages",
            "created_at",
            "updated_at",
        )