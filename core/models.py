from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    ADMIN = "admin", _("Administrator")
    TEACHER = "teacher", _("Teacher")
    ASSISTANT = "asis", _("Assistant")


class Weekday(models.TextChoices):
    MON = "Monday", _("Monday")
    TUE = "Tuesday", _("Tuesday")
    WED = "Wednesday", _("Wednesday")
    THU = "Thursday", _("Thursday")
    FRI = "Friday", _("Friday")
    SAT = "Saturday", _("Saturday")
    SUN = "Sunday", _("Sunday")


WEEKDAY_ORDER = [w.value for w in Weekday]
WEEKDAY_ISO = {w.value: i + 1 for i, w in enumerate(Weekday)}


class User(AbstractUser):
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.TEACHER)
    fullname = models.CharField(max_length=255, blank=True)

    def display_name(self) -> str:
        return self.fullname or self.get_full_name() or self.username

    @property
    def is_app_admin(self) -> bool:
        return self.role == Role.ADMIN or self.is_superuser


class ClassStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    CLOSED = "close", _("Closed")


class ClassRoom(models.Model):
    code = models.CharField(_("Class code"), max_length=64)
    subject = models.CharField(_("Subject"), max_length=128)
    teacher = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="classes_taught",
        verbose_name=_("Teacher"),
    )
    assistant = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="classes_assisted", verbose_name=_("Assistant"),
    )
    total_lessons = models.PositiveIntegerField(_("Number of lessons"), default=0)
    minutes_per_lesson = models.PositiveIntegerField(_("Lesson length (min)"), default=60)
    fee_per_lesson = models.DecimalField(_("Price per lesson (CZK)"), max_digits=10, decimal_places=2, default=0)
    date_start = models.DateField(_("Start date"))
    date_end = models.DateField(_("End date"))
    status = models.CharField(max_length=16, choices=ClassStatus.choices, default=ClassStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} – {self.subject}"

    @property
    def is_closed(self) -> bool:
        return self.status == ClassStatus.CLOSED


class ClassTime(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="times")
    weekday = models.CharField(max_length=10, choices=Weekday.choices)
    time_start = models.TimeField()
    time_end = models.TimeField()

    class Meta:
        ordering = ["weekday", "time_start"]

    def __str__(self) -> str:
        return f"{self.classroom.code} {self.weekday} {self.time_start}-{self.time_end}"


class DayOff(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="days_off")
    date = models.DateField()

    class Meta:
        unique_together = [("classroom", "date")]
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.classroom.code} – {self.date}"


class Student(models.Model):
    rodne_cislo = models.CharField(_("Birth number / VS"), max_length=32, blank=True)
    name = models.CharField(_("Name"), max_length=255)
    birth_year = models.PositiveSmallIntegerField(_("Birth year"), null=True, blank=True)
    school_class = models.CharField(_("Class"), max_length=64, blank=True)
    contact = models.CharField(_("Contact"), max_length=255, blank=True)
    note = models.CharField(_("Note"), max_length=512, blank=True)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="enrollments")
    actual_lessons = models.PositiveIntegerField(_("Actual lessons"), default=0)
    note = models.CharField(_("Note"), max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("student", "classroom")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student} → {self.classroom}"
