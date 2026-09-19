from typing import ClassVar

from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsStudent
from apps.schools.serializers import StudentRosterSerializer
from apps.users.models import StudentProfile

from . import services
from .models import Duel, DuelRating
from .serializers import (
    DuelCreateSerializer,
    DuelListSerializer,
    DuelQuestionSerializer,
    DuelRatingSerializer,
    DuelSubmitSerializer,
)


class DuelViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Duels are a student-to-student feature — director/teacher have no place here."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        profile = self.request.user.student_profile
        return Duel.objects.filter(Q(challenger=profile) | Q(opponent=profile)).select_related(
            "challenger__user", "opponent__user"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return DuelCreateSerializer
        return DuelListSerializer

    def create(self, request, *args, **kwargs):
        serializer = DuelCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        duel = serializer.save()
        return Response(
            DuelListSerializer(duel, context=self.get_serializer_context()).data, status=201
        )

    @action(detail=True, methods=["get"])
    def questions(self, request, pk=None):
        duel = self.get_object()
        duel = services.start_participant(duel=duel, participant=request.user.student_profile)
        queryset = duel.duel_questions.select_related("question").prefetch_related("question__options")
        return Response(DuelQuestionSerializer(queryset, many=True).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        duel = self.get_object()
        serializer = DuelSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            duel = services.submit_duel_answers(
                duel=duel,
                participant=request.user.student_profile,
                answers=serializer.validated_data["answers"],
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        return Response(DuelListSerializer(duel, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"])
    def opponents(self, request):
        """Classmates you're allowed to challenge."""
        profile = request.user.student_profile
        classmates = (
            StudentProfile.objects.filter(school_class_id=profile.school_class_id)
            .exclude(pk=profile.pk)
            .select_related("user")
            .order_by("user__first_name")
        )
        return Response(StudentRosterSerializer(classmates, many=True).data)

    @action(detail=False, methods=["get"])
    def leaderboard(self, request):
        profile = request.user.student_profile
        ratings = (
            DuelRating.objects.filter(student__school_class_id=profile.school_class_id)
            .select_related("student__user")
            .order_by("-rating")
        )
        return Response(DuelRatingSerializer(ratings, many=True).data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        rating = services.get_or_create_rating(request.user.student_profile)
        return Response(DuelRatingSerializer(rating).data)
