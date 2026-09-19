from rest_framework.routers import DefaultRouter

from .views import RemedialSessionViewSet

router = DefaultRouter()
router.register("remedial-sessions", RemedialSessionViewSet, basename="remedial-session")

urlpatterns = router.urls
