from __future__ import annotations

from backend.models.schemas import AgentSignal
from backend.services.market_data_service import MarketDataService
from backend.utils.indicators import calculate_support_resistance, trend_strength


class TechnicalAgent:
    def __init__(self) -> None:
        self.market_data = MarketDataService()

    def analyze(self, symbol: str) -> AgentSignal:
        df = self.market_data.fetch_enriched_history(symbol)
        latest = df.iloc[-1]
        support, resistance = calculate_support_resistance(df)
        momentum = trend_strength(df)
        score = 0.0
        key_points = [
            f"RSI(14) is {latest['rsi_14']:.2f}.",
            f"MACD is {latest['macd']:.2f} vs signal {latest['macd_signal']:.2f}.",
            f"Support sits near Rs. {support} and resistance near Rs. {resistance}.",
            f"20-day trend strength is {momentum}%.",
        ]
        if latest["rsi_14"] < 35 and latest["macd"] > latest["macd_signal"]:
            score = 0.7
            key_points.append("Oversold recovery setup is forming.")
        elif latest["rsi_14"] > 68 and latest["macd"] < latest["macd_signal"]:
            score = -0.7
            key_points.append("Momentum shows signs of exhaustion.")
        elif latest["Close"] > latest["sma_20"] > latest["sma_50"]:
            score = 0.5
            key_points.append("Short-term trend remains above medium-term moving averages.")
        return AgentSignal(agent="technical", summary=f"Technical view for {symbol} from indicators and price structure.", score=score, key_points=key_points, sources=["Yahoo Finance OHLCV", "native pandas indicator calculations"])

