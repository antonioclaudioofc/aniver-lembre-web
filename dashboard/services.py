import calendar
from datetime import date, timedelta

TONE_NAMES = ["rose", "teal", "amber", "violet", "blue", "lime", "indigo", "orange"]

TONE_COLORS = {
    "rose": {"bg": "#FCE7F3", "fg": "#BE185D", "dot": "#EC4899"},
    "teal": {"bg": "#CCFBF1", "fg": "#0F766E", "dot": "#14B8A6"},
    "amber": {"bg": "#FEF3C7", "fg": "#B45309", "dot": "#F59E0B"},
    "violet": {"bg": "#EDE9FE", "fg": "#6D28D9", "dot": "#8B5CF6"},
    "blue": {"bg": "#DBEAFE", "fg": "#1D4ED8", "dot": "#3B82F6"},
    "lime": {"bg": "#ECFCCB", "fg": "#4D7C0F", "dot": "#84CC16"},
    "indigo": {"bg": "#E0E7FF", "fg": "#4338CA", "dot": "#6366F1"},
    "orange": {"bg": "#FFEDD5", "fg": "#C2410C", "dot": "#F97316"},
}

MONTH_ABBR = [
    "",
    "JAN",
    "FEV",
    "MAR",
    "ABR",
    "MAI",
    "JUN",
    "JUL",
    "AGO",
    "SET",
    "OUT",
    "NOV",
    "DEZ",
]

MONTH_NAMES = [
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]

WEEKDAYS = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]


def tone_for(value):
    return TONE_NAMES[int(value) % len(TONE_NAMES)]


def next_occurrence(birthday, today):
    for year in range(today.year, today.year + 9):
        try:
            occurrence = birthday.replace(year=year)
        except ValueError:
            continue
        if occurrence >= today:
            return occurrence
    return None


def annotate(reminder, today):
    contact = reminder.contact
    occurrence = next_occurrence(contact.birthday, today)
    reminder.next_date = occurrence
    reminder.tone = tone_for(contact.id)
    reminder.stamp_month = MONTH_ABBR[contact.birthday.month]
    reminder.stamp_day = contact.birthday.day
    if occurrence is None:
        reminder.days_until_birthday = None
        reminder.turning_age = None
        reminder.notify_date = None
    else:
        reminder.days_until_birthday = (occurrence - today).days
        reminder.turning_age = occurrence.year - contact.birthday.year
        reminder.notify_date = occurrence - timedelta(days=reminder.days_before)
    return reminder


def annotate_all(reminders, today):
    return [annotate(r, today) for r in reminders]


def sort_by_proximity(reminders):
    return sorted(
        reminders,
        key=lambda r: (r.days_until_birthday is None, r.days_until_birthday or 0),
    )


def calendar_data(reminders, today):
    by_day = {}
    for r in reminders:
        birthday = r.contact.birthday
        by_day.setdefault((birthday.month, birthday.day), []).append(r)

    months = []
    year, month = today.year, today.month
    for _ in range(12):
        first_weekday = (date(year, month, 1).weekday() + 1) % 7
        total_days = calendar.monthrange(year, month)[1]
        days = {}
        for day in range(1, total_days + 1):
            people = list(by_day.get((month, day), []))
            if month == 2 and day == 28 and not calendar.isleap(year):
                people += by_day.get((2, 29), [])
            if people:
                days[day] = [
                    {
                        "id": r.id,
                        "name": r.contact.name,
                        "tone": r.tone,
                        "age": year - r.contact.birthday.year,
                        "relationship": r.contact.relationship,
                        "active": r.active,
                    }
                    for r in people
                ]
        months.append(
            {
                "year": year,
                "month": month,
                "label": f"{MONTH_NAMES[month]} {year}",
                "lead": first_weekday,
                "total": total_days,
                "days": days,
            }
        )
        month += 1
        if month > 12:
            month, year = 1, year + 1

    return {
        "months": months,
        "today": [today.year, today.month, today.day],
        "tones": TONE_COLORS,
    }
