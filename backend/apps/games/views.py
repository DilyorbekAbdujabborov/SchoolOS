from typing import ClassVar

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsDirector, IsStudent

from . import services
from .models import GameSession
from .serializers import (
    GameAnswerCheckSerializer,
    GameQuestionSerializer,
    GameSessionCreateSerializer,
    GameSessionSerializer,
    GameSubmitSerializer,
    PoolRefillSerializer,
)

POOL_NOT_READY_DETAIL = "Bu fan va sinf uchun savollar hali tayyorlanmagan. Birozdan so'ng qayta urinib ko'ring."


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
        game_questions = services.pick_session_questions(session)
        if game_questions is None:
            return Response({"detail": POOL_NOT_READY_DETAIL}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(GameQuestionSerializer(game_questions, many=True).data)

    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        """Live per-question check for the tug-of-war rope — see `services.check_answer`."""
        session = self.get_object()
        serializer = GameAnswerCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            correct = services.check_answer(session=session, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        return Response({"correct": correct})

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


class QuestionPoolViewSet(viewsets.ViewSet):
    """Director-only: see and top up each subject+class question pool that
    powers the self-serve games — see `apps.games.services.refill_pool`. A
    game's live start never calls Gemini; only this (and the scheduled
    `apps.games.tasks.refill_low_pools`) does.
    """

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated, IsDirector]

    def list(self, request):
        return Response(services.pool_status())

    @action(detail=False, methods=["post"])
    def refill(self, request):
        serializer = PoolRefillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        added = services.refill_pool(**serializer.validated_data)
        return Response({"added": added})
