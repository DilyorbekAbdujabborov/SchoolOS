from rest_framework.routers import DefaultRouter

from .views import TeacherTaskAssignmentViewSet, TeacherTaskViewSet

router = DefaultRouter()
router.register("teacher-tasks", TeacherTaskViewSet, basename="teacher-task")
router.register("my-tasks", TeacherTaskAssignmentViewSet, basename="my-task")

urlpatterns = router.urls
