from collections import defaultdict
from datetime import date, timedelta

from django.utils.formats import date_format

from .models import WEEKDAY_ISO, ClassRoom


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
