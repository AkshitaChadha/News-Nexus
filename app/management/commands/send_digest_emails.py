import logging

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from django.contrib.auth.models import User

from app.news import digest_due_for_profile, get_digest_articles_for_user, refresh_all_categories


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send digest emails to users who have digest enabled."

    def handle(self, *args, **options):
        refresh_all_categories(force=False)
        sent_count = 0
        for user in User.objects.select_related("userprofile").all():
            profile = getattr(user, "userprofile", None)
            if not profile or not profile.digest_enabled or not user.email:
                continue
            if not digest_due_for_profile(profile):
                continue

            articles = get_digest_articles_for_user(user)
            if not articles:
                continue

            html_content = render_to_string(
                "digest_email.html",
                {"user": user, "articles": articles},
            )
            text_content = "\n".join(
                [f"- {article.headline} ({article.source})\n  {article.url}" for article in articles]
            )

            try:
                send_mail(
                    subject="Your News Nexus digest",
                    message=text_content,
                    from_email=None,
                    recipient_list=[user.email],
                    html_message=html_content,
                    fail_silently=False,
                )
                profile.last_digest_sent_at = timezone.now()
                profile.save(update_fields=["last_digest_sent_at"])
                sent_count += 1
            except Exception as exc:
                logger.warning("Digest email failed for %s: %s", user.email, exc)

        self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} digest email(s)."))
