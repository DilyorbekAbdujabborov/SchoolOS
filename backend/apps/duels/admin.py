from django.contrib import admin

from .models import Duel, DuelAnswer, DuelQuestion, DuelRating


class DuelQuestionInline(admin.TabularInline):
    model = DuelQuestion
    extra = 0
    readonly_fields = ("question", "order")


@admin.register(Duel)
class DuelAdmin(admin.ModelAdmin):
    list_display = ("challenger", "opponent", "school_class", "status", "result", "created_at")
    list_filter = ("status", "result", "school_class")
    search_fields = ("challenger__user__email", "opponent__user__email")
    inlines = (DuelQuestionInline,)


@admin.register(DuelAnswer)
class DuelAnswerAdmin(admin.ModelAdmin):
    list_display = ("duel", "participant", "question", "is_correct")
    list_filter = ("is_correct",)


@admin.register(DuelRating)
class DuelRatingAdmin(admin.ModelAdmin):
    list_display = ("student", "rating", "wins", "losses", "draws")
    search_fields = ("student__user__email",)
    ordering = ("-rating",)
