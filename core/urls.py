from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("timetable/", views.timetable, name="timetable"),
    path("statistics/", views.statistics, name="statistics"),

    path("classes/", views.class_list, name="class_list"),
    path("classes/new/", views.class_create, name="class_create"),
    path("classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("classes/<int:pk>/times/", views.class_times, name="class_times"),
    path("classes/<int:pk>/close/", views.class_close, name="class_close"),
    path("classes/<int:pk>/calendar/", views.class_calendar, name="class_calendar"),
    path("classes/<int:pk>/calendar/download/", views.calendar_download, name="calendar_download"),
    path("calendar/", views.calendar_pick, name="calendar_pick"),
    path("dayoff/<int:pk>/remove/", views.dayoff_remove, name="dayoff_remove"),

    path("students/", views.student_list, name="student_list"),
    path("students/new/", views.student_create, name="student_create"),
    path("students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),

    path("enrollments/", views.enrollment_list, name="enrollment_list"),
    path("enrollments/new/", views.enrollment_create, name="enrollment_create"),
    path(
        "enrollments/new/student/<int:pk>/",
        views.enrollment_create,
        name="enrollment_create_for_student",
    ),
    path("enrollments/<int:pk>/delete/", views.enrollment_delete, name="enrollment_delete"),

    path("users/new/", views.user_create, name="user_create"),

    path("autocomplete/class/", views.autocomplete_class, name="autocomplete_class"),
]
