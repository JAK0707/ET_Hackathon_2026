from __future__ import annotations

from collections import defaultdict

from backend.models.schemas import HoldingInput, PortfolioAnalysisResponse, PortfolioHoldingAnalysis
from backend.services.market_data_service import MarketDataService


class PortfolioService:
    def __init__(self) -> None:
        self.market_data = MarketDataService()

    def analyze(self, holdings: list[HoldingInput], explain_like_im_5: bool = False) -> PortfolioAnalysisResponse:
        if not holdings:
            return PortfolioAnalysisResponse(
                diversification_score=0,
                sector_exposure={},
                risk_alerts=["Add holdings to unlock portfolio-aware analysis."],
                holdings=[],
                summary="No holdings were provided.",
                explain_like_im_5="Your basket is empty, so I cannot tell if it is balanced yet." if explain_like_im_5 else None,
            )

        enriched_holdings: list[PortfolioHoldingAnalysis] = []
        sector_value: dict[str, float] = defaultdict(float)
        total_value = 0.0
        raw_rows: list[tuple[HoldingInput, float, str]] = []

        for holding in holdings:
            quote = self.market_data.fetch_quote(holding.symbol)
            current_value = quote.price * holding.quantity
            total_value += current_value
            sector = holding.sector or quote.sector or "Unknown"
            sector_value[sector] += current_value
            raw_rows.append((holding, quote.price, sector))

        risk_alerts: list[str] = []
        for holding, current_price, sector in raw_rows:
            weight = round((current_price * holding.quantity / total_value) * 100, 2)
            pnl_pct = round(((current_price - holding.average_price) / holding.average_price) * 100, 2)
            risk_flag = "Healthy"
            if weight > 35:
                risk_flag = "Concentrated"
                risk_alerts.append(f"{holding.symbol} exceeds 35% of portfolio weight.")
            elif pnl_pct < -12:
                risk_flag = "Drawdown"
                risk_alerts.append(f"{holding.symbol} is down more than 12% from average cost.")
            enriched_holdings.append(PortfolioHoldingAnalysis(symbol=holding.symbol, sector=sector, weight=weight, pnl_pct=pnl_pct, risk_flag=risk_flag))

        sector_exposure = {sector: round((value / total_value) * 100, 2) for sector, value in sector_value.items()}
        diversification_score = round(max(0.0, 100 - max(sector_exposure.values(), default=0) * 1.2 - len(risk_alerts) * 6), 2)
        if len(sector_exposure) < 3:
            risk_alerts.append("Portfolio has exposure to fewer than 3 sectors.")

        dominant_sector = max(sector_exposure, key=sector_exposure.get)
        summary = f"Portfolio diversification score is {diversification_score}/100 with the highest exposure in {dominant_sector} at {sector_exposure[dominant_sector]}%."
        eli5 = None
        if explain_like_im_5:
            eli5 = f"Most of your money sits in {dominant_sector}. A safer basket usually spreads money across more kinds of companies so one bad day hurts less."

        return PortfolioAnalysisResponse(
            diversification_score=diversification_score,
            sector_exposure=sector_exposure,
            risk_alerts=sorted(set(risk_alerts)),
            holdings=enriched_holdings,
            summary=summary,
            explain_like_im_5=eli5,
        )
