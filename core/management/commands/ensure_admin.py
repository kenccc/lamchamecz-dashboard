import os

from django.core.management.base import BaseCommand, CommandError

from core.models import Role, User

WEAK_PASSWORDS = {"admin", "password", "changeme", "change-me", "12345678"}


class Command(BaseCommand):
    help = "Create the bootstrap admin from env (only sets password on first creation)."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD")
        fullname = os.getenv("ADMIN_FULLNAME", "Administrator")

        if not password:
            raise CommandError("ADMIN_PASSWORD env var is required.")
        if password.lower() in WEAK_PASSWORDS or len(password) < 12:
            raise CommandError(
                "ADMIN_PASSWORD is too weak. Use at least 12 chars and avoid common values."
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "fullname": fullname,
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"created admin '{username}'"))
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"admin '{username}' already exists; password not changed"
                )
            )
