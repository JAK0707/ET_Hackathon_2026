from __future__ import annotations

from backend.services.market_data_service import MarketDataService


def fetch_stock_snapshot(symbol: str) -> dict:
    service = MarketDataService()
    quote = service.fetch_quote(symbol)
    history = service.fetch_recent_closes(symbol)
    return {
        "symbol": symbol,
        "price": quote.price,
        "change_pct": quote.change_pct,
        "volume": quote.volume,
        "history": history,
        "sector": quote.sector,
    }


if __name__ == "__main__":
    print(fetch_stock_snapshot("TCS.NS"))
