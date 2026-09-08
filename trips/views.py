from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Trip
from .serializers import TripSerializer
from core.permissions import IsOwnerOrReadOnly
from bookings.models import Booking


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Pour complete / retrieve / update : accès large
        if self.action in ["complete", "retrieve", "update", "partial_update", "destroy"]:
            return Trip.objects.all()

        # Mes trajets
        if self.action == "my_trips":
            return Trip.objects.filter(driver=self.request.user)

        # Liste publique : uniquement publiés
        qs = Trip.objects.filter(status=Trip.Status.PUBLISHED)
        origin = self.request.query_params.get("origin")
        destination = self.request.query_params.get("destination")
        date = self.request.query_params.get("date")
        min_seats = self.request.query_params.get("min_seats")
        max_price = self.request.query_params.get("max_price")

        if origin:
            qs = qs.filter(origin_city__icontains=origin)
        if destination:
            qs = qs.filter(destination_city__icontains=destination)
        if date:
            qs = qs.filter(departure_datetime__date=date)
        if min_seats:
            qs = qs.filter(seats_available__gte=min_seats)
        if max_price:
            qs = qs.filter(price_per_seat__lte=max_price)
        return qs

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user, status=Trip.Status.PUBLISHED)

    def perform_update(self, serializer):
        trip = self.get_object()
        if trip.driver != self.request.user:
            raise PermissionDenied("Seul le conducteur peut modifier ce trajet.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.driver != self.request.user:
            raise PermissionDenied("Seul le conducteur peut supprimer ce trajet.")
        instance.delete()

    @action(detail=False, methods=["get"])
    def my_trips(self, request):
        qs = Trip.objects.filter(driver=request.user)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],  # écrase IsOwnerOrReadOnly
    )
    def complete(self, request, pk=None):
        trip = self.get_object()
        user = request.user

        is_driver = trip.driver_id == user.id
        is_passenger = Booking.objects.filter(
            trip=trip,
            passenger=user,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED],
        ).exists()

        if not (is_driver or is_passenger):
            raise PermissionDenied("Vous n'avez pas participé à ce trajet.")

        if trip.status not in [Trip.Status.PUBLISHED, Trip.Status.STARTED]:
            return Response(
                {"detail": "Ce trajet ne peut plus être terminé."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trip.status = Trip.Status.COMPLETED
        trip.save(update_fields=["status"])

        Booking.objects.filter(trip=trip, status=Booking.Status.CONFIRMED).update(
            status=Booking.Status.COMPLETED
        )

        return Response({"detail": "Trajet terminé.", "status": trip.status})