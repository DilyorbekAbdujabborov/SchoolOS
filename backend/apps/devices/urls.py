from django.urls import path

from .views import EventsView, HeartbeatView

urlpatterns = [
    path("devices/events/", EventsView.as_view(), name="device-events"),
    path("devices/heartbeat/", HeartbeatView.as_view(), name="device-heartbeat"),
]
