from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search_trips, name="search"),
    path("trip/<int:pk>/", views.trip_detail, name="trip_detail"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("my-trips/", views.my_trips, name="my_trips"),
    path("publish/", views.publish_trip, name="publish"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("api/session-login/", views.session_login, name="session_login"),
]