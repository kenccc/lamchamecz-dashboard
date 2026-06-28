import calendar as _calendar
from collections import defaultdict
from datetime import date, timedelta

from django.utils.dates import WEEKDAYS_ABBR
from django.utils.formats import date_format

from .models import WEEKDAY_ISO, ClassRoom


def weekday_headers() -> list:
    """Monday-first localized short weekday names for calendar headers."""
    return [WEEKDAYS_ABBR[i] for i in range(7)]


def build_calendar_months(
    lesson_dates: list[date],
    dayoff_dates,
    today: date | None = None,
) -> list[dict]:
    """Arrange lesson dates into Google-Calendar-style month matrices.

    Each month is a dict with ``name``, ``lesson_count`` and ``weeks`` — a list
    of weeks, each a list of 7 day cells flagged for rendering.
    """
    lessons = set(lesson_dates)
    if not lessons:
        return []
    offs = set(dayoff_dates)
    cal = _calendar.Calendar(firstweekday=_calendar.MONDAY)

    months = []
    for year, month in sorted({(d.year, d.month) for d in lessons}):
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            weeks.append([
                {
                    "day": d.day,
                    "date": d,
                    "in_month": d.month == month,
                    "is_lesson": d in lessons,
                    "is_dayoff": d in offs,
                    "is_today": d == today,
                }
                for d in week
            ])
        months.append({
            "name": date_format(date(year, month, 1), format="F Y", use_l10n=True),
            "lesson_count": sum(1 for d in lessons if d.year == year and d.month == month),
            "weeks": weeks,
        })
    return months


def working_days(
    classroom: ClassRoom,
    date_start: date | None = None,
    date_end: date | None = None,
) -> list[date]:
    """Compute list of class session dates respecting weekdays + day-offs."""
    weekdays = {
        iso for iso in (WEEKDAY_ISO.get(t.weekday) for t in classroom.times.all()) if iso
    }
    if not weekdays:
        return []
    holidays = {d.date for d in classroom.days_off.all()}
    out: list[date] = []
    cur = date_start or classroom.date_start
    end = date_end or classroom.date_end
    while cur <= end:
        if cur.isoweekday() in weekdays and cur not in holidays:
            out.append(cur)
        cur += timedelta(days=1)
    return out



def working_days_by_month(dates: list[date]) -> list[tuple[str, list[date]]]:
    grouped: dict[str, list[date]] = defaultdict(list)
    for d in dates:
        grouped[d.strftime("%Y-%m")].append(d)
    return [
        (date_format(date.fromisoformat(f"{key}-01"), format="F Y", use_l10n=True), vals)
        for key, vals in sorted(grouped.items())
    ]
