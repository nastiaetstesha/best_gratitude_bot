import csv

from django.core.management.base import BaseCommand, CommandError
from core.models import WeeklyTask


class Command(BaseCommand):
    help = "Import WeeklyTask from CSV: iso_year, iso_week, title, description, is_active"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        path = options["csv_path"]

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required = {"iso_year", "iso_week", "title", "description", "is_active"}
                if not required.issubset(reader.fieldnames or []):
                    raise CommandError(f"CSV must contain columns: {sorted(required)}")

                created, updated = 0, 0
                for row in reader:
                    iso_year = int(row["iso_year"])
                    iso_week = int(row["iso_week"])
                    title = row["title"].strip()
                    description = row["description"].strip()
                    is_active = str(row["is_active"]).strip().lower() in {"1", "true", "yes", "y"}

                    obj, was_created = WeeklyTask.objects.update_or_create(
                        iso_year=iso_year,
                        iso_week=iso_week,
                        defaults={
                            "title": title,
                            "description": description,
                            "is_active": is_active,
                        },
                    )
                    created += int(was_created)
                    updated += int(not was_created)

        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")

        self.stdout.write(self.style.SUCCESS(f"Done. created={created}, updated={updated}"))
