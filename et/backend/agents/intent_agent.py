from __future__ import annotations

from backend.models.schemas import IntentType


class IntentAgent:
    def detect(self, message: str) -> IntentType:
        lowered = message.lower()
        if any(word in lowered for word in ["portfolio", "diversification", "allocation", "holdings"]):
            return "portfolio_advice"
        if any(word in lowered for word in ["summary", "market today", "nifty", "sensex", "overview"]):
            return "market_summary"
        return "stock_analysis"
