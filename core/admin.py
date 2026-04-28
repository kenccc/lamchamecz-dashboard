from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ClassRoom, ClassTime, DayOff, Enrollment, Student, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("LCM", {"fields": ("role", "fullname")}),
    )
    list_display = ("username", "fullname", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser")


class ClassTimeInline(admin.TabularInline):
    model = ClassTime
    extra = 1


class DayOffInline(admin.TabularInline):
    model = DayOff
    extra = 1


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ("code", "subject", "teacher", "status", "date_start", "date_end")
    list_filter = ("status", "teacher")
    search_fields = ("code", "subject")
    inlines = [ClassTimeInline, DayOffInline]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "rodne_cislo", "school_class", "contact")
    search_fields = ("name", "rodne_cislo", "contact")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "classroom", "actual_lessons")
    list_filter = ("classroom",)


admin.site.register(ClassTime)
admin.site.register(DayOff)
