from django.urls import path
from . import views

app_name = "admin_dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users_list, name="users"),
    path("trips/", views.trips_list, name="trips"),
    path("bookings/", views.bookings_list, name="bookings"),
    path("login/", views.admin_login, name="login"),
    path("logout/", views.admin_logout, name="logout"),
    path("users/<int:user_id>/toggle-active/", views.toggle_user_active, name="toggle_user_active"),
    path("trips/<int:trip_id>/cancel/", views.cancel_trip, name="cancel_trip"),
    path("trips/<int:trip_id>/track/", views.trip_track, name="trip_track"),
    path("trips/<int:trip_id>/location/", views.trip_location_json, name="trip_location_json"),
]