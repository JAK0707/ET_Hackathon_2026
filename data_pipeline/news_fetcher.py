from __future__ import annotations

from backend.services.news_service import NewsService


def fetch_latest_news(query: str) -> list[dict]:
    service = NewsService()
    items = service.fetch_news(query)
    return [
        {
            "title": item.title,
            "summary": item.summary,
            "source": item.source,
            "published_at": item.published_at,
            "url": item.url,
            "sentiment_score": item.sentiment_score,
        }
        for item in items
    ]


if __name__ == "__main__":
    print(fetch_latest_news("Nifty"))
