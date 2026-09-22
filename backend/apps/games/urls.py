from rest_framework.routers import DefaultRouter

from .views import GameSessionViewSet, QuestionPoolViewSet

router = DefaultRouter()
router.register("games", GameSessionViewSet, basename="game-session")
router.register("question-pools", QuestionPoolViewSet, basename="question-pool")

urlpatterns = router.urls
