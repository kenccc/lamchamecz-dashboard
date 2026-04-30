import io
import math
from collections import OrderedDict
from datetime import date as date_type
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from PIL import Image, ImageDraw, ImageFont

from .forms import (
    ClassRoomForm,
    ClassTimeFormSet,
    DayOffForm,
    EnrollmentForm,
    StudentForm,
    UserForm,
)
from .models import (
    ClassRoom,
    ClassStatus,
    ClassTime,
    DayOff,
    Enrollment,
    Role,
    Student,
    User,
    WEEKDAY_ORDER,
    Weekday,
)
from .services import working_days, working_days_by_month


_FONT_PATHS = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
}


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS["bold" if bold else "regular"]:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _fmt_czk(val: Decimal) -> str:
    n = int(val) if val == val.to_integral_value() else val
    return f"{n:,}".replace(",", " ")


def _build_calendar_image(
    cls, months, session_count: int, total_fee: Decimal,
    label_price: str, label_lessons: str,
) -> Image.Image:
    COLS = 3
    IMG_W = 960
    MARGIN = 40
    GAP = 14
    MONTH_HDR_H = 34
    DATE_LINE_H = 22
    CELL_PAD = 10
    TITLE_H = 88
    PRICE_BOX_H = 72

    font_title = _load_font(24, bold=True)
    font_sub = _load_font(13)
    font_month = _load_font(14, bold=True)
    font_date = _load_font(13)
    font_formula = _load_font(20, bold=True)
    font_formula_label = _load_font(12)

    max_dates = max((len(d) for _, d in months), default=0)
    card_h = MONTH_HDR_H + CELL_PAD + max_dates * DATE_LINE_H + CELL_PAD
    col_w = (IMG_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
    n_rows = math.ceil(len(months) / COLS) if months else 1

    img_h = MARGIN + TITLE_H + n_rows * card_h + (n_rows - 1) * GAP + GAP + PRICE_BOX_H + MARGIN

    BG = (246, 248, 252)
    CARD_BG = (255, 255, 255)
    CARD_BORDER = (203, 213, 225)
    HDR_BG = (29, 78, 216)
    HDR_FG = (255, 255, 255)
    DATE_FG = (30, 41, 59)
    TITLE_FG = (15, 23, 42)
    SUB_FG = (100, 116, 139)
    PRICE_BG = (239, 246, 255)
    PRICE_BORDER = (147, 197, 253)
    PRICE_FG = (29, 78, 216)
    PRICE_LABEL_FG = (71, 85, 105)

    img = Image.new("RGB", (IMG_W, img_h), BG)
    draw = ImageDraw.Draw(img)

    draw.text((MARGIN, MARGIN), f"{cls.code} – {cls.subject}", fill=TITLE_FG, font=font_title)
    draw.text(
        (MARGIN, MARGIN + 34),
        f"{cls.date_start.strftime('%d.%m.%Y')} → {cls.date_end.strftime('%d.%m.%Y')}  ·  {session_count} {label_lessons}",
        fill=SUB_FG,
        font=font_sub,
    )

    grid_top = MARGIN + TITLE_H
    for i, (month_name, dates) in enumerate(months):
        col = i % COLS
        row = i // COLS
        x = MARGIN + col * (col_w + GAP)
        y = grid_top + row * (card_h + GAP)

        draw.rectangle([x, y, x + col_w, y + card_h], fill=CARD_BG, outline=CARD_BORDER, width=1)
        draw.rectangle([x, y, x + col_w, y + MONTH_HDR_H], fill=HDR_BG)
        draw.text((x + CELL_PAD, y + (MONTH_HDR_H - 14) // 2), month_name, fill=HDR_FG, font=font_month)

        for j, d in enumerate(dates):
            dy = y + MONTH_HDR_H + CELL_PAD + j * DATE_LINE_H
            draw.text((x + CELL_PAD, dy), d.strftime("%d.%m.%Y"), fill=DATE_FG, font=font_date)

    price_y = grid_top + n_rows * card_h + (n_rows - 1) * GAP + GAP
    draw.rectangle([MARGIN, price_y, IMG_W - MARGIN, price_y + PRICE_BOX_H], fill=PRICE_BG, outline=PRICE_BORDER, width=1)

    formula = f"{session_count} × {_fmt_czk(cls.fee_per_lesson)} = {_fmt_czk(total_fee)} CZK"
    draw.text((MARGIN + 16, price_y + 10), label_price, fill=PRICE_LABEL_FG, font=font_formula_label)
    draw.text((MARGIN + 16, price_y + 26), formula, fill=PRICE_FG, font=font_formula)

    return img


def _is_admin(u) -> bool:
    return u.is_authenticated and u.is_app_admin


admin_required = user_passes_test(_is_admin, login_url="login")


def _visible_students_qs(user):
    qs = Student.objects.all()
    if user.is_app_admin:
        return qs
    return qs.filter(
        Q(enrollments__isnull=True) | Q(enrollments__classroom__teacher=user)
    ).distinct()


def _editable_students_qs(user):
    """Students a non-admin user is allowed to edit: only those enrolled in their classes."""
    if user.is_app_admin:
        return Student.objects.all()
    return Student.objects.filter(enrollments__classroom__teacher=user).distinct()


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "registration/login.html", {"form": form})


@require_POST
@login_required
def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    cards = [
        (_("Timetable"), reverse("timetable")),
        (_("Statistics"), reverse("statistics")),
        (_("Class manager"), reverse("class_list")),
        (_("Create class"), reverse("class_create")),
        (_("Students"), reverse("student_list")),
        (_("Add student"), reverse("student_create")),
        (_("Enrollments"), reverse("enrollment_list")),
        (_("Add enrollment"), reverse("enrollment_create")),
        (_("Class calendar"), reverse("calendar_pick")),
    ]
    if request.user.is_app_admin:
        cards.append((_("Create user"), reverse("user_create")))
    return render(request, "core/dashboard.html", {"cards": cards})


@login_required
def timetable(request):
    qs = (
        ClassRoom.objects
        .filter(status=ClassStatus.ACTIVE)
        .prefetch_related("times")
        .select_related("teacher")
    )
    if not request.user.is_app_admin:
        qs = qs.filter(teacher=request.user)

    grid: "OrderedDict[str, list]" = OrderedDict((d, []) for d in WEEKDAY_ORDER)
    for cls in qs:
        for t in cls.times.all():
            if t.weekday in grid:
                grid[t.weekday].append({"cls": cls, "time": t})

    for day in grid:
        grid[day].sort(key=lambda r: r["time"].time_start)

    weekday_labels = dict(Weekday.choices)
    days = [(d, weekday_labels[d], grid[d]) for d in WEEKDAY_ORDER]
    return render(request, "core/timetable.html", {"days": days})


@login_required
def statistics(request):
    teacher_count = User.objects.filter(role__in=[Role.TEACHER, Role.ADMIN]).count()
    assistant_count = User.objects.filter(role=Role.ASSISTANT).count()
    student_count = Student.objects.count()
    class_count = ClassRoom.objects.count()
    return render(request, "core/statistics.html", {
        "class_count": class_count,
        "teacher_count": teacher_count,
        "assistant_count": assistant_count,
        "student_count": student_count,
    })


@login_required
def class_list(request):
    qs = (
        ClassRoom.objects
        .select_related("teacher")
        .annotate(
            student_count=Count("enrollments", distinct=True),
            actual_total=Sum("enrollments__actual_lessons"),
        )
    )
    if not request.user.is_app_admin:
        qs = qs.filter(teacher=request.user)

    is_admin = request.user.is_app_admin
    rows = []
    for cls in qs:
        if is_admin:
            fee = cls.fee_per_lesson * Decimal(cls.actual_total or 0)
        else:
            fee = cls.fee_per_lesson * Decimal(cls.student_count) * Decimal(cls.total_lessons)
        rows.append({"cls": cls, "fee": fee})
    return render(request, "core/class_list.html", {"rows": rows})


@login_required
def class_create(request):
    form = ClassRoomForm(request.POST or None, current_user=request.user)
    if request.method == "POST" and form.is_valid():
        cls = form.save(commit=False)
        if not request.user.is_app_admin:
            cls.teacher = request.user
        cls.save()
        messages.success(request, _("Class created. Set the lesson schedule."))
        return redirect("class_times", pk=cls.pk)
    return render(request, "core/class_form.html", {"form": form, "title": _("Create class")})


@login_required
def class_edit(request, pk: int):
    cls = get_object_or_404(ClassRoom, pk=pk)
    if not request.user.is_app_admin and cls.teacher_id != request.user.id:
        return HttpResponseForbidden()
    form = ClassRoomForm(request.POST or None, instance=cls, current_user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Class saved."))
        return redirect("class_list")
    return render(request, "core/class_form.html", {"form": form, "title": _("Edit %(code)s") % {"code": cls.code}})


@login_required
def class_times(request, pk: int):
    cls = get_object_or_404(ClassRoom, pk=pk)
    if not request.user.is_app_admin and cls.teacher_id != request.user.id:
        return HttpResponseForbidden()
    formset = ClassTimeFormSet(request.POST or None, instance=cls)
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, _("Schedule saved."))
        return redirect("class_list")
    return render(request, "core/class_times.html", {"cls": cls, "formset": formset})


@login_required
@require_POST
def class_close(request, pk: int):
    cls = get_object_or_404(ClassRoom, pk=pk)
    if not request.user.is_app_admin and cls.teacher_id != request.user.id:
        return HttpResponseForbidden()
    cls.status = ClassStatus.CLOSED
    cls.save(update_fields=["status"])
    messages.success(request, _("Class %(code)s has been closed.") % {"code": cls.code})
    return redirect("class_list")


@login_required
def class_calendar(request, pk: int):
    cls = get_object_or_404(ClassRoom, pk=pk)
    if not request.user.is_app_admin and cls.teacher_id != request.user.id:
        return HttpResponseForbidden()

    form = DayOffForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            DayOff.objects.get_or_create(classroom=cls, date=form.cleaned_data["date"])
        messages.success(request, _("Day off added."))
        return redirect("class_calendar", pk=pk)

    def _parse_date(param):
        try:
            return date_type.fromisoformat(request.GET[param])
        except (KeyError, ValueError):
            return None

    range_start = _parse_date("date_from")
    range_end = _parse_date("date_to")
    if range_start and range_start < cls.date_start:
        range_start = cls.date_start
    if range_end and range_end > cls.date_end:
        range_end = cls.date_end
    if range_start and range_end and range_start > range_end:
        range_start, range_end = None, None

    days = working_days(cls, date_start=range_start, date_end=range_end)
    months = working_days_by_month(days)
    return render(request, "core/class_calendar.html", {
        "cls": cls,
        "months": months,
        "days_off": cls.days_off.all(),
        "form": form,
        "session_count": len(days),
        "range_start": (range_start or cls.date_start).isoformat(),
        "range_end": (range_end or cls.date_end).isoformat(),
        "cls_date_start": cls.date_start.isoformat(),
        "cls_date_end": cls.date_end.isoformat(),
        "is_filtered": bool(range_start or range_end),
    })


@login_required
def calendar_download(request, pk: int):
    cls = get_object_or_404(ClassRoom, pk=pk)
    if not request.user.is_app_admin and cls.teacher_id != request.user.id:
        return HttpResponseForbidden()

    def _parse_date(param):
        try:
            return date_type.fromisoformat(request.GET[param])
        except (KeyError, ValueError):
            return None

    range_start = _parse_date("date_from")
    range_end = _parse_date("date_to")
    days = working_days(cls, date_start=range_start, date_end=range_end)
    months = working_days_by_month(days)
    session_count = len(days)
    total_fee = cls.fee_per_lesson * Decimal(session_count)

    img = _build_calendar_image(
        cls, months, session_count, total_fee,
        label_price=str(_("Total price:")),
        label_lessons=str(_("lessons")),
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    safe_code = "".join(c if c.isalnum() or c in "-_" else "_" for c in cls.code)
    response = HttpResponse(buf.read(), content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="calendar_{safe_code}.png"'
    return response


@login_required
@require_POST
def dayoff_remove(request, pk: int):
    d = get_object_or_404(DayOff, pk=pk)
    cls = d.classroom
    if not request.user.is_app_admin and cls.teacher_id != request.user.id:
        return HttpResponseForbidden()
    d.delete()
    messages.success(request, _("Day off removed."))
    return redirect("class_calendar", pk=cls.pk)


@login_required
def calendar_pick(request):
    qs = ClassRoom.objects.all()
    if not request.user.is_app_admin:
        qs = qs.filter(teacher=request.user)
    return render(request, "core/calendar_pick.html", {"classes": qs})


@login_required
def student_list(request):
    qs = _visible_students_qs(request.user)
    return render(request, "core/student_list.html", {"students": qs})


@login_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        s = form.save()
        messages.success(request, _("Student %(name)s added.") % {"name": s.name})
        return redirect("enrollment_create_for_student", pk=s.pk)
    return render(request, "core/student_form.html", {"form": form, "title": _("Add student")})


@login_required
def student_edit(request, pk: int):
    s = get_object_or_404(_editable_students_qs(request.user), pk=pk)
    form = StudentForm(request.POST or None, instance=s)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Student saved."))
        return redirect("student_list")
    return render(request, "core/student_form.html", {"form": form, "title": _("Edit %(name)s") % {"name": s.name}})


@login_required
@require_POST
def student_delete(request, pk: int):
    if not request.user.is_app_admin:
        return HttpResponseForbidden()
    s = get_object_or_404(Student, pk=pk)
    s.delete()
    messages.success(request, _("Student deleted."))
    return redirect("student_list")


@login_required
def enrollment_list(request):
    qs = Enrollment.objects.select_related("student", "classroom")
    if not request.user.is_app_admin:
        qs = qs.filter(classroom__teacher=request.user)
    return render(request, "core/enrollment_list.html", {"rows": qs})


@login_required
def enrollment_create(request, pk: int | None = None):
    initial = {}
    if pk:
        initial["student"] = get_object_or_404(_visible_students_qs(request.user), pk=pk)
    form = EnrollmentForm(request.POST or None, initial=initial)
    if not request.user.is_app_admin:
        form.fields["student"].queryset = _visible_students_qs(request.user)
        form.fields["classroom"].queryset = ClassRoom.objects.filter(teacher=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Student added to class."))
        return redirect("enrollment_list")
    return render(request, "core/enrollment_form.html", {"form": form, "title": _("Add enrollment")})


@login_required
@require_POST
def enrollment_delete(request, pk: int):
    e = get_object_or_404(Enrollment, pk=pk)
    if not request.user.is_app_admin and e.classroom.teacher_id != request.user.id:
        return HttpResponseForbidden()
    e.delete()
    messages.success(request, _("Enrollment removed."))
    return redirect("enrollment_list")


@admin_required
def user_create(request):
    form = UserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        u: User = form.save(commit=False)
        u.fullname = form.cleaned_data["fullname"]
        u.role = form.cleaned_data["role"]
        u.save()
        messages.success(request, _("User %(username)s created.") % {"username": u.username})
        return redirect("dashboard")
    return render(request, "core/user_form.html", {"form": form, "title": _("Create user")})


@login_required
def autocomplete_class(request):
    q = request.GET.get("q", "").strip()
    qs = ClassRoom.objects.all()
    if not request.user.is_app_admin:
        qs = qs.filter(teacher=request.user)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(subject__icontains=q))
    return render(request, "core/_class_autocomplete.html", {"classes": qs.order_by("code")[:10]})
