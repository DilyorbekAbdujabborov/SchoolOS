from typing import ClassVar

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsStudent

from . import services
from .models import GameSession
from .serializers import (
    GameQuestionSerializer,
    GameSessionCreateSerializer,
    GameSessionSerializer,
    GameSubmitSerializer,
)

AI_UNAVAILABLE_DETAIL = "AI hozircha javob bera olmadi. Birozdan so'ng qayta urinib ko'ring."


class GameSessionViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """The self-serve "O'yinlar" section — student-only, any time, not tied to a test."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return GameSession.objects.filter(student=self.request.user.student_profile).select_related("subject")

    def get_serializer_class(self):
        if self.action == "create":
            return GameSessionCreateSerializer
        return GameSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = GameSessionCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        return Response(GameSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def questions(self, request, pk=None):
        session = self.get_object()
        game_questions = services.generate_questions(session)
        if game_questions is None:
            return Response({"detail": AI_UNAVAILABLE_DETAIL}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(GameQuestionSerializer(game_questions, many=True).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        session = self.get_object()
        serializer = GameSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = {
            answer["question_index"]: answer["selected_index"]
            for answer in serializer.validated_data["answers"]
        }
        try:
            session = services.submit_game(session=session, answers=answers)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        return Response(GameSessionSerializer(session).data)
