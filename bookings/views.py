from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from .models import Booking
from .serializers import BookingSerializer
from trips.models import Trip
from messaging.models import Conversation
from notifications.utils import send_notification
from core.permissions import IsOwnerOrReadOnly


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Booking.objects.filter(passenger=self.request.user)

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]
        seats = serializer.validated_data["seats"]
        user = self.request.user

        if trip.driver == user:
            raise PermissionDenied("Vous ne pouvez pas réserver votre propre trajet.")
        if trip.seats_available < seats:
            raise PermissionDenied("Places insuffisantes.")
        if trip.status != Trip.Status.PUBLISHED:
            raise PermissionDenied("Trajet non disponible.")

        # Réservation active déjà ?
        active = Booking.objects.filter(
            trip=trip,
            passenger=user,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
                Booking.Status.COMPLETED,
            ],
        ).first()
        if active:
            raise ValidationError("Vous avez déjà une réservation sur ce trajet.")

        total = trip.price_per_seat * seats

        # Réutiliser une réservation annulée si elle existe
        cancelled = Booking.objects.filter(
            trip=trip,
            passenger=user,
            status=Booking.Status.CANCELLED,
        ).first()

        if cancelled:
            cancelled.seats = seats
            cancelled.total_price = total
            cancelled.status = Booking.Status.CONFIRMED
            cancelled.save(update_fields=["seats", "total_price", "status", "updated_at"])
            booking = cancelled
            # Important pour la réponse API
            serializer.instance = booking
        else:
            booking = serializer.save(
                passenger=user,
                total_price=total,
                status=Booking.Status.CONFIRMED,
            )

        send_notification(
            user=trip.driver,
            title="Nouvelle réservation",
            message=(
                f"{user.username} a réservé {seats} place(s) sur votre trajet "
                f"{trip.origin_city} → {trip.destination_city}."
            ),
            type="BOOKING",
        )
        send_notification(
            user=user,
            title="Réservation confirmée",
            message=(
                f"Votre réservation pour {trip.origin_city} → "
                f"{trip.destination_city} est confirmée."
            ),
            type="BOOKING",
        )

        trip.seats_available -= seats
        trip.save(update_fields=["seats_available"])

        conversation, _ = Conversation.objects.get_or_create(trip=trip)
        conversation.participants.add(trip.driver, user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Recharger pour renvoyer la bonne instance (y compris réactivée)
        instance = getattr(serializer, "instance", None)
        if instance is None:
            instance = Booking.objects.filter(
                trip=serializer.validated_data["trip"],
                passenger=request.user,
            ).order_by("-updated_at").first()
        out = self.get_serializer(instance)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status != Booking.Status.CONFIRMED:
            return Response(
                {"detail": "Réservation non annulable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])

        trip = booking.trip
        trip.seats_available += booking.seats
        trip.save(update_fields=["seats_available"])

        # Supprimer l’ancien paiement lié pour permettre un nouveau paiement
        if hasattr(booking, "payment"):
            try:
                booking.payment.delete()
            except Exception:
                pass

        send_notification(
            user=trip.driver,
            title="Réservation annulée",
            message=(
                f"{booking.passenger.username} a annulé sa réservation "
                f"({booking.seats} place(s)) sur {trip.origin_city} → "
                f"{trip.destination_city}."
            ),
            type="BOOKING",
        )
        send_notification(
            user=booking.passenger,
            title="Réservation annulée",
            message=(
                f"Votre réservation pour {trip.origin_city} → "
                f"{trip.destination_city} a été annulée."
            ),
            type="BOOKING",
        )

        return Response({
            "detail": "Réservation annulée.",
            "seats_available": trip.seats_available,
        })