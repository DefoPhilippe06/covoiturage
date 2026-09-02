from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer
from bookings.models import Booking
from notifications.utils import send_notification
import uuid

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        booking = serializer.validated_data["booking"]
        user = self.request.user

        if booking.passenger != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Ce n'est pas votre réservation.")

        if hasattr(booking, "payment"):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Un paiement existe déjà pour cette réservation.")

        payment = serializer.save(
            user=user,
            amount=booking.total_price,
            currency="XAF",
            status=Payment.Status.PENDING
        )
        return payment

    @action(detail=True, methods=["post"])
    def simulate_success(self, request, pk=None):
        """Simule un paiement réussi (pour les tests)"""
        payment = self.get_object()
        if payment.status != Payment.Status.PENDING:
            return Response({"detail": "Paiement déjà traité."}, status=400)

        payment.status = Payment.Status.SUCCESS
        payment.transaction_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        payment.provider_response = {"simulated": True, "message": "Paiement simulé avec succès"}
        payment.save()

        send_notification(
            user=payment.user,
            title="Paiement réussi",
            message=f"Votre paiement de {payment.amount} {payment.currency} a été confirmé.",
            type="PAYMENT"
        )
        # Notifier le conducteur
        send_notification(
            user=payment.booking.trip.driver,
            title="Paiement reçu",
            message=f"Le passager {payment.user.username} a payé {payment.amount} {payment.currency}.",
            type="PAYMENT"
        )

        return Response(PaymentSerializer(payment).data)