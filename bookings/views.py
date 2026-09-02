from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer
from trips.models import Trip
from rest_framework.exceptions import PermissionDenied
from messaging.models import Conversation
from notifications.utils import send_notification
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsOwnerOrReadOnly


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
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

        total = trip.price_per_seat * seats
        booking = serializer.save(
            passenger=user,
            total_price=total,
            status=Booking.Status.CONFIRMED
        )

        # Notification au conducteur
        send_notification(
            user=trip.driver,
            title="Nouvelle réservation",
            message=f"{user.username} a réservé {seats} place(s) sur votre trajet {trip.origin_city} → {trip.destination_city}.",
            type="BOOKING"
        )

        # Notification au passager
        send_notification(
            user=user,
            title="Réservation confirmée",
            message=f"Votre réservation pour {trip.origin_city} → {trip.destination_city} est confirmée.",
            type="BOOKING"
        )

        # Décrémente les places
        trip.seats_available -= seats
        trip.save(update_fields=["seats_available"])

        # Crée la conversation si elle n'existe pas encore
        conversation, created = Conversation.objects.get_or_create(trip=trip)
        conversation.participants.add(trip.driver, user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status != Booking.Status.CONFIRMED:
            return Response({"detail": "Réservation non annulable."}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])

        trip = booking.trip
        trip.seats_available += booking.seats
        trip.save(update_fields=["seats_available"])

        # Notifications
        from notifications.utils import send_notification

        send_notification(
            user=trip.driver,
            title="Réservation annulée",
            message=f"{booking.passenger.username} a annulé sa réservation ({booking.seats} place(s)) sur {trip.origin_city} → {trip.destination_city}.",
            type="BOOKING"
        )
        send_notification(
            user=booking.passenger,
            title="Réservation annulée",
            message=f"Votre réservation pour {trip.origin_city} → {trip.destination_city} a été annulée.",
            type="BOOKING"
        )

        return Response({
            "detail": "Réservation annulée.",
            "seats_available": trip.seats_available
        })