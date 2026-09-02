from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from .models import Review
from .serializers import ReviewSerializer
from trips.models import Trip
from bookings.models import Booking


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.all()

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]
        reviewed_user = serializer.validated_data["reviewed_user"]
        user = self.request.user

        # Le trajet doit être terminé
        if trip.status != Trip.Status.COMPLETED:
            raise ValidationError("Vous ne pouvez noter que les trajets terminés.")

       # Vérification stricte de participation
        is_driver = trip.driver == user
        is_passenger = Booking.objects.filter(
            trip=trip,
            passenger=user,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED]
        ).exists()

        if not (is_driver or is_passenger):
            raise ValidationError("Vous n'avez pas participé à ce trajet.")
        # On ne peut pas se noter soi-même
        if reviewed_user == user:
            raise ValidationError("Vous ne pouvez pas vous noter vous-même.")

        review = serializer.save(reviewer=user)

        # Notification
        from notifications.utils import send_notification
        send_notification(
            user=reviewed_user,
            title="Nouvel avis reçu",
            message=f"{user.username} vous a donné {review.rating}★ sur le trajet {trip.origin_city} → {trip.destination_city}.",
            type="REVIEW"
        )