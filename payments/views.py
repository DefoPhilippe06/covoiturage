from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Payment
from .serializers import PaymentSerializer
from .services import initiate_payment
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

        if booking.passenger_id != user.id:
            raise PermissionDenied("Ce n'est pas votre réservation.")

        if Payment.objects.filter(booking=booking).exists():
            raise ValidationError("Un paiement existe déjà pour cette réservation.")

        payment = serializer.save(
            user=user,
            amount=booking.total_price,
            currency="XAF",
            status=Payment.Status.PENDING,
        )

        phone = (
            self.request.data.get("phone")
            or getattr(user, "phone", "")
            or ""
        )
        initiate_payment(payment, phone)

        return payment

    @action(detail=True, methods=["post"])
    def simulate_success(self, request, pk=None):
        """Simule un paiement réussi (sandbox / tests)."""
        payment = self.get_object()
        if payment.status != Payment.Status.PENDING:
            return Response(
                {"detail": "Paiement déjà traité."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = Payment.Status.SUCCESS
        payment.transaction_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        payment.provider_response = {
            "simulated": True,
            "message": "Paiement simulé avec succès",
        }
        payment.save()

        send_notification(
            user=payment.user,
            title="Paiement réussi",
            message=f"Votre paiement de {payment.amount} {payment.currency} a été confirmé.",
            type="PAYMENT",
        )
        send_notification(
            user=payment.booking.trip.driver,
            title="Paiement reçu",
            message=(
                f"Le passager {payment.user.username} a payé "
                f"{payment.amount} {payment.currency}."
            ),
            type="PAYMENT",
        )

        return Response(PaymentSerializer(payment).data)