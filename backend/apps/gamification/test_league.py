from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.common.testing import default_organization, make_director, make_student

from . import league
from .models import LeagueStanding, WeeklyGoal, XPTransaction


def _noon(day):
    """An aware datetime at local noon on `day` — safely inside that calendar
    date whichever way the timezone conversion rounds."""
    return timezone.make_aware(datetime(day.year, day.month, day.day, 12, 0))  # noqa: DTZ001


def _give_xp(student, amount, when):
    """Grant XP dated to `when`. created_at is auto_now_add, so it is forced with
    a follow-up update() (which bypasses auto fields)."""
    tx = XPTransaction.objects.create(
        student=student, amount=amount, source=XPTransaction.Source.GAME, reason="test"
    )
    XPTransaction.objects.filter(pk=tx.pk).update(created_at=when)
    return tx


class MovementCountsTests(TestCase):
    def test_tier_with_one_student_moves_nobody(self):
        self.assertEqual(league.movement_counts(1, 3), (0, 0))

    def test_small_middle_tier_moves_at_least_one_each_way(self):
        self.assertEqual(league.movement_counts(3, 3), (1, 1))

    def test_bottom_tier_never_relegates(self):
        promote, demote = league.movement_counts(10, league.MIN_TIER)
        self.assertEqual((promote, demote), (2, 0))

    def test_top_tier_never_promotes(self):
        promote, demote = league.movement_counts(10, league.MAX_TIER)
        self.assertEqual((promote, demote), (0, 2))

    def test_zones_never_overlap_in_a_tiny_tier(self):
        promote, demote = league.movement_counts(2, 3)
        self.assertLessEqual(promote + demote, 2)


class LeagueBoardTests(TestCase):
    def setUp(self):
        self.org = default_organization()
        self.monday = league.week_start()

    def test_new_student_starts_in_the_bottom_tier(self):
        user, profile = make_student()
        data = league.board(user)
        self.assertEqual(data["my_tier"], league.MIN_TIER)
        self.assertTrue(
            LeagueStanding.objects.filter(student=profile, tier=league.MIN_TIER).exists()
        )
        self.assertEqual(len(data["tiers"]), 9)

    def test_members_are_ranked_by_this_weeks_xp(self):
        user_low, profile_low = make_student()
        _user_high, profile_high = make_student()
        league.ensure_standings(self.org.id)
        _give_xp(profile_low, 100, _noon(self.monday))
        _give_xp(profile_high, 300, _noon(self.monday))

        data = league.board(user_low)
        self.assertEqual(data["members"][0]["weekly_xp"], 300)
        self.assertEqual(data["members"][1]["weekly_xp"], 100)
        me = next(member for member in data["members"] if member["is_me"])
        self.assertEqual(me["rank"], 2)

    def test_last_weeks_xp_does_not_count_toward_this_week(self):
        user, profile = make_student()
        league.ensure_standings(self.org.id)
        _give_xp(profile, 999, _noon(self.monday - timedelta(days=3)))
        data = league.board(user)
        me = next(member for member in data["members"] if member["is_me"])
        self.assertEqual(me["weekly_xp"], 0)


class WeeklyRollupTests(TestCase):
    def setUp(self):
        self.org = default_organization()
        self.this_monday = league.week_start()
        self.ended_week = self.this_monday - timedelta(days=7)

    def _run(self):
        return league.run_weekly_update(self.org.id, today=self.this_monday)

    def test_top_is_promoted_and_bottom_relegated(self):
        students = [make_student() for _ in range(5)]
        league.ensure_standings(self.org.id)
        LeagueStanding.objects.filter(organization=self.org).update(tier=3)
        for (_user, profile), amount in zip(students, [500, 400, 300, 200, 100]):
            _give_xp(profile, amount, _noon(self.ended_week))

        result = self._run()

        self.assertFalse(result["skipped"])
        self.assertEqual(result["moved"], 2)
        self.assertEqual(LeagueStanding.objects.get(student=students[0][1]).tier, 4)
        self.assertEqual(LeagueStanding.objects.get(student=students[4][1]).tier, 2)
        self.assertEqual(LeagueStanding.objects.get(student=students[2][1]).tier, 3)

    def test_rollup_is_idempotent(self):
        make_student()
        league.ensure_standings(self.org.id)
        first = self._run()
        second = self._run()
        self.assertFalse(first["skipped"])
        self.assertTrue(second["skipped"])


class WeeklyGoalTests(TestCase):
    def setUp(self):
        self.org = default_organization()
        self.this_monday = league.week_start()
        self.ended_week = self.this_monday - timedelta(days=7)

    def test_streak_increments_when_goal_met(self):
        user, profile = make_student()
        league.set_weekly_goal(user, 200)
        _give_xp(profile, 250, _noon(self.ended_week))

        league.run_weekly_update(self.org.id, today=self.this_monday)

        goal = WeeklyGoal.objects.get(student=profile)
        self.assertEqual(goal.goal_streak, 1)
        self.assertEqual(goal.best_goal_streak, 1)
        self.assertEqual(goal.last_completed_week, self.ended_week)

    def test_streak_resets_but_best_is_kept_when_goal_missed(self):
        user, profile = make_student()
        goal = league.set_weekly_goal(user, 500)
        WeeklyGoal.objects.filter(pk=goal.pk).update(goal_streak=3, best_goal_streak=3)
        _give_xp(profile, 100, _noon(self.ended_week))

        league.run_weekly_update(self.org.id, today=self.this_monday)

        goal.refresh_from_db()
        self.assertEqual(goal.goal_streak, 0)
        self.assertEqual(goal.best_goal_streak, 3)

    def test_status_reports_current_week_progress(self):
        user, profile = make_student()
        league.set_weekly_goal(user, 300)
        _give_xp(profile, 120, _noon(self.this_monday))

        status = league.weekly_goal_status(user)

        self.assertEqual(status["earned_xp"], 120)
        self.assertEqual(status["target_xp"], 300)
        self.assertFalse(status["met"])


class LeagueEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        default_organization()

    def test_student_can_read_the_league(self):
        user, _profile = make_student()
        self.client.force_authenticate(user)
        response = self.client.get("/api/league/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("members", response.data)
        self.assertEqual(len(response.data["tiers"]), 9)

    def test_student_sets_their_weekly_goal(self):
        user, _profile = make_student()
        self.client.force_authenticate(user)
        response = self.client.patch("/api/weekly-goal/", {"target_xp": 750}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["target_xp"], 750)

    def test_weekly_goal_rejects_an_absurd_target(self):
        user, _profile = make_student()
        self.client.force_authenticate(user)
        response = self.client.patch("/api/weekly-goal/", {"target_xp": 0}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_non_student_cannot_read_the_league(self):
        director = make_director()
        self.client.force_authenticate(director)
        response = self.client.get("/api/league/")
        self.assertEqual(response.status_code, 403)
