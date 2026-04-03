from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .forms import BookmarkUpdateForm, CustomUserCreationForm, UserPreferenceForm
from .models import Bookmark, UserProfile
from .news import DEFAULT_IMAGE_URL, digest_due_for_profile, get_articles_for_category, get_digest_articles_for_user, get_personalized_home_articles, refresh_all_categories


def get_bookmarked_urls(request):
    if not request.user.is_authenticated:
        return set()
    return set(
        Bookmark.objects.filter(user=request.user).values_list("url", flat=True)
    )


def serialize_articles(articles):
    serialized = []
    for article in articles:
        serialized.append(
            {
                "headline": article.headline,
                "title": article.title or article.headline,
                "summary": article.summary,
                "url": article.url,
                "full_url": article.url,
                "image_url": article.image_url or DEFAULT_IMAGE_URL,
                "source": article.source,
                "category": article.category,
                "published_at": article.published_at,
            }
        )
    return serialized


def render_news_page(request, template_name, articles):
    return render(
        request,
        template_name,
        {
            "news_data": serialize_articles(articles),
            "bookmarked_urls": get_bookmarked_urls(request),
        },
    )


def home(request):
    query = (request.GET.get("q") or "").strip()
    return render_news_page(
        request,
        "hello.html",
        get_personalized_home_articles(request.user, query=query),
    )


def national(request):
    query = (request.GET.get("q") or "").strip()
    return render_news_page(
        request,
        "national.html",
        get_articles_for_category("national", query=query),
    )


def international(request):
    query = (request.GET.get("q") or "").strip()
    return render_news_page(
        request,
        "international.html",
        get_articles_for_category("international", query=query),
    )


def sports(request):
    query = (request.GET.get("q") or "").strip()
    return render_news_page(
        request,
        "sports.html",
        get_articles_for_category("sports", query=query),
    )


def science(request):
    query = (request.GET.get("q") or "").strip()
    return render_news_page(
        request,
        "science.html",
        get_articles_for_category("science", query=query),
    )


def health(request):
    query = (request.GET.get("q") or "").strip()
    return render_news_page(
        request,
        "health.html",
        get_articles_for_category("health", query=query),
    )


@login_required
@require_POST
def refresh_news(request):
    refresh_all_categories(force=True)
    messages.success(request, "News sources refreshed and cached.")
    return redirect(request.POST.get("next") or "home")


@login_required
@require_POST
def toggle_bookmark(request):
    url = (request.POST.get("url") or "").strip()
    headline = (request.POST.get("headline") or "").strip()
    title = (request.POST.get("title") or headline or "No Title").strip()
    image_url = (request.POST.get("image_url") or DEFAULT_IMAGE_URL).strip()
    summary = (request.POST.get("summary") or "").strip()
    source = (request.POST.get("source") or "").strip()
    category = (request.POST.get("category") or "").strip()
    collection = (request.POST.get("collection") or "Read later").strip()
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "home"

    if not url or not headline:
        messages.error(request, "Missing news details, so the bookmark was not saved.")
        return redirect(next_url)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        url=url,
        defaults={
            "headline": headline,
            "title": title,
            "image_url": image_url,
            "summary": summary,
            "source": source,
            "category": category,
            "collection": collection,
        },
    )

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"email": request.user.email or "example@example.com"},
    )
    if created:
        profile.bookmarks.add(bookmark)
        messages.success(request, "Bookmark saved.")
    else:
        profile.bookmarks.remove(bookmark)
        bookmark.delete()
        messages.info(request, "Bookmark removed.")

    return HttpResponseRedirect(next_url)


@login_required
@require_POST
def update_bookmark(request, bookmark_id):
    bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
    form = BookmarkUpdateForm(request.POST)
    if form.is_valid():
        bookmark.collection = form.cleaned_data["collection"]
        bookmark.notes = form.cleaned_data["notes"]
        bookmark.save(update_fields=["collection", "notes"])
        messages.success(request, "Bookmark updated.")
    else:
        messages.error(request, "Could not update that bookmark.")
    return redirect("profile")


@login_required
@require_POST
def send_digest_now(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"email": request.user.email or "example@example.com"},
    )
    articles = get_digest_articles_for_user(user)
    if not articles:
        messages.warning(request, "No articles are available for your digest yet.")
        return redirect("profile")

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
    except Exception:
        messages.error(
            request,
            "Digest could not be sent because the email server credentials are not working right now.",
        )
        return redirect("profile")

    messages.success(request, "Test digest sent to your email.")
    return redirect("profile")


def user_login(request):
    next_url = request.GET.get("next", "")
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("home")

        messages.error(request, "Invalid username or password.")
        return render(request, "login.html", {"next_url": next_url})

    return render(request, "login.html", {"next_url": next_url})


def user_logout(request):
    logout(request)
    return redirect("home")


def user_signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            try:
                validate_email(user.email)
            except ValidationError:
                form.add_error("email", "Invalid email address.")
                return render(request, "signup.html", {"form": form})

            user.save()
            messages.success(request, "Signup successful! Please log in.")
            login(request, user)
            return redirect("login")
        messages.error(request, "Please correct the highlighted errors below.")
        return render(request, "signup.html", {"form": form})

    return render(request, "signup.html", {"form": CustomUserCreationForm()})


class CustomLoginView(LoginView):
    def get_success_url(self):
        return self.request.GET.get("next", "home")


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"email": request.user.email or "example@example.com"},
    )

    if request.method == "POST" and request.POST.get("form_type") == "preferences":
        form = UserPreferenceForm(request.POST)
        if form.is_valid():
            profile.preferred_categories = ",".join(form.cleaned_data["preferred_categories"])
            profile.preferred_sources = ",".join(form.cleaned_data["preferred_sources"])
            profile.digest_enabled = form.cleaned_data["digest_enabled"]
            profile.digest_frequency = form.cleaned_data["digest_frequency"]
            profile.save()
            messages.success(request, "Preferences updated.")
            return redirect("profile")
    else:
        form = UserPreferenceForm(
            initial={
                "preferred_categories": [
                    value for value in profile.preferred_categories.split(",") if value
                ],
                "preferred_sources": [
                    value for value in profile.preferred_sources.split(",") if value
                ],
                "digest_enabled": profile.digest_enabled,
                "digest_frequency": profile.digest_frequency,
            }
        )

    bookmarks = Bookmark.objects.filter(user=request.user)
    digest_articles = get_digest_articles_for_user(request.user, limit=5)
    return render(
        request,
        "profile.html",
        {
            "bookmarks": bookmarks,
            "preference_form": form,
            "digest_articles": digest_articles,
            "digest_due": digest_due_for_profile(profile),
        },
    )
