from django.contrib import admin
from .models import Bookmark, NewsArticle, SourceStatus, UserProfile


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("headline", "source", "category", "published_at", "fetched_at", "is_active")
    list_filter = ("source", "category", "is_active")
    search_fields = ("headline", "summary", "url")


@admin.register(SourceStatus)
class SourceStatusAdmin(admin.ModelAdmin):
    list_display = ("source", "category", "status", "article_count", "last_attempt_at", "last_success_at")
    list_filter = ("category", "status", "source")
    search_fields = ("source", "category", "error_message")


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("headline", "user", "source", "category", "collection", "created_at")
    list_filter = ("source", "category", "collection")
    search_fields = ("headline", "url", "notes")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "digest_enabled", "digest_frequency")
    search_fields = ("user__username", "email")
