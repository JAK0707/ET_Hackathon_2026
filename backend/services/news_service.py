from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import feedparser
import requests

from backend.config import get_settings


@dataclass
class NewsItem:
    title: str
    summary: str
    source: str
    published_at: str
    url: str
    sentiment_score: float


def _vader_sentiment(text: str) -> float:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        score = analyzer.polarity_scores(text)["compound"]
        return round(score, 2)
    except Exception:
        return _keyword_sentiment(text)


def _keyword_sentiment(text: str) -> float:
    positive = {"gain", "surge", "beats", "strong", "growth", "upgrade", "bullish",
                "rally", "profit", "record", "breakout", "outperform", "buy", "positive"}
    negative = {"fall", "drops", "misses", "weak", "downgrade", "bearish", "fraud",
                "risk", "loss", "decline", "crash", "sell", "negative", "concern", "warning"}
    lowered = text.lower()
    pos = sum(w in lowered for w in positive)
    neg = sum(w in lowered for w in negative)
    return round((pos - neg) / max(1, pos + neg), 2)


class NewsService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_news(self, query: str, limit: int = 5) -> list[NewsItem]:
        if self.settings.news_api_key:
            try:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query,
                    "pageSize": limit,
                    "sortBy": "publishedAt",
                    "apiKey": self.settings.news_api_key,
                }
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                articles = response.json().get("articles", [])
                return [
                    NewsItem(
                        title=item["title"],
                        summary=item.get("description") or "",
                        source=item.get("source", {}).get("name", "NewsAPI"),
                        published_at=item.get("publishedAt") or datetime.utcnow().isoformat(),
                        url=item.get("url") or "",
                        sentiment_score=_vader_sentiment(
                            item["title"] + " " + (item.get("description") or "")
                        ),
                    )
                    for item in articles
                ]
            except Exception:
                pass

        # Free fallback: Google News RSS
        rss_url = (
            f"https://news.google.com/rss/search"
            f"?q={query.replace(' ', '+')}+India+stock+market"
            f"&hl=en-IN&gl=IN&ceid=IN:en"
        )
        try:
            feed = feedparser.parse(rss_url)
            items: list[NewsItem] = []
            for entry in feed.entries[:limit]:
                text = f"{entry.title} {getattr(entry, 'summary', '')}"
                source_obj = getattr(entry, "source", None)
                source_name = (
                    source_obj.get("title", "Google News")
                    if isinstance(source_obj, dict)
                    else "Google News"
                )
                items.append(
                    NewsItem(
                        title=entry.title,
                        summary=getattr(entry, "summary", ""),
                        source=source_name,
                        published_at=getattr(entry, "published", datetime.utcnow().isoformat()),
                        url=getattr(entry, "link", ""),
                        sentiment_score=_vader_sentiment(text),
                    )
                )
            return items
        except Exception:
            return []

    def sentiment(self, text: str) -> float:
        return _vader_sentiment(text)