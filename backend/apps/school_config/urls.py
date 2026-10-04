from django.urls import path

from .views import ClassAccessView, SchoolTimeSettingsView

urlpatterns = [
    path("school-config/", SchoolTimeSettingsView.as_view(), name="school-config"),
    path("class-access/", ClassAccessView.as_view(), name="class-access"),
]
