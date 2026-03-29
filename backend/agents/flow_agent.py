"""
flow_agent.py — UPGRADED
Uses IndianMarketService to fetch real NSE FII/DII data.
Drop this at: backend/agents/flow_agent.py
"""
from __future__ import annotations

from backend.models.schemas import AgentSignal
from backend.services.indian_market_service import IndianMarketService


class FlowAgent:
    def __init__(self) -> None:
        self.indian_market = IndianMarketService()

    def analyze(self) -> AgentSignal:
        flow = self.indian_market.fetch_fii_dii_flow()

        fii = flow.fii_net_cr
        dii = flow.dii_net_cr
        combined = fii + dii

        # Score: both flows positive = bullish (+0.8 max)
        # Both negative = bearish (-0.8 max)
        # Mixed = muted
        if fii > 0 and dii > 0:
            score = min(0.8, round((combined / 5000) * 0.8, 3))
        elif fii < 0 and dii < 0:
            score = max(-0.8, round((combined / 5000) * 0.8, 3))
        else:
            # Divergence — use FII as primary driver (FII weight 70%)
            score = round((fii * 0.7 + dii * 0.3) / 5000, 3)
            score = max(-0.5, min(0.5, score))

        fii_arrow = "▲" if fii >= 0 else "▼"
        dii_arrow = "▲" if dii >= 0 else "▼"

        key_points = [
            f"FII net flow ({flow.date}): {fii_arrow} Rs. {abs(fii):,.2f} Cr "
            f"({'buying' if fii >= 0 else 'selling'}).",
            f"DII net flow ({flow.date}): {dii_arrow} Rs. {abs(dii):,.2f} Cr "
            f"({'buying' if dii >= 0 else 'selling'}).",
        ]

        if fii > 1000:
            key_points.append("Strong FII buying — foreign confidence in Indian equities is high.")
        elif fii < -1000:
            key_points.append("Heavy FII selling — foreign outflows may pressure index levels.")

        if dii > 500 and fii < 0:
            key_points.append("DII absorption of FII selling may provide a floor.")
        elif dii < -500 and fii < 0:
            key_points.append("Both FII and DII are net sellers — broad market weakness signal.")

        return AgentSignal(
            agent="flow",
            summary=(
                f"FII {fii_arrow} Rs.{fii:,.0f}Cr | DII {dii_arrow} Rs.{dii:,.0f}Cr "
                f"on {flow.date}. Source: {flow.source}."
            ),
            score=score,
            key_points=key_points,
            sources=[flow.source],
        )