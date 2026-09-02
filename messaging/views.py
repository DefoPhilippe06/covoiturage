from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related("messages", "participants")

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        content = request.data.get("content", "").strip()
        if not content:
            return Response({"detail": "Message vide."}, status=400)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        conversation.save()  # met à jour updated_at
        return Response(MessageSerializer(message).data)