from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from notifications.utils import send_notification
import re


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Conversation.objects.filter(participants=self.request.user)
            .prefetch_related("messages", "participants")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        content = (request.data.get("content") or "").strip()
        if not content or content in ("<p></p>", "<p><br></p>", "<p>&nbsp;</p>"):
            return Response({"detail": "Message vide."}, status=400)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
        )
        conversation.save()

        plain = re.sub(r"<[^>]+>", "", content).strip()
        preview = (plain[:80] + "…") if len(plain) > 80 else plain

        # Notifier les AUTRES participants (pas l'expéditeur)
        for user in conversation.participants.exclude(id=request.user.id):
            send_notification(
                user=user,
                title="Nouveau message",
                message=f"{request.user.username} : {preview}",
                type="MESSAGE",
                link="/messages/",
            )

        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related("sender", "conversation")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_update(self, serializer):
        if serializer.instance.sender_id != self.request.user.id:
            raise PermissionDenied("Vous ne pouvez modifier que vos messages.")
        content = (serializer.validated_data.get("content") or "").strip()
        if not content or content in ("<p></p>", "<p><br></p>"):
            raise ValidationError({"content": "Message vide."})
        serializer.save()

    def perform_destroy(self, instance):
        if instance.sender_id != self.request.user.id:
            raise PermissionDenied("Vous ne pouvez supprimer que vos messages.")
        instance.delete()