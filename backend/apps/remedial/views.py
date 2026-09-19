from typing import ClassVar

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsStudent

from . import services
from .models import RemedialSession
from .serializers import (
    RemedialGameQuestionSerializer,
    RemedialSessionSerializer,
    RemedialSubmitSerializer,
)

AI_UNAVAILABLE_DETAIL = "AI hozircha javob bera olmadi. Birozdan so'ng qayta urinib ko'ring."


class RemedialSessionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """A student's own AI-assisted practice sessions — created automatically
    on a low test score (see `apps.learning.views.TestViewSet.submit`), never
    created directly through this API.
    """

    serializer_class = RemedialSessionSerializer
    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return RemedialSession.objects.filter(
            student=self.request.user.student_profile
        ).select_related("subject", "attempt__test")

    @action(detail=True, methods=["post"])
    def explain(self, request, pk=None):
        session = self.get_object()
        explanation = services.generate_explanation(session)
        if explanation is None:
            return Response({"detail": AI_UNAVAILABLE_DETAIL}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(RemedialSessionSerializer(session).data)

    @action(detail=True, methods=["get"])
    def game(self, request, pk=None):
        session = self.get_object()
        if not session.explanation:
            raise ValidationError("Avval mavzu tushuntirilishi kerak.")

        questions = services.generate_game_questions(session)
        if questions is None:
            return Response({"detail": AI_UNAVAILABLE_DETAIL}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(RemedialGameQuestionSerializer(questions, many=True).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        session = self.get_object()
        serializer = RemedialSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = {
            answer["question_index"]: answer["selected_index"]
            for answer in serializer.validated_data["answers"]
        }
        try:
            session = services.submit_game(session=session, answers=answers)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        return Response(RemedialSessionSerializer(session).data)
