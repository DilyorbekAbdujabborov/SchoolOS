from django.contrib import admin

from .models import TeacherTask, TeacherTaskAssignment


class TeacherTaskAssignmentInline(admin.TabularInline):
    model = TeacherTaskAssignment
    extra = 0
    readonly_fields = ("teacher", "is_done", "completed_at")


@admin.register(TeacherTask)
class TeacherTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_by", "is_broadcast", "created_at")
    list_filter = ("category", "is_broadcast")
    search_fields = ("title", "description")
    inlines = (TeacherTaskAssignmentInline,)


@admin.register(TeacherTaskAssignment)
class TeacherTaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("task", "teacher", "is_done", "completed_at", "created_at")
    list_filter = ("is_done",)
    search_fields = ("task__title", "teacher__user__email")
