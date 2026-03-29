from __future__ import annotations

from backend.models.schemas import AgentSignal
from backend.services.news_service import NewsService


class NewsAgent:
    def __init__(self) -> None:
        self.news_service = NewsService()

    def analyze(self, symbol: str) -> AgentSignal:
        news_items = self.news_service.fetch_news(symbol, limit=5)
        avg_sentiment = round(sum(item.sentiment_score for item in news_items) / max(len(news_items), 1), 2)
        key_points = [f"{item.title} ({item.source}, sentiment {item.sentiment_score:+.2f})" for item in news_items[:3]] or ["No recent news headlines were available."]
        return AgentSignal(agent="news", summary=f"News sentiment for {symbol} based on recent headlines.", score=avg_sentiment, key_points=key_points, sources=[item.url for item in news_items if item.url])
