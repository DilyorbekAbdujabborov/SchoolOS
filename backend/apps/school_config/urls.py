from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClassAccessView, SchoolDayExceptionViewSet, SchoolTimeSettingsView

router = DefaultRouter()
router.register("school-day-exceptions", SchoolDayExceptionViewSet, basename="school-day-exception")

urlpatterns = [
    path("school-config/", SchoolTimeSettingsView.as_view(), name="school-config"),
    path("class-access/", ClassAccessView.as_view(), name="class-access"),
    path("", include(router.urls)),
]
