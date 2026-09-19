from rest_framework.routers import DefaultRouter

from .views import DuelViewSet

router = DefaultRouter()
router.register("duels", DuelViewSet, basename="duel")

urlpatterns = router.urls
