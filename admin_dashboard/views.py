from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from trips.models import Trip
from bookings.models import Booking
from vehicles.models import Vehicle
from reviews.models import Review
from payments.models import Payment

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)

    context = {
        "total_users": User.objects.count(),
        "total_drivers": User.objects.filter(is_driver=True).count(),
        "total_trips": Trip.objects.count(),
        "published_trips": Trip.objects.filter(status="PUBLISHED").count(),
        "total_bookings": Booking.objects.count(),
        "confirmed_bookings": Booking.objects.filter(status="CONFIRMED").count(),
        "total_vehicles": Vehicle.objects.count(),
        "total_reviews": Review.objects.count(),
        "total_revenue": Payment.objects.filter(status="SUCCESS").aggregate(s=Sum("amount"))["s"] or 0,
        "bookings_last_7_days": Booking.objects.filter(created_at__date__gte=last_7_days).count(),
        "recent_trips": Trip.objects.select_related("driver").order_by("-created_at")[:8],
        "recent_bookings": Booking.objects.select_related("passenger", "trip").order_by("-created_at")[:8],
        "recent_reviews": Review.objects.select_related("reviewer", "reviewed_user", "trip").order_by("-created_at")[:6],
    }
    return render(request, "admin_dashboard/dashboard.html", context)


@login_required
@user_passes_test(is_admin)
def users_list(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "admin_dashboard/users.html", {"users": users})


@login_required
@user_passes_test(is_admin)
def trips_list(request):
    trips = Trip.objects.select_related("driver", "vehicle").order_by("-departure_datetime")
    status = request.GET.get("status")
    if status:
        trips = trips.filter(status=status)
    return render(request, "admin_dashboard/trips.html", {
        "trips": trips,
        "current_status": status or "",
    })


@login_required
@user_passes_test(is_admin)
def bookings_list(request):
    bookings = Booking.objects.select_related("passenger", "trip").order_by("-created_at")
    return render(request, "admin_dashboard/bookings.html", {"bookings": bookings})


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard:dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect("admin_dashboard:dashboard")
            form.add_error(None, "Accès réservé aux administrateurs.")
    else:
        form = AuthenticationForm()

    return render(request, "admin_dashboard/login.html", {"form": form})


def admin_logout(request):
    logout(request)
    return redirect("admin_dashboard:login")


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas vous désactiver vous-même.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        status = "activé" if user.is_active else "désactivé"
        messages.success(request, f"Utilisateur {user.username} {status}.")
    return redirect("admin_dashboard:users")


@login_required
@user_passes_test(is_admin)
@require_POST
def cancel_trip(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    if trip.status in ["COMPLETED", "CANCELLED"]:
        messages.error(request, "Ce trajet ne peut plus être annulé.")
    else:
        trip.status = "CANCELLED"
        trip.save(update_fields=["status"])
        messages.success(request, f"Trajet {trip.origin_city} → {trip.destination_city} annulé.")
    return redirect("admin_dashboard:trips")