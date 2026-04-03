from django.core.management.base import BaseCommand

from app.news import refresh_all_categories


class Command(BaseCommand):
    help = "Refresh and cache news articles from all configured sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh even if cached articles are still fresh.",
        )

    def handle(self, *args, **options):
        refresh_all_categories(force=options["force"])
        self.stdout.write(self.style.SUCCESS("News cache refreshed successfully."))
