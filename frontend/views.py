from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from trips.models import Trip
from bookings.models import Booking

def home(request):
    trips = Trip.objects.filter(status="PUBLISHED").order_by("departure_datetime")[:12]
    return render(request, "frontend/home.html", {"trips": trips})

def search_trips(request):
    trips = Trip.objects.filter(status="PUBLISHED")
    origin = request.GET.get("origin")
    destination = request.GET.get("destination")
    date = request.GET.get("date")
    if origin:
        trips = trips.filter(origin_city__icontains=origin)
    if destination:
        trips = trips.filter(destination_city__icontains=destination)
    if date:
        trips = trips.filter(departure_datetime__date=date)
    return render(request, "frontend/search.html", {
        "trips": trips,
        "origin": origin or "",
        "destination": destination or "",
        "date": date or "",
    })

def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    return render(request, "frontend/trip_detail.html", {"trip": trip})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(passenger=request.user).select_related("trip")
    return render(request, "frontend/my_bookings.html", {"bookings": bookings})

@login_required
def my_trips(request):
    trips = Trip.objects.filter(driver=request.user)
    return render(request, "frontend/my_trips.html", {"trips": trips})

@login_required
def publish_trip(request):
    return render(request, "frontend/publish.html")

def login_page(request):
    return render(request, "frontend/login.html")

def register_page(request):
    return render(request, "frontend/register.html")

from django.contrib.auth import authenticate, login as django_login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def session_login(request):
    data = json.loads(request.body)
    user = authenticate(username=data.get("username"), password=data.get("password"))
    if user is not None:
        django_login(request, user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False}, status=400)