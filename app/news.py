import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.db.models import Q
from django.utils import timezone

from .models import NewsArticle, SourceStatus


logger = logging.getLogger(__name__)

DEFAULT_IMAGE_URL = "/static/img/depositphotos_132158888-stock-photo-science-concept-science-on-newspaper.jpg"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 15
REFRESH_INTERVAL_MINUTES = 30

SOURCE_CONFIGS = {
    "home": [
        {
            "source": "NDTV",
            "category": "home",
            "endpoint": "https://feeds.feedburner.com/ndtvnews-top-stories",
            "mode": "rss",
        },
        {
            "source": "The Hindu",
            "category": "home",
            "endpoint": "https://www.thehindu.com/feeder/default.rss",
            "mode": "rss",
        },
    ],
    "national": [
        {
            "source": "NDTV",
            "category": "national",
            "endpoint": "https://feeds.feedburner.com/ndtvnews-india-news",
            "mode": "rss",
        },
        {
            "source": "The Hindu",
            "category": "national",
            "endpoint": "https://www.thehindu.com/news/national/feeder/default.rss",
            "mode": "rss",
        },
    ],
    "international": [
        {
            "source": "The Hindu",
            "category": "international",
            "endpoint": "https://www.thehindu.com/news/international/feeder/default.rss",
            "mode": "rss",
        },
        {
            "source": "India Today",
            "category": "international",
            "endpoint": "https://www.indiatoday.in/world",
            "mode": "card",
            "item_selectors": ("article.B1S3_story__card__A_fhi", "article"),
        },
        {
            "source": "News18",
            "category": "international",
            "endpoint": "https://www.news18.com/world/",
            "mode": "card",
            "item_selectors": ("div.left", "a.CN-videoListbox"),
            "headline_selectors": ("h3",),
            "link_selectors": ("h3 a[href]", "a[href]"),
        },
    ],
    "sports": [
        {
            "source": "The Hindu",
            "category": "sports",
            "endpoint": "https://www.thehindu.com/sport/feeder/default.rss",
            "mode": "rss",
        },
        {
            "source": "India Today",
            "category": "sports",
            "endpoint": "https://www.indiatoday.in/sports",
            "mode": "card",
            "item_selectors": ("article.B1S3_story__card__A_fhi", "article"),
        },
    ],
    "science": [
        {
            "source": "The Hindu",
            "category": "science",
            "endpoint": "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
            "mode": "rss",
        },
        {
            "source": "India Today",
            "category": "science",
            "endpoint": "https://www.indiatoday.in/science",
            "mode": "card",
            "item_selectors": ("article.B1S3_story__card__A_fhi", "article"),
        },
    ],
    "health": [
        {
            "source": "India Today",
            "category": "health",
            "endpoint": "https://www.indiatoday.in/health",
            "mode": "card",
            "item_selectors": ("article.B1S3_story__card__A_fhi", "article"),
        },
    ],
}


def fetch_content(url):
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.content


def normalize_image_url(image_url):
    if not image_url:
        return DEFAULT_IMAGE_URL
    if image_url.startswith("//"):
        return f"https:{image_url}"
    return image_url


def parse_datetime(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.utc)
        return parsed
    except Exception:
        return None


def build_news_item(headline, url, source, category, image_url=None, summary="", published_at=None):
    headline = (headline or "").strip()
    url = (url or "").strip()
    if not headline or not url:
        return None
    return {
        "headline": headline,
        "title": headline,
        "summary": (summary or "").strip(),
        "url": url,
        "image_url": normalize_image_url(image_url),
        "source": source,
        "category": category,
        "published_at": published_at,
    }


def dedupe_news(items):
    seen = set()
    cleaned = []
    for item in items:
        if not item:
            continue
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        cleaned.append(item)
    return cleaned


def scrape_rss_feed(config, limit=12):
    root = ET.fromstring(fetch_content(config["endpoint"]))
    media_ns = {"media": "http://search.yahoo.com/mrss/"}
    news_items = []

    for item in root.findall(".//item"):
        headline = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        summary = BeautifulSoup(
            item.findtext("description", default=""),
            "html.parser",
        ).get_text(" ", strip=True)
        published_at = parse_datetime(item.findtext("pubDate", default=""))

        image_url = None
        for tag_name in ("media:content", "media:thumbnail"):
            media_tag = item.find(tag_name, media_ns)
            if media_tag is not None:
                image_url = media_tag.attrib.get("url")
                break

        if not image_url:
            enclosure = item.find("enclosure")
            if enclosure is not None:
                image_url = enclosure.attrib.get("url")

        if not image_url:
            desc_soup = BeautifulSoup(item.findtext("description", default=""), "html.parser")
            desc_img = desc_soup.find("img")
            if desc_img:
                image_url = desc_img.get("src") or desc_img.get("data-src")

        news_item = build_news_item(
            headline=headline,
            url=link,
            source=config["source"],
            category=config["category"],
            image_url=image_url,
            summary=summary,
            published_at=published_at,
        )
        if news_item:
            news_items.append(news_item)
        if len(news_items) >= limit:
            break

    return dedupe_news(news_items)


def first_matching_elements(soup, selectors):
    for selector in selectors:
        matches = soup.select(selector)
        if matches:
            return matches
    return []


def scrape_card_page(config, limit=12):
    soup = BeautifulSoup(fetch_content(config["endpoint"]), "html.parser")
    items = first_matching_elements(soup, config.get("item_selectors", ()))
    headline_selectors = config.get("headline_selectors", ("h2", "h3"))
    link_selectors = config.get("link_selectors", ("a[href]",))
    image_selectors = config.get("image_selectors", ("img",))
    news_items = []

    for item in items:
        headline_tag = None
        for selector in headline_selectors:
            headline_tag = item.select_one(selector)
            if headline_tag:
                break

        link_tag = None
        for selector in link_selectors:
            link_tag = item.select_one(selector)
            if link_tag and link_tag.get("href"):
                break

        image_tag = None
        for selector in image_selectors:
            image_tag = item.select_one(selector)
            if image_tag:
                break

        image_url = None
        if image_tag:
            image_url = (
                image_tag.get("data-src")
                or image_tag.get("src")
                or image_tag.get("placeholdersrc")
                or image_tag.get("data-lazy-src")
            )

        summary_tag = item.select_one("p")
        news_item = build_news_item(
            headline=headline_tag.get_text(" ", strip=True) if headline_tag else "",
            url=urljoin(config["endpoint"], link_tag.get("href")) if link_tag else "",
            source=config["source"],
            category=config["category"],
            image_url=image_url,
            summary=summary_tag.get_text(" ", strip=True) if summary_tag else "",
        )
        if news_item:
            news_items.append(news_item)
        if len(news_items) >= limit:
            break

    return dedupe_news(news_items)


def scrape_source(config):
    if config["mode"] == "rss":
        return scrape_rss_feed(config)
    return scrape_card_page(config)


def upsert_articles(items):
    for item in items:
        NewsArticle.objects.update_or_create(
            url=item["url"],
            defaults={
                "headline": item["headline"],
                "title": item["title"],
                "summary": item["summary"],
                "image_url": item["image_url"],
                "source": item["source"],
                "category": item["category"],
                "published_at": item["published_at"],
                "is_active": True,
            },
        )


def update_source_status(config, status, article_count=0, error_message=""):
    now = timezone.now()
    defaults = {
        "endpoint": config["endpoint"],
        "last_attempt_at": now,
        "status": status,
        "error_message": error_message[:1000],
        "article_count": article_count,
    }
    if status == "success":
        defaults["last_success_at"] = now

    SourceStatus.objects.update_or_create(
        source=config["source"],
        category=config["category"],
        defaults=defaults,
    )


def refresh_category(category, force=False):
    if category not in SOURCE_CONFIGS:
        return []

    cutoff = timezone.now() - timezone.timedelta(minutes=REFRESH_INTERVAL_MINUTES)
    if not force and NewsArticle.objects.filter(category=category, fetched_at__gte=cutoff).exists():
        return list(NewsArticle.objects.filter(category=category))

    collected = []
    for config in SOURCE_CONFIGS[category]:
        try:
            items = scrape_source(config)
            upsert_articles(items)
            update_source_status(config, "success", article_count=len(items))
            collected.extend(items)
        except Exception as exc:
            logger.warning("Source refresh failed for %s/%s: %s", category, config["source"], exc)
            update_source_status(config, "failed", error_message=str(exc))

    return collected


def refresh_all_categories(force=False):
    for category in SOURCE_CONFIGS:
        refresh_category(category, force=force)


def get_articles_for_category(category, query=""):
    refresh_category(category)
    queryset = NewsArticle.objects.filter(category=category, is_active=True)
    if query:
        queryset = queryset.filter(
            Q(headline__icontains=query)
            | Q(summary__icontains=query)
            | Q(source__icontains=query)
        )
    return queryset


def split_csv_values(raw_value):
    return [value.strip() for value in (raw_value or "").split(",") if value.strip()]


def get_personalized_home_articles(user=None, query=""):
    refresh_category("home")
    refresh_category("national")
    refresh_category("international")

    queryset = NewsArticle.objects.filter(
        category__in=["home", "national", "international"],
        is_active=True,
    )

    if query:
        queryset = queryset.filter(
            Q(headline__icontains=query)
            | Q(summary__icontains=query)
            | Q(source__icontains=query)
        )

    articles = list(queryset)
    if not user or not user.is_authenticated:
        return sorted(
            articles,
            key=lambda article: (article.published_at or timezone.now(), article.fetched_at),
            reverse=True,
        )

    profile = getattr(user, "userprofile", None)
    preferred_categories = split_csv_values(profile.preferred_categories if profile else "")
    preferred_sources = split_csv_values(profile.preferred_sources if profile else "")

    def article_score(article):
        score = 0
        if article.category in preferred_categories:
            score += 4
        if article.source in preferred_sources:
            score += 3
        if article.category == "home":
            score += 1
        freshness = article.published_at or article.fetched_at or timezone.now()
        return (score, freshness)

    return sorted(articles, key=article_score, reverse=True)


def get_digest_articles_for_user(user, limit=8):
    profile = getattr(user, "userprofile", None)
    preferred_categories = split_csv_values(profile.preferred_categories if profile else "")
    preferred_sources = split_csv_values(profile.preferred_sources if profile else "")

    queryset = NewsArticle.objects.filter(is_active=True)
    if preferred_categories:
        queryset = queryset.filter(category__in=preferred_categories)
    if preferred_sources:
        queryset = queryset.filter(source__in=preferred_sources)

    return list(queryset.order_by("-published_at", "-fetched_at")[:limit])


def digest_due_for_profile(profile, now=None):
    if not profile or not profile.digest_enabled:
        return False

    now = now or timezone.now()
    if not profile.last_digest_sent_at:
        return True

    frequency = (profile.digest_frequency or "daily").lower()
    if frequency == "weekly":
        delta = timezone.timedelta(days=7)
    else:
        delta = timezone.timedelta(days=1)

    return profile.last_digest_sent_at <= now - delta
