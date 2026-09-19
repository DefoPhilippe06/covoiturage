from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Trip, TripLocation
from .serializers import TripSerializer, TripLocationSerializer
from core.permissions import IsOwnerOrReadOnly
from bookings.models import Booking
from django.utils import timezone


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Pour complete / retrieve / update : accès large
        if self.action in [
            "complete", "retrieve", "update", "partial_update", "destroy",
            "start", "location", "location_latest",
        ]:
            return Trip.objects.all()

        # Mes trajets
        if self.action == "my_trips":
            return Trip.objects.filter(driver=self.request.user)

        # Liste publique : publiés + futurs + places
        qs = Trip.objects.filter(
            status=Trip.Status.PUBLISHED,
            departure_datetime__gte=timezone.now(),
            seats_available__gt=0,
        )
        origin = self.request.query_params.get("origin")
        destination = self.request.query_params.get("destination")
        date = self.request.query_params.get("date")
        min_seats = self.request.query_params.get("min_seats")
        max_price = self.request.query_params.get("max_price")
        near_city = self.request.query_params.get("near_city")

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

        if near_city and not origin:
            qs = qs.order_by("departure_datetime")
        else:
            qs = qs.order_by("departure_datetime")

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
        permission_classes=[permissions.IsAuthenticated],
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def start(self, request, pk=None):
        trip = self.get_object()
        if trip.driver_id != request.user.id:
            raise PermissionDenied("Seul le conducteur peut démarrer ce trajet.")
        if trip.status != Trip.Status.PUBLISHED:
            return Response(
                {"detail": f"Trajet non démarrable (statut actuel : {trip.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        trip.status = Trip.Status.STARTED
        trip.save(update_fields=["status"])
        return Response({"detail": "Trajet démarré.", "status": trip.status})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def location(self, request, pk=None):
        """Conducteur envoie sa position (trajet STARTED uniquement)."""
        trip = self.get_object()

        if trip.driver_id != request.user.id:
            raise PermissionDenied("Seul le conducteur peut partager sa position.")

        if trip.status != Trip.Status.STARTED:
            return Response(
                {"detail": "Le suivi n'est actif que lorsque le trajet est démarré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if lat is None or lng is None:
            return Response(
                {"detail": "lat et lng requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        loc = TripLocation.objects.create(
            trip=trip,
            lat=lat,
            lng=lng,
            speed=request.data.get("speed"),
        )

        # Garder seulement les 50 dernières positions
        old_ids = list(
            trip.locations.order_by("-recorded_at")
            .values_list("id", flat=True)[50:]
        )

        if old_ids:
            TripLocation.objects.filter(id__in=old_ids).delete()

        return Response(
            TripLocationSerializer(loc).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="location/latest",
        permission_classes=[permissions.IsAuthenticated],
    )
    def location_latest(self, request, pk=None):
        """Dernière position connue (passager, conducteur, admin staff)."""
        trip = self.get_object()
        user = request.user

        is_driver = trip.driver_id == user.id

        is_passenger = Booking.objects.filter(
            trip=trip,
            passenger=user,
            status__in=[
                Booking.Status.CONFIRMED,
                Booking.Status.COMPLETED,
            ],
        ).exists()

        is_admin = user.is_staff

        if not (is_driver or is_passenger or is_admin):
            raise PermissionDenied("Accès refusé.")

        loc = trip.locations.order_by("-recorded_at").first()

        if not loc:
            return Response({
                "detail": "Aucune position encore.",
                "status": trip.status,
            })

        data = TripLocationSerializer(loc).data
        data["trip_status"] = trip.status

        data["origin"] = {
            "lat": trip.origin_lat,
            "lng": trip.origin_lng,
            "city": trip.origin_city,
        }

        data["destination"] = {
            "lat": trip.destination_lat,
            "lng": trip.destination_lng,
            "city": trip.destination_city,
        }

        return Response(data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def start(self, request, pk=None):
        """Conducteur démarre le trajet → active le tracking."""
        trip = self.get_object()

        if trip.driver_id != request.user.id:
            raise PermissionDenied("Seul le conducteur peut démarrer.")

        if trip.status != Trip.Status.PUBLISHED:
            return Response(
                {"detail": "Trajet non démarrable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trip.status = Trip.Status.STARTED
        trip.save(update_fields=["status"])

        return Response({
            "detail": "Trajet démarré.",
            "status": trip.status,
        })