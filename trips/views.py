from math import perm

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Trip
from .serializers import TripSerializer
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from core.permissions import IsOwnerOrReadOnly


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
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

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

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

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        trip = self.get_object()
        if trip.driver != request.user:
            raise PermissionDenied("Seul le conducteur peut terminer le trajet.")
        if trip.status not in [Trip.Status.PUBLISHED, Trip.Status.STARTED]:
            return Response({"detail": "Trajet non terminable."}, status=400)
        
        trip.status = Trip.Status.COMPLETED
        trip.save(update_fields=["status"])
        return Response({"detail": "Trajet terminé.", "status": trip.status})