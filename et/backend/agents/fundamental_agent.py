


"""
fundamental_agent.py  — UPGRADED
Replaces the original 52-week-range-only scoring with real Indian fundamentals:
P/E, EPS, Market Cap, P/B ratio, Dividend Yield, and Promoter Holding.
Drop this at: backend/agents/fundamental_agent.py
"""
from __future__ import annotations

from backend.models.schemas import AgentSignal
from backend.services.indian_market_service import IndianMarketService


# ── Sector-aware P/E benchmarks (NSE India norms) ────────────────────────────
SECTOR_PE_BENCHMARKS: dict[str, float] = {
    "Technology": 28.0,
    "Financial Services": 18.0,
    "Banking": 14.0,
    "Consumer Cyclical": 30.0,
    "Consumer Defensive": 40.0,
    "Healthcare": 25.0,
    "Energy": 12.0,
    "Utilities": 14.0,
    "Basic Materials": 15.0,
    "Industrials": 22.0,
    "Real Estate": 20.0,
    "Communication Services": 20.0,
    "Unknown": 22.0,   # market average proxy
}


def _sector_pe(sector: str) -> float:
    for key in SECTOR_PE_BENCHMARKS:
        if key.lower() in sector.lower():
            return SECTOR_PE_BENCHMARKS[key]
    return SECTOR_PE_BENCHMARKS["Unknown"]


class FundamentalAgent:
    def __init__(self) -> None:
        self.indian_market = IndianMarketService()

    def analyze(self, symbol: str) -> AgentSignal:
        quote = self.indian_market.fetch_indian_quote(symbol)
        score = 0.0
        key_points: list[str] = []
        sources = list(quote.sources)

        # ── 1. Price context ─────────────────────────────────────────────────
        key_points.append(
            f"CMP: Rs. {quote.price} | Daily move: {quote.change_pct:+.2f}%"
        )

        # ── 2. 52-week range position ─────────────────────────────────────────
        if quote.high_52w and quote.low_52w and quote.high_52w != quote.low_52w:
            range_pos = (quote.price - quote.low_52w) / (quote.high_52w - quote.low_52w)
            score += round((range_pos * 2) - 1, 2) * 0.25   # 25% of total score
            band_label = (
                "upper third of 52-week range (momentum territory)"
                if range_pos > 0.66
                else "lower third of 52-week range (value zone)"
                if range_pos < 0.33
                else "mid-range"
            )
            key_points.append(
                f"52W range Rs. {quote.low_52w}–{quote.high_52w} | "
                f"Price is in {band_label} ({range_pos * 100:.0f}th percentile)."
            )

        # ── 3. P/E vs sector benchmark ───────────────────────────────────────
        if quote.pe_ratio:
            benchmark = _sector_pe(quote.sector)
            pe_discount = (benchmark - quote.pe_ratio) / benchmark   # positive = cheaper
            score += round(pe_discount * 0.35, 3)   # 35% of total score

            if quote.pe_ratio < benchmark * 0.8:
                pe_label = f"attractively valued vs {quote.sector} peers (benchmark P/E ~{benchmark:.0f}x)"
            elif quote.pe_ratio > benchmark * 1.25:
                pe_label = f"trading at a premium to {quote.sector} peers (benchmark P/E ~{benchmark:.0f}x)"
            else:
                pe_label = f"fairly valued vs {quote.sector} peers (benchmark P/E ~{benchmark:.0f}x)"
            key_points.append(f"P/E: {quote.pe_ratio:.1f}x — {pe_label}.")
        else:
            key_points.append("P/E ratio not available (may be loss-making or unlisted segment).")

        # ── 4. EPS quality ───────────────────────────────────────────────────
        if quote.eps_ttm:
            if quote.eps_ttm > 0:
                score += 0.10
                key_points.append(f"EPS (TTM): Rs. {quote.eps_ttm:.2f} — company is profitable.")
            else:
                score -= 0.15
                key_points.append(f"EPS (TTM): Rs. {quote.eps_ttm:.2f} — currently loss-making, watch next quarter.")

        # ── 5. Market cap category ───────────────────────────────────────────
        if quote.market_cap_cr:
            if quote.market_cap_cr >= 20_000:
                cap_label = "Large-cap"
                score += 0.05   # stability premium
            elif quote.market_cap_cr >= 5_000:
                cap_label = "Mid-cap"
            else:
                cap_label = "Small-cap"
                score -= 0.05  # liquidity risk
            key_points.append(
                f"Market cap: Rs. {quote.market_cap_cr:,.0f} Cr ({cap_label})."
            )

        # ── 6. P/B ratio ─────────────────────────────────────────────────────
        if quote.pb_ratio:
            if quote.pb_ratio < 1.5:
                score += 0.08
                key_points.append(f"P/B: {quote.pb_ratio:.2f}x — trading near book value (value signal).")
            elif quote.pb_ratio > 5.0:
                score -= 0.05
                key_points.append(f"P/B: {quote.pb_ratio:.2f}x — significant premium to book value.")
            else:
                key_points.append(f"P/B: {quote.pb_ratio:.2f}x.")

        # ── 7. Dividend yield ────────────────────────────────────────────────
        if quote.div_yield_pct and quote.div_yield_pct > 0:
            score += min(quote.div_yield_pct * 0.02, 0.06)   # max +0.06 bonus
            key_points.append(f"Dividend yield: {quote.div_yield_pct:.2f}% (income support).")

        # ── 8. Promoter holding ──────────────────────────────────────────────
        if quote.promoter_holding_pct:
            if quote.promoter_holding_pct >= 50:
                score += 0.05
                key_points.append(
                    f"Promoter holding: {quote.promoter_holding_pct:.1f}% — strong insider conviction."
                )
            elif quote.promoter_holding_pct < 20:
                score -= 0.05
                key_points.append(
                    f"Promoter holding: {quote.promoter_holding_pct:.1f}% — low insider stake, watch for dilution."
                )
            else:
                key_points.append(f"Promoter holding: {quote.promoter_holding_pct:.1f}%.")

        # ── Clamp score to [-1, 1] ────────────────────────────────────────────
        score = max(-1.0, min(1.0, round(score, 3)))

        return AgentSignal(
            agent="fundamental",
            summary=(
                f"Fundamental analysis for {symbol}: "
                f"P/E {quote.pe_ratio or 'N/A'}, "
                f"EPS Rs.{quote.eps_ttm or 'N/A'}, "
                f"Mkt cap Rs.{quote.market_cap_cr or 'N/A'} Cr, "
                f"sector {quote.sector}."
            ),
            score=score,
            key_points=key_points,
            sources=sources,
        )