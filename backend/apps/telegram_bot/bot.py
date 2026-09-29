"""Telegram bot handlers — the single source of truth for how updates are handled.

Two delivery modes share this module, so routing and handlers can never drift:

- `management/commands/runbot.py` — long polling, for local dev where the machine
  has no public HTTPS URL.
- `views.TelegramWebhookView` — production, where Telegram POSTs every update to
  our endpoint and the `WebhookBotRunner` below feeds it to the same `Application`.

Handlers only ever see a `context` for `/start`'s code argument, so the webhook
path and the polling path behave identically.
"""

import asyncio
import logging
import threading

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Q, Sum
from django.utils import timezone
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from apps.academics.models import Lesson
from apps.attendance.models import Attendance
from apps.attendance.services import count_by_status
from apps.gamification.models import Streak, StudentAchievement, XPTransaction
from apps.learning.models import Test, TestAttempt
from apps.schools.models import SchoolClass
from apps.telegram_bot.models import TelegramAccount, TelegramLinkCode
from apps.users.models import StudentProfile, TeacherProfile

logger = logging.getLogger(__name__)

# count_by_status runs a synchronous ORM query — bot handlers are async, so it
# must go through sync_to_async instead of being awaited/called directly.
acount_by_status = sync_to_async(count_by_status, thread_sensitive=True)

LESSONS_BUTTON = "📅 Bugungi darslar"
ATTENDANCE_BUTTON = "📊 Davomatim"
CLASSES_BUTTON = "🏫 Mening sinflarim"
STATS_BUTTON = "📊 Umumiy statistika"
TESTS_BUTTON = "🧪 Mavjud testlar"
XP_BUTTON = "🏆 Mening XP'im"
ACHIEVEMENTS_BUTTON = "🎖 Yutuqlarim"
CLASS_XP_BUTTON = "📈 Sinflar XP statistikasi"

STUDENT_MENU = ReplyKeyboardMarkup(
    [
        [LESSONS_BUTTON, ATTENDANCE_BUTTON],
        [TESTS_BUTTON, XP_BUTTON],
        [ACHIEVEMENTS_BUTTON],
    ],
    resize_keyboard=True,
)
TEACHER_MENU = ReplyKeyboardMarkup(
    [[LESSONS_BUTTON, CLASSES_BUTTON], [CLASS_XP_BUTTON]], resize_keyboard=True
)
DIRECTOR_MENU = ReplyKeyboardMarkup([[STATS_BUTTON]], resize_keyboard=True)


def menu_for(user) -> ReplyKeyboardMarkup:
    if user.is_director:
        return DIRECTOR_MENU
    if user.is_teacher:
        return TEACHER_MENU
    return STUDENT_MENU


async def get_linked_user(telegram_id: int):
    account = (
        await TelegramAccount.objects.select_related("user")
        .filter(telegram_id=telegram_id)
        .afirst()
    )
    return account.user if account else None


async def today_lessons_text(user) -> str:
    today = timezone.localdate()

    if user.is_student:
        profile = await StudentProfile.objects.select_related("school_class").aget(user=user)
        if not profile.school_class_id:
            return "Siz hali biror sinfga biriktirilmagansiz."
        queryset = Lesson.objects.filter(school_class_id=profile.school_class_id, date=today)
    elif user.is_teacher:
        profile = await TeacherProfile.objects.aget(user=user)
        queryset = Lesson.objects.filter(
            Q(teacher=profile) | Q(school_class__class_teacher=profile), date=today
        ).distinct()
    else:
        return "Bu buyruq faqat o'quvchi va o'qituvchilar uchun."

    lessons = [
        lesson
        async for lesson in queryset.select_related("subject", "school_class").order_by(
            "start_time"
        )
    ]
    if not lessons:
        return f"📅 Bugun ({today:%d.%m.%Y}) darslar yo'q."

    lines = [f"📅 Bugungi darslar ({today:%d.%m.%Y}):", ""]
    for lesson in lessons:
        room = f" · {lesson.room}" if lesson.room else ""
        lines.append(
            f"{lesson.start_time:%H:%M}–{lesson.end_time:%H:%M} "
            f"{lesson.subject.name} ({lesson.school_class.name}){room}"
        )
    return "\n".join(lines)


async def attendance_summary_text(user) -> str:
    profile = await StudentProfile.objects.aget(user=user)
    counts = await acount_by_status(Attendance.objects.filter(student=profile))
    return (
        "📊 Umumiy davomatingiz:\n\n"
        f"✅ Keldi: {counts[Attendance.Status.PRESENT]}\n"
        f"🕐 Kechikdi: {counts[Attendance.Status.LATE]}\n"
        f"❌ Kelmadi: {counts[Attendance.Status.ABSENT]}\n"
        f"📄 Sababli: {counts[Attendance.Status.EXCUSED]}"
    )


async def my_classes_text(user) -> str:
    profile = await TeacherProfile.objects.aget(user=user)
    classes = [
        cls
        async for cls in SchoolClass.objects.filter(
            Q(class_teacher=profile) | Q(lessons__teacher=profile)
        ).distinct()
    ]
    if not classes:
        return "Sizga hali sinf biriktirilmagan."

    lines = ["🏫 Mening sinflarim:", ""]
    for cls in classes:
        suffix = " (sinf rahbari)" if cls.class_teacher_id == profile.id else ""
        lines.append(f"• {cls.name}{suffix}")
    return "\n".join(lines)


async def director_stats_text() -> str:
    today = timezone.localdate()
    counts = await acount_by_status(Attendance.objects.filter(lesson__date=today))
    xp_today = await XPTransaction.objects.filter(created_at__date=today).aaggregate(total=Sum("amount"))
    top_class = await SchoolClass.objects.order_by("-total_xp").afirst()

    lines = [
        "📊 Umumiy statistika:",
        "",
        f"👨‍🎓 Jami o'quvchilar: {await StudentProfile.objects.acount()}",
        f"👩‍🏫 Jami o'qituvchilar: {await TeacherProfile.objects.acount()}",
        f"🏫 Jami sinflar: {await SchoolClass.objects.acount()}",
        f"📅 Bugungi darslar: {await Lesson.objects.filter(date=today).acount()}",
        "",
        "Bugungi davomat:",
        f"✅ Keldi: {counts[Attendance.Status.PRESENT]}",
        f"🕐 Kechikdi: {counts[Attendance.Status.LATE]}",
        f"❌ Kelmadi: {counts[Attendance.Status.ABSENT]}",
        "",
        f"⭐ Bugun berilgan XP: {xp_today['total'] or 0}",
    ]
    if top_class:
        lines.append(f"🥇 Yetakchi sinf: {top_class.name} ({top_class.total_xp} XP)")
    return "\n".join(lines)


async def available_tests_text(user) -> str:
    profile = await StudentProfile.objects.select_related("school_class").aget(user=user)
    if not profile.school_class_id:
        return "Siz hali biror sinfga biriktirilmagansiz."

    taken_test_ids = {
        test_id
        async for test_id in TestAttempt.objects.filter(student=profile).values_list("test_id", flat=True)
    }
    queryset = (
        Test.objects.filter(is_published=True, school_class_id=profile.school_class_id)
        .exclude(id__in=taken_test_ids)
        .select_related("subject")
        .order_by("-created_at")[:10]
    )
    tests = [test async for test in queryset]
    if not tests:
        return "🧪 Hozircha yangi test yo'q."

    lines = ["🧪 Mavjud testlar:", ""]
    for test in tests:
        lines.append(f"• {test.subject.name}: {test.title} (max {test.max_xp} XP)")
    lines.append("\nTestni topshirish uchun veb-saytga kiring.")
    return "\n".join(lines)


async def my_xp_text(user) -> str:
    profile = await StudentProfile.objects.aget(user=user)
    streak, _created = await Streak.objects.aget_or_create(student=profile)
    return (
        "🏆 Mening XP'im:\n\n"
        f"⭐ Jami XP: {profile.total_xp}\n"
        f"🔥 Joriy seriya: {streak.current_streak} kun\n"
        f"🏅 Eng uzun seriya: {streak.longest_streak} kun"
    )


async def my_achievements_text(user) -> str:
    profile = await StudentProfile.objects.aget(user=user)
    unlocked = [
        student_achievement
        async for student_achievement in StudentAchievement.objects.select_related("achievement")
        .filter(student=profile)
        .order_by("-unlocked_at")
    ]
    if not unlocked:
        return "🎖 Hali birorta yutuq ochilmagan. Test va topshiriqlarni bajarib, birinchi yutuqingizni oching!"

    lines = ["🎖 Yutuqlarim:", ""]
    for student_achievement in unlocked:
        achievement = student_achievement.achievement
        lines.append(f"{achievement.icon} {achievement.name} — {achievement.description}")
    return "\n".join(lines)


async def class_xp_text(user) -> str:
    profile = await TeacherProfile.objects.aget(user=user)
    classes = [
        cls
        async for cls in SchoolClass.objects.filter(
            Q(class_teacher=profile) | Q(lessons__teacher=profile)
        ).distinct()
    ]
    if not classes:
        return "Sizga hali sinf biriktirilmagan."

    lines = ["📈 Sinflar XP statistikasi:", ""]
    for cls in sorted(classes, key=lambda school_class: -school_class.total_xp):
        lines.append(f"• {cls.name}: {cls.total_xp} XP")
    return "\n".join(lines)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_chat.id

    if context.args:
        code = context.args[0]
        link_code = await TelegramLinkCode.objects.select_related("user").filter(code=code).afirst()
        if link_code is None or not link_code.is_valid():
            await update.message.reply_text("❌ Kod noto'g'ri yoki muddati o'tgan.")
            return

        await TelegramAccount.objects.filter(telegram_id=telegram_id).adelete()
        await TelegramAccount.objects.aupdate_or_create(
            user=link_code.user,
            defaults={
                "telegram_id": telegram_id,
                "telegram_username": update.effective_user.username or "",
            },
        )
        link_code.used_at = timezone.now()
        await link_code.asave(update_fields=["used_at"])

        name = link_code.user.get_full_name() or link_code.user.username
        await update.message.reply_text(
            f"✅ Hisobingiz bog'landi: {name}", reply_markup=menu_for(link_code.user)
        )
        return

    user = await get_linked_user(telegram_id)
    if user:
        name = user.get_full_name() or user.username
        await update.message.reply_text(f"Salom, {name}! 👋", reply_markup=menu_for(user))
    else:
        await update.message.reply_text(
            "👋 SchoolOS botiga xush kelibsiz!\n\n"
            "Hisobingizni bog'lash uchun avval veb-saytda profilingizdan kod oling, "
            "so'ng shu yerga /start <kod> deb yuboring."
        )


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_chat.id
    user = await get_linked_user(telegram_id)
    if user is None:
        await update.message.reply_text("Avval hisobingizni bog'lang: /start <kod>")
        return

    text = update.message.text
    if text == LESSONS_BUTTON:
        reply = await today_lessons_text(user)
    elif text == ATTENDANCE_BUTTON:
        reply = await attendance_summary_text(user)
    elif text == CLASSES_BUTTON:
        reply = await my_classes_text(user)
    elif text == STATS_BUTTON:
        reply = await director_stats_text()
    elif text == TESTS_BUTTON:
        reply = await available_tests_text(user)
    elif text == XP_BUTTON:
        reply = await my_xp_text(user)
    elif text == ACHIEVEMENTS_BUTTON:
        reply = await my_achievements_text(user)
    elif text == CLASS_XP_BUTTON:
        reply = await class_xp_text(user)
    else:
        reply = "Iltimos, quyidagi menyudan tanlang."

    await update.message.reply_text(reply, reply_markup=menu_for(user))


def build_application(token: str | None = None) -> Application:
    """An `Application` with every handler registered. Built but not started."""
    application = Application.builder().token(token or settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    return application


_STARTUP_TIMEOUT_SECONDS = 20


class WebhookBotRunner:
    """Owns one bot `Application` running on a private event loop in a daemon thread.

    The webhook view can't just call `asyncio.run(application.process_update(...))`
    per request, for two reasons:

    1. An `Application` holds asyncio primitives (its lock, the HTTPX client) that
       bind to the loop that first uses them, so handing it to a second
       `asyncio.run()` raises "bound to a different event loop".
    2. The handler replies back to Telegram over HTTP. Blocking the gunicorn
       worker on that risks a slow response, and Telegram retries slow endpoints —
       which would re-deliver the same update. So updates are queued onto the
       loop and the request is acknowledged immediately.

    One runner per process: with several gunicorn workers each owns its own
    `Application`, which is harmless because updates only ever arrive by webhook
    (nothing polls `getUpdates` in production).
    """

    def __init__(self) -> None:
        self._application: Application | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._failure: BaseException | None = None
        self._start_lock = threading.Lock()

    def _serve(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            self._application = build_application()
            # initialize() resolves the bot identity, so a bad token fails here
            # rather than silently on the first update.
            loop.run_until_complete(self._application.initialize())
        except BaseException as exc:  # re-raised in start() on the request thread
            self._failure = exc
            self._ready.set()
            return
        self._ready.set()
        loop.run_forever()

    def start(self) -> None:
        with self._start_lock:
            # A failed start is sticky: a missing token or a Telegram outage won't
            # heal itself, and retrying per request would just pile up failures.
            if self._failure is not None:
                raise self._failure
            if self._thread is not None:
                return

            self._thread = threading.Thread(
                target=self._serve, name="telegram-bot", daemon=True
            )
            self._thread.start()

            if not self._ready.wait(timeout=_STARTUP_TIMEOUT_SECONDS):
                raise RuntimeError(
                    f"Telegram bot did not start within {_STARTUP_TIMEOUT_SECONDS}s."
                )
            if self._failure is not None:
                raise self._failure

    def enqueue(self, update_data: dict) -> None:
        """Hand a raw Telegram update to the bot loop and return immediately."""
        self.start()
        update = Update.de_json(update_data, self._application.bot)
        future = asyncio.run_coroutine_threadsafe(
            self._application.process_update(update), self._loop
        )
        future.add_done_callback(self._log_failure)

    @staticmethod
    def _log_failure(future) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("Telegram update handling failed")


_webhook_bot = WebhookBotRunner()


def enqueue_update(update_data: dict) -> None:
    """Entry point for `views.TelegramWebhookView`. Raises if the bot can't start."""
    _webhook_bot.enqueue(update_data)
