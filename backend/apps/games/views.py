from typing import ClassVar

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsDirector, IsStudent

from . import question_service, services
from .models import GameSession
from .serializers import (
    GameAnswerCheckSerializer,
    GameQuestionSerializer,
    GameSessionCreateSerializer,
    GameSessionSerializer,
    GameSubmitSerializer,
    PoolImportSerializer,
    PoolPromptSerializer,
    PoolRefillSerializer,
)

POOL_NOT_READY_DETAIL = "Bu fan uchun savollar hali kiritilmagan."
# A machine-readable companion to the message above, so the client can show a
# proper empty state ("no questions for this subject yet") and tell it apart
# from a transport/server failure — without either side guessing.
POOL_NOT_READY_CODE = "no_questions_for_subject"


class GameSessionViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """The self-serve "O'yinlar" section — student-only, any time, not tied to a test."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return (
            GameSession.objects.filter(student=self.request.user.student_profile)
            .select_related("subject")
            .prefetch_related("remedial_sessions")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return GameSessionCreateSerializer
        return GameSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = GameSessionCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        return Response(GameSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def subjects(self, request):
        """Every subject with its current question-bank size, so a client can
        show a real empty state ("no questions for this subject yet") *before*
        a session is started rather than only when its questions are requested.
        """
        return Response(question_service.subject_availability())

    @action(detail=True, methods=["get"])
    def questions(self, request, pk=None):
        session = self.get_object()
        game_questions = services.pick_session_questions(session)
        if game_questions is None:
            # The session's subject has nothing in the bank — an empty state to
            # show, not an error to retry. `code` is what the client keys off.
            return Response(
                {"detail": POOL_NOT_READY_DETAIL, "code": POOL_NOT_READY_CODE, "subject": session.subject_id},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(GameQuestionSerializer(game_questions, many=True).data)

    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        """Live per-question check. Arqon tortish only learns whether the one
        answer was right (`services.check_answer`); Minora qurish and Kodni
        buzish lock the answer in server-side and get the key, explanation and
        running totals back (`services.record_live_answer`).
        """
        session = self.get_object()
        serializer = GameAnswerCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            if session.game_type in services.LIVE_KEY_GAMES:
                return Response(services.record_live_answer(session=session, **serializer.validated_data))
            correct = services.check_answer(
                session=session,
                question_index=serializer.validated_data["question_index"],
                selected_index=serializer.validated_data["selected_index"],
            )
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

        # A low score opens the same AI-tutor flow a low test score does.
        from apps.remedial.services import maybe_start_remedial_for_game

        maybe_start_remedial_for_game(session)
        # Re-read so the response's `remedial_session_id` sees a session just opened
        # (the one from get_object() carries a stale prefetch cache).
        return Response(GameSessionSerializer(self.get_queryset().get(pk=session.pk)).data)


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
        added = services.refill_pool(
            organization=request.user.active_organization, **serializer.validated_data
        )
        return Response({"added": added})

    @action(detail=False, methods=["post"])
    def prompt(self, request):
        """Return the exact generation prompt for a subject (+ optional class),
        so a director can run it in an external chatbot (ChatGPT, Claude, …) and
        paste the result back via `import_questions`. No AI call is made here."""
        serializer = PoolPromptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        kwargs = {"subject": data["subject"]}
        if data.get("school_class") is not None:
            kwargs["school_class"] = data["school_class"]
        if data.get("count") is not None:
            kwargs["batch_size"] = data["count"]
        return Response({"prompt": services.build_refill_prompt(**kwargs)})

    @action(detail=False, methods=["post"], url_path="import")
    def import_questions(self, request):
        """Store questions a director pasted back from an external chatbot. The
        paste is parsed leniently (bare JSON, ```json fences, or prose) and only
        well-formed questions are kept; returns how many were received vs added."""
        serializer = PoolImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        subject = data["subject"]
        school_class = data.get("school_class")
        raw_questions = services.parse_questions_payload(data["content"])
        if not raw_questions:
            raise ValidationError(
                "Matndan savollar topilmadi. Chatbot bergan JSON'ni to'liq nusxalab joylang."
            )
        organization = request.user.active_organization
        added = services.store_pool_questions(
            subject=subject,
            school_class=school_class,
            organization_id=organization.pk if organization else None,
            raw_questions=raw_questions,
        )
        return Response({"received": len(raw_questions), "added": added})
