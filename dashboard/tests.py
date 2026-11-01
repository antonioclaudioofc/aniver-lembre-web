from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.utils import get_profile
from contacts.models import Contact
from dashboard import services
from reminders.models import Reminder


def make_reminder(profile, name, birthday, days_before=1, active=True):
    contact = Contact.objects.create(owner=profile, name=name, birthday=birthday)
    return Reminder.objects.create(
        contact=contact, days_before=days_before, notify_at="09:00", active=active
    )


class ServicesTests(TestCase):
    def test_next_occurrence_handles_leap_day(self):
        result = services.next_occurrence(date(2000, 2, 29), date(2026, 3, 1))
        self.assertEqual(result, date(2028, 2, 29))

    def test_tone_is_stable_by_id(self):
        self.assertEqual(services.tone_for(1), services.tone_for(9))
        self.assertNotEqual(services.tone_for(1), services.tone_for(2))


class DashboardPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", "ana@example.com", "senha-forte-1")
        self.profile = get_profile(self.user)
        self.profile.email_verified = True
        self.profile.save()
        self.client.force_login(self.user)
        today = timezone.localdate()
        self.soon = make_reminder(
            self.profile, "Marina Costa", today + timedelta(days=3, weeks=-52 * 20)
        )
        self.far = make_reminder(
            self.profile, "Roberto", today + timedelta(days=100, weeks=-52 * 30)
        )
        self.paused = make_reminder(
            self.profile, "Pausado", today + timedelta(days=10), active=False
        )

    def test_home_renders_featured_and_calendar(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["featured"].id, self.soon.id)
        self.assertEqual(len(response.context["calendar_payload"]["months"]), 12)
        self.assertContains(response, "Marina Costa")
        self.assertContains(response, "calendarData")

    def test_home_search_filters_people(self):
        response = self.client.get(reverse("dashboard:index"), {"q": "rober"})
        names = [r.contact.name for r in response.context["people"]]
        self.assertEqual(names, ["Roberto"])

    def test_people_page_filters_by_month(self):
        month = self.far.contact.birthday.month
        response = self.client.get(reverse("dashboard:people"), {"month": month})
        self.assertEqual(response.status_code, 200)
        ids = [r.id for r in response.context["reminders"]]
        self.assertIn(self.far.id, ids)

    def test_people_page_sorted_by_proximity(self):
        response = self.client.get(reverse("dashboard:people"))
        days = [r.days_until_birthday for r in response.context["reminders"]]
        self.assertEqual(days, sorted(days))

    def test_empty_user_renders_empty_states(self):
        Reminder.objects.all().delete()
        for name in ("dashboard:index", "dashboard:people"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Nenhum aniversário")

    def test_profile_page_renders(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)

    def test_create_redirects_back_with_saved_id(self):
        response = self.client.post(
            reverse("dashboard:create_reminder"),
            {
                "name": "Novo",
                "birthday": "1990-05-10",
                "relationship": "",
                "notes": "",
                "days_before": "3",
                "notify_at": "08:30",
                "active": "on",
                "next": "people",
                "page": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        reminder = Reminder.objects.get(contact__name="Novo")
        self.assertIn(reverse("dashboard:people"), response.url)
        self.assertIn("reminder_created=1", response.url)
        self.assertIn(f"saved={reminder.id}", response.url)

    def test_invalid_create_reopens_dialog(self):
        response = self.client.post(
            reverse("dashboard:create_reminder"),
            {"name": "", "birthday": "", "days_before": "1", "notify_at": "09:00"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_dialog"])

    def test_delete_from_people_returns_to_people(self):
        response = self.client.post(
            reverse("dashboard:delete_reminder", args=[self.far.id]),
            {"next": "people", "page": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("dashboard:people"), response.url)
        self.assertFalse(Reminder.objects.filter(pk=self.far.id).exists())

    def test_cannot_delete_other_users_reminder(self):
        other = User.objects.create_user("bia", "bia@example.com", "senha-forte-2")
        theirs = make_reminder(get_profile(other), "Alheio", date(1991, 1, 1))
        response = self.client.post(
            reverse("dashboard:delete_reminder", args=[theirs.id])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Reminder.objects.filter(pk=theirs.id).exists())


class SmokeTests(TestCase):
    def test_public_pages_render(self):
        for name in (
            "accounts:login",
            "accounts:register",
            "accounts:password_reset_request",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertNotContains(response, "material-symbols")

    def test_not_found_page_renders(self):
        response = self.client.get("/nao-existe-mesmo/")
        self.assertEqual(response.status_code, 404)

    def test_panel_pages_render_for_superuser(self):
        admin = User.objects.create_superuser(
            "root", "root@example.com", "senha-forte-3"
        )
        profile = get_profile(admin)
        profile.email_verified = True
        profile.save()
        make_reminder(profile, "Admin Contato", date(1990, 6, 6))
        self.client.force_login(admin)
        for name in ("panel:overview", "panel:users", "panel:reminders"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
