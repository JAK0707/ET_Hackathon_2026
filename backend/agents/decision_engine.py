from __future__ import annotations

from backend.models.schemas import AgentSignal, DecisionPayload
from backend.services.llm_service import LLMService


AGENT_WEIGHTS = {
    "fundamental": 0.35,
    "technical": 0.30,
    "news": 0.20,
    "flow": 0.15,
}

DECISION_SYSTEM_PROMPT = """
You are MarketMind AI, a strict Indian equity research engine used by professional analysts.

Return ONLY valid JSON with exactly these keys: verdict, confidence, reasons, risks.

RULES YOU MUST FOLLOW:
- verdict must be exactly BUY, HOLD, or SELL — nothing else
- confidence must be exactly High, Medium, or Low
- reasons: 2-3 short, specific, action-oriented bullet points (why this verdict)
- risks: 2-3 short, specific risks the investor must know

DECISION LOGIC:
- Weighted composite score > 0.35 → lean BUY
- Weighted composite score < -0.35 → lean SELL
- Between -0.35 and 0.35 → lean HOLD
- If portfolio has HIGH concentration in this stock (>30%) → penalize, avoid BUY
- If FII flow is strongly negative → add caution even on BUY
- Avoid generic phrases like "market conditions" or "do your research"
- Be decisive. A clear HOLD is better than a vague BUY with 5 caveats.

CONFIDENCE RULES:
- High: abs(score) > 0.6 AND signals agree
- Medium: abs(score) between 0.3-0.6 OR signals disagree
- Low: abs(score) < 0.3 OR data is incomplete
"""


class DecisionEngine:
    def __init__(self) -> None:
        self.llm = LLMService()

    def decide(
    self,
    symbol: str,
    agent_signals: list[AgentSignal],
    portfolio_summary: str,
    rag_context: list[str],
    ) -> DecisionPayload:

    # ── Step 1: Weighted score ─────────────────────────────
        weighted_score = 0.0
        total_weight = 0.0
   
        for signal in agent_signals:
            weight = AGENT_WEIGHTS.get(signal.agent, 0.25)
            weighted_score += signal.score * weight
            total_weight += weight

        if total_weight > 0:
            weighted_score /= total_weight

    # ── Step 2: Signal agreement logic ─────────────────────
        positive = sum(1 for s in agent_signals if s.score > 0.2)
        negative = sum(1 for s in agent_signals if s.score < -0.2)

    # ── Step 3: Portfolio penalty ──────────────────────────
        portfolio_lower = portfolio_summary.lower()
        symbol_base = symbol.replace(".NS", "").replace(".BO", "").lower()

        high_concentration = False
        if symbol_base in portfolio_lower and (
            "high exposure" in portfolio_lower
            or "exceeds 30%" in portfolio_lower
            or "exceeds 35%" in portfolio_lower
        ):
            weighted_score -= 0.2
            high_concentration = True

    # ── Step 4: Fundamental override (VERY IMPORTANT) ──────
        signal_map = {s.agent: s for s in agent_signals}
        fundamental = signal_map.get("fundamental")

        fundamental_override = False
        if fundamental and fundamental.score < -0.7:
            fundamental_override = True

        technical = signal_map.get("technical")
        if technical and technical.score < -0.5:
            weighted_score -= 0.2

    # ── Step 5: Final verdict logic ────────────────────────
        if fundamental_override:
            if weighted_score > 0:
                pre_verdict = "HOLD"
            else:
                pre_verdict = "SELL"

        else:
            if positive >= 3 and weighted_score > 0.2:
                pre_verdict = "BUY"
            elif negative >= 3 and weighted_score < -0.2:
                pre_verdict = "SELL"
            elif weighted_score > 0.25:
                pre_verdict = "BUY"
            elif weighted_score < -0.25:
                pre_verdict = "SELL"
            else:
                pre_verdict = "HOLD"

    # ── Step 6: Confidence logic ───────────────────────────
        abs_score = abs(weighted_score)

        if abs(weighted_score) > 0.5:
            pre_confidence = "High"
        elif abs(weighted_score) > 0.2:
            pre_confidence = "Medium"
        else:
            pre_confidence = "Low"

    # ── Step 7: Action output (NEW 🔥) ─────────────────────
        if pre_verdict == "BUY":
            action = "Consider buying with controlled allocation."
        elif pre_verdict == "SELL":
            action = "Avoid or reduce exposure."
        else:
            action = "Wait for clearer signals before taking action."

    # ── Step 8: Structured prompt ─────────────────────────
        
        news = signal_map.get("news")
        flow = signal_map.get("flow")

        structured_prompt = f"""
    Symbol: {symbol}

    Final decision (pre-computed): {pre_verdict}
    Confidence: {pre_confidence}
    Weighted score: {weighted_score:.3f}

    Signal agreement:
    - Positive signals: {positive}
    - Negative signals: {negative}
    - Fundamental override applied: {fundamental_override}

    --- FUNDAMENTAL ---
    Score: {f"{fundamental.score:.2f}" if fundamental else 'N/A'}
    {chr(10).join(fundamental.key_points) if fundamental else ''}

    --- TECHNICAL ---
    Score: {f"{technical.score:.2f}" if technical else 'N/A'}
    {chr(10).join(technical.key_points) if technical else ''}

    --- NEWS ---
    Score: {f"{news.score:.2f}" if news else 'N/A'}
    {chr(10).join(news.key_points[:2]) if news else ''}

    --- FLOW ---
    Score: {f"{flow.score:.2f}" if flow else 'N/A'}
    {chr(10).join(flow.key_points) if flow else ''}

    --- PORTFOLIO ---
    {portfolio_summary}

    --- CONTEXT ---
    {chr(10).join(rag_context) if rag_context else ''}

Explain WHY this decision makes sense. Keep it sharp and actionable.
"""

    # ── Step 9: LLM explanation ───────────────────────────
        llm_result = self.llm.complete_json(DECISION_SYSTEM_PROMPT, structured_prompt)

        print("🔥 DECISION ENGINE UPDATED VERSION RUNNING")
        print("Weighted Score:", weighted_score)
        print("Positive:", positive, "Negative:", negative)

    # ── Step 10: Final output ─────────────────────────────
        return DecisionPayload(
            verdict=pre_verdict,
            confidence=pre_confidence,
            reasons=llm_result.get("reasons", [
                f"Composite score {weighted_score:.2f} supports {pre_verdict}.",
                f"{positive} positive vs {negative} negative signals observed.",
                action,
            ]),
            risks=llm_result.get("risks", [
                "Conflicting signals may cause short-term volatility.",
                "Market sentiment can shift quickly with new data.",
            ]),
            data_sources=list(dict.fromkeys(
                source for signal in agent_signals for source in signal.sources
            )),


        )