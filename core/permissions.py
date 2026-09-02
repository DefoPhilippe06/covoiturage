from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Pour Trip
        if hasattr(obj, "driver"):
            return obj.driver == request.user
        # Pour Vehicle
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        # Pour Booking
        if hasattr(obj, "passenger"):
            return obj.passenger == request.user
        return False