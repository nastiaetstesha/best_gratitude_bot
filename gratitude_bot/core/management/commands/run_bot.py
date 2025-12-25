from django.core.management.base import BaseCommand

from core.bot.bot import build_updater


class Command(BaseCommand):
    help = "Run Telegram bot (polling)"

    def handle(self, *args, **options):
        updater = build_updater()
        updater.start_polling()
        updater.idle()
