from django.contrib.auth.models import User
from django.db import models


class NewsArticle(models.Model):
    CATEGORY_CHOICES = [
        ("home", "Home"),
        ("national", "National"),
        ("international", "International"),
        ("sports", "Sports"),
        ("science", "Science"),
        ("health", "Health"),
    ]

    headline = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    url = models.URLField(unique=True)
    image_url = models.URLField(blank=True, null=True)
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    published_at = models.DateTimeField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at", "-fetched_at"]

    def __str__(self):
        return f"{self.source}: {self.headline}"


class SourceStatus(models.Model):
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=30)
    endpoint = models.URLField()
    last_attempt_at = models.DateTimeField(blank=True, null=True)
    last_success_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default="unknown")
    error_message = models.TextField(blank=True)
    article_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("source", "category")
        ordering = ["category", "source"]

    def __str__(self):
        return f"{self.category} - {self.source} ({self.status})"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()
    headline = models.CharField(max_length=255)
    title = models.CharField(max_length=255, default="No Title")
    image_url = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True)
    source = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=30, blank=True)
    collection = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "url")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.headline}"


class UserProfile(models.Model):
    email = models.EmailField(unique=True, default="example@example.com")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bookmarks = models.ManyToManyField(Bookmark, blank=True)
    preferred_categories = models.CharField(
        max_length=255,
        default="home,national,international,sports,science,health",
    )
    preferred_sources = models.CharField(
        max_length=255,
        default="NDTV,The Hindu,India Today,News18",
    )
    digest_enabled = models.BooleanField(default=True)
    digest_frequency = models.CharField(max_length=20, default="daily")
    last_digest_sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username
