from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from trips.models import Trip
from bookings.models import Booking
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField, Q
from urllib.parse import unquote


def _active_trips():
    """Trajets publiés, encore dans le futur, avec places."""
    return Trip.objects.filter(
        status="PUBLISHED",
        departure_datetime__gte=timezone.now(),
        seats_available__gt=0,
    )

# Alias / abréviations → nom canonique pour le matching
CITY_ALIASES = {
    # Douala
    "douala": "Douala",
    "dla": "Douala",
    "dla.": "Douala",
    # Yaoundé
    "yaounde": "Yaoundé",
    "yaoundé": "Yaoundé",
    "yde": "Yaoundé",
    "yde.": "Yaoundé",
    # Bafoussam
    "bafoussam": "Bafoussam",
    "baf": "Bafoussam",
    "baf.": "Bafoussam",
    "bafoussam ii": "Bafoussam",
    "bafoussam i": "Bafoussam",
    # Autres villes fréquentes
    "bamenda": "Bamenda",
    "bda": "Bamenda",
    "garoua": "Garoua",
    "maroua": "Maroua",
    "ngaoundere": "Ngaoundéré",
    "ngaoundéré": "Ngaoundéré",
    "kribi": "Kribi",
    "limbe": "Limbé",
    "limbé": "Limbé",
    "buea": "Buea",
    "ebolowa": "Ebolowa",
    "bertoua": "Bertoua",
    "kumba": "Kumba",
    "dschang": "Dschang",
}


def normalize_city(name: str) -> str:
    """Retourne une clé de matching (ex. Bafoussam II → Bafoussam)."""
    if not name:
        return ""
    raw = name.strip().lower()
    # enlever accents simples pour la clé alias
    import unicodedata
    flat = "".join(
        c for c in unicodedata.normalize("NFD", raw)
        if unicodedata.category(c) != "Mn"
    )
    if flat in CITY_ALIASES:
        return CITY_ALIASES[flat]
    if raw in CITY_ALIASES:
        return CITY_ALIASES[raw]
    # premier mot : "Bafoussam II" → "Bafoussam"
    first = raw.split(",")[0].strip().split()[0] if raw else ""
    if first in CITY_ALIASES:
        return CITY_ALIASES[first]
    return name.split(",")[0].strip().split()[0] if name else ""

def home(request):
    user_city = unquote(request.COOKIES.get("user_city") or "").strip()
    if "%20" in user_city:
        user_city = unquote(user_city).strip()

    if not user_city and request.user.is_authenticated:
        user_city = (getattr(request.user, "home_city", None) or "").strip()

    qs = _active_trips().select_related("driver", "vehicle")

    if user_city:
        city_key = normalize_city(user_city)  # ex. "Bafoussam II" → "Bafoussam"

        local = list(
            qs.filter(origin_city__icontains=city_key)
            .order_by("departure_datetime")[:12]
        )
        if len(local) < 12:
            ids = [t.id for t in local]
            others = list(
                qs.exclude(id__in=ids)
                .order_by("departure_datetime")[: 12 - len(local)]
            )
            trips = local + others
        else:
            trips = local
    else:
        trips = list(qs.order_by("departure_datetime")[:12])

    return render(request, "frontend/home.html", {
        "trips": trips,
        "user_city": user_city,  # nom complet affiché (ex. Bafoussam II)
    })


def search_trips(request):
    trips_qs = _active_trips().select_related("driver", "vehicle")
    origin = (request.GET.get("origin") or "").strip()
    destination = (request.GET.get("destination") or "").strip()
    date = request.GET.get("date")

    user_city = unquote(request.COOKIES.get("user_city") or "").strip()
    if "%20" in user_city:
        user_city = unquote(user_city).strip()
    if not user_city and request.user.is_authenticated:
        user_city = (getattr(request.user, "home_city", None) or "").strip()

    if origin:
        trips_qs = trips_qs.filter(origin_city__icontains=normalize_city(origin) or origin)
    if destination:
        trips_qs = trips_qs.filter(destination_city__icontains=destination)
    if date:
        trips_qs = trips_qs.filter(departure_datetime__date=date)

    # Sans origin saisi → priorité ville utilisateur
    if not origin and user_city:
        city_key = normalize_city(user_city)
        local = list(
            trips_qs.filter(origin_city__icontains=city_key)
            .order_by("departure_datetime")[:50]
        )
        ids = [t.id for t in local]
        others = list(
            trips_qs.exclude(id__in=ids)
            .order_by("departure_datetime")[:50]
        )
        trips = local + others
    else:
        trips = trips_qs.order_by("departure_datetime")

    return render(request, "frontend/search.html", {
        "trips": trips,
        "origin": origin or user_city or "",
        "destination": destination or "",
        "date": date or "",
        "user_city": user_city,
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

@login_required
def my_vehicles(request):
    return render(request, "frontend/my_vehicles.html")

@login_required
def messages_page(request):
    return render(request, "frontend/messages.html")