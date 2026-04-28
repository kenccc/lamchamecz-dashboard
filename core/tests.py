from datetime import date, time
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from .models import ClassRoom, ClassStatus, ClassTime, Enrollment, Role, Student, User, Weekday


class ReviewFixesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin", password="pw", role=Role.ADMIN
        )
        self.teacher_a = User.objects.create_user(
            username="teacher-a", password="pw", role=Role.TEACHER
        )
        self.teacher_b = User.objects.create_user(
            username="teacher-b", password="pw", role=Role.TEACHER
        )

        self.class_a = ClassRoom.objects.create(
            code="A1",
            subject="Math",
            teacher=self.teacher_a,
            total_lessons=12,
            fee_per_lesson=Decimal("100"),
            date_start=date(2026, 1, 1),
            date_end=date(2026, 1, 31),
            status=ClassStatus.ACTIVE,
        )
        self.class_b = ClassRoom.objects.create(
            code="B1",
            subject="Science",
            teacher=self.teacher_b,
            total_lessons=8,
            fee_per_lesson=Decimal("100"),
            date_start=date(2026, 1, 1),
            date_end=date(2026, 1, 31),
            status=ClassStatus.ACTIVE,
        )

        self.student_a = Student.objects.create(name="Student A")
        self.student_b = Student.objects.create(name="Student B")
        self.student_c = Student.objects.create(name="Student C")
        Enrollment.objects.create(
            student=self.student_a, classroom=self.class_a, actual_lessons=5
        )
        Enrollment.objects.create(
            student=self.student_b, classroom=self.class_b, actual_lessons=5
        )
        Enrollment.objects.create(
            student=self.student_c, classroom=self.class_a, actual_lessons=5
        )

    def test_teacher_cannot_edit_unrelated_student(self):
        self.client.force_login(self.teacher_a)

        response = self.client.get(reverse("student_edit", args=[self.student_b.pk]))

        self.assertEqual(response.status_code, 404)

    def test_teacher_cannot_prefill_enrollment_for_unrelated_student(self):
        self.client.force_login(self.teacher_a)

        response = self.client.get(
            reverse("enrollment_create_for_student", args=[self.student_b.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_teacher_enrollment_form_hides_unrelated_students(self):
        self.client.force_login(self.teacher_b)

        response = self.client.get(reverse("enrollment_create"))

        student_field = response.context["form"].fields["student"]
        queryset_ids = set(student_field.queryset.values_list("id", flat=True))
        self.assertIn(self.student_b.id, queryset_ids)
        self.assertNotIn(self.student_a.id, queryset_ids)
        self.assertNotIn(self.student_c.id, queryset_ids)

    def test_admin_revenue_uses_actual_lessons_total_once(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("class_list"))

        row = next(r for r in response.context["rows"] if r["cls"].pk == self.class_a.pk)
        self.assertEqual(row["fee"], 1000.0)

    def test_timetable_excludes_closed_classes(self):
        ClassTime.objects.create(
            classroom=self.class_a,
            weekday=Weekday.MON,
            time_start=time(9, 0),
            time_end=time(10, 0),
        )
        closed_class = ClassRoom.objects.create(
            code="C1",
            subject="Closed",
            teacher=self.teacher_a,
            total_lessons=4,
            fee_per_lesson=Decimal("100"),
            date_start=date(2026, 1, 1),
            date_end=date(2026, 1, 31),
            status=ClassStatus.CLOSED,
        )
        ClassTime.objects.create(
            classroom=closed_class,
            weekday=Weekday.MON,
            time_start=time(11, 0),
            time_end=time(12, 0),
        )

        self.client.force_login(self.teacher_a)
        response = self.client.get(reverse("timetable"))

        monday = next(day for day in response.context["days"] if day[0] == Weekday.MON)
        self.assertEqual([slot["cls"].pk for slot in monday[2]], [self.class_a.pk])
