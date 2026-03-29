"""
orchestrator.py — UPGRADED
Key changes:
  1. Collects citations from every agent and the decision engine.
  2. Injects persisted user portfolio from DB into every chat (portfolio memory).
  3. Uses IndianMarketService for market summary (real NSE data).
  4. Richer agent_steps for agentic architecture demo.
Drop this at: backend/orchestrator.py  (or wherever your original lives)
"""
from __future__ import annotations

from backend.agents.decision_engine import DecisionEngine
from backend.agents.flow_agent import FlowAgent
from backend.agents.fundamental_agent import FundamentalAgent
from backend.agents.intent_agent import IntentAgent
from backend.agents.news_agent import NewsAgent
from backend.agents.technical_agent import TechnicalAgent
from backend.config import get_settings
from backend.models.schemas import ChatRequest, StockAnalysisResponse
from backend.services.indian_market_service import IndianMarketService
from backend.services.llm_service import LLMService
from backend.services.portfolio_service import PortfolioService
from backend.services.rag_service import SimpleRAGService
from backend.services.session_portfolio_service import SessionPortfolioService


# ── Symbol alias map (unchanged from original) ───────────────────────────────
INDIAN_STOCK_ALIASES: dict[str, str] = {
    "tcs": "TCS.NS", "reliance": "RELIANCE.NS", "ril": "RELIANCE.NS",
    "infy": "INFY.NS", "infosys": "INFY.NS", "hdfcbank": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS", "hdfc": "HDFCBANK.NS", "icicibank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS", "sbin": "SBIN.NS", "sbi": "SBIN.NS",
    "state bank": "SBIN.NS", "wipro": "WIPRO.NS", "hcltech": "HCLTECH.NS",
    "hcl": "HCLTECH.NS", "bajfinance": "BAJFINANCE.NS", "bajaj finance": "BAJFINANCE.NS",
    "bhartiartl": "BHARTIARTL.NS", "airtel": "BHARTIARTL.NS",
    "bharti": "BHARTIARTL.NS", "kotakbank": "KOTAKBANK.NS", "kotak": "KOTAKBANK.NS",
    "ltim": "LTIM.NS", "lti": "LTIM.NS", "mindtree": "LTIM.NS",
    "lt": "LT.NS", "larsen": "LT.NS", "l&t": "LT.NS",
    "axisbank": "AXISBANK.NS", "axis bank": "AXISBANK.NS", "axis": "AXISBANK.NS",
    "asianpaint": "ASIANPAINT.NS", "asian paints": "ASIANPAINT.NS",
    "maruti": "MARUTI.NS", "maruti suzuki": "MARUTI.NS", "msil": "MARUTI.NS",
    "titan": "TITAN.NS", "nestleind": "NESTLEIND.NS", "nestle": "NESTLEIND.NS",
    "sunpharma": "SUNPHARMA.NS", "sun pharma": "SUNPHARMA.NS",
    "drreddy": "DRREDDY.NS", "dr reddy": "DRREDDY.NS", "cipla": "CIPLA.NS",
    "techm": "TECHM.NS", "tech mahindra": "TECHM.NS",
    "ultracemco": "ULTRACEMCO.NS", "ultratech": "ULTRACEMCO.NS",
    "hindalco": "HINDALCO.NS", "tatasteel": "TATASTEEL.NS",
    "tata steel": "TATASTEEL.NS", "tatamotors": "TATAMOTORS.NS",
    "tata motors": "TATAMOTORS.NS", "tatacons": "TATACONSUM.NS",
    "tata consumer": "TATACONSUM.NS", "powergrid": "POWERGRID.NS",
    "power grid": "POWERGRID.NS", "ntpc": "NTPC.NS", "ongc": "ONGC.NS",
    "coalindia": "COALINDIA.NS", "coal india": "COALINDIA.NS",
    "indusindbk": "INDUSINDBK.NS", "indusind": "INDUSINDBK.NS",
    "bajajfinsv": "BAJAJFINSV.NS", "bajaj finserv": "BAJAJFINSV.NS",
    "jswsteel": "JSWSTEEL.NS", "jsw steel": "JSWSTEEL.NS",
    "grasim": "GRASIM.NS", "adaniports": "ADANIPORTS.NS",
    "adani ports": "ADANIPORTS.NS", "adanient": "ADANIENT.NS",
    "adani enterprises": "ADANIENT.NS", "adani": "ADANIENT.NS",
    "bpcl": "BPCL.NS", "ioc": "IOC.NS", "indian oil": "IOC.NS",
    "hpcl": "HPCL.NS", "eichermot": "EICHERMOT.NS", "eicher": "EICHERMOT.NS",
    "royal enfield": "EICHERMOT.NS", "hero": "HEROMOTOCO.NS",
    "heromotoco": "HEROMOTOCO.NS", "bajaj auto": "BAJAJ-AUTO.NS",
    "bajajauto": "BAJAJ-AUTO.NS", "divislab": "DIVISLAB.NS", "divis": "DIVISLAB.NS",
    "apollohosp": "APOLLOHOSP.NS", "apollo": "APOLLOHOSP.NS",
    "sbilife": "SBILIFE.NS", "hdfclife": "HDFCLIFE.NS",
    "icicipruli": "ICICIPRULI.NS", "pidilitind": "PIDILITIND.NS",
    "pidilite": "PIDILITIND.NS", "dabur": "DABUR.NS",
    "britannia": "BRITANNIA.NS", "colpal": "COLPAL.NS", "colgate": "COLPAL.NS",
    "havells": "HAVELLS.NS", "voltas": "VOLTAS.NS", "zomato": "ZOMATO.NS",
    "nykaa": "NYKAA.NS", "paytm": "PAYTM.NS",
    "policybazaar": "POLICYBZR.NS", "dmart": "DMART.NS",
    "avenue supermarts": "DMART.NS",
}


def _collect_citations(signals: list, decision) -> list[dict]:
    """
    Build a flat citations list from all agent signals + decision sources.
    Each citation: { id, label, source, agent }
    """
    seen: set[str] = set()
    citations: list[dict] = []
    cid = 1
    for signal in signals:
        for src in signal.sources:
            if src and src not in seen:
                seen.add(src)
                citations.append({
                    "id": cid,
                    "label": f"[{cid}]",
                    "source": src,
                    "agent": signal.agent,
                })
                cid += 1
    if hasattr(decision, "data_sources"):
        for src in decision.data_sources:
            if src and src not in seen:
                seen.add(src)
                citations.append({
                    "id": cid,
                    "label": f"[{cid}]",
                    "source": src,
                    "agent": "decision",
                })
                cid += 1
    return citations


class MarketMindOrchestrator:
    def __init__(self) -> None:
        settings = get_settings()
        self.intent_agent = IntentAgent()
        self.fundamental_agent = FundamentalAgent()
        self.technical_agent = TechnicalAgent()
        self.news_agent = NewsAgent()
        self.flow_agent = FlowAgent()
        self.decision_engine = DecisionEngine()
        self.indian_market = IndianMarketService()
        self.portfolio_service = PortfolioService()
        self.session_portfolio = SessionPortfolioService()   # NEW: persistent memory
        self.llm = LLMService()
        self.rag = SimpleRAGService(str(settings.vector_store_dir))

    # ── RAG seeding ───────────────────────────────────────────────────────────

    def seed_rag(self, symbol: str, news_points: list[str]) -> None:
        docs = [p for p in news_points if p]
        meta = [f"{symbol}-headline-{i+1}" for i in range(len(docs))]
        if docs:
            self.rag.add_documents(docs, meta)

    # ── Main entry point ──────────────────────────────────────────────────────

    def analyze(self, payload: ChatRequest) -> StockAnalysisResponse:
        # ── Step 1: Intent detection ──────────────────────────────────────────
        intent = self.intent_agent.detect(payload.message)
        symbol = self._extract_symbol(payload.message)

        # ── Step 2: Portfolio — merge live payload + persisted holdings ────────
        persisted_holdings = self.session_portfolio.load(payload.user_id or "default")
        merged_holdings = list(payload.holdings or [])
        existing_symbols = {h.get("symbol") for h in merged_holdings}
        for h in persisted_holdings:
            if h.get("symbol") not in existing_symbols:
                merged_holdings.append(h)

        # Persist any new holdings sent in this request
        if payload.holdings:
            self.session_portfolio.save(payload.user_id or "default", payload.holdings)

        portfolio = self.portfolio_service.analyze(
            merged_holdings, explain_like_im_5=payload.explain_like_im_5
        )

        # ── Market summary path ───────────────────────────────────────────────
        if intent == "market_summary":
            flow_signal = self.flow_agent.analyze()
            summary = self._market_summary_text()
            decision = self.decision_engine.decide(
                symbol="^NSEI",
                agent_signals=[flow_signal],
                portfolio_summary=portfolio.summary,
                rag_context=[],
            )
            citations = _collect_citations([flow_signal], decision)
            return StockAnalysisResponse(
                intent=intent,
                symbol="^NSEI",
                market_summary=summary,
                decision=decision,
                agent_signals=[flow_signal],
                rag_context=[],
                citations=citations,
                agent_steps=[
                    "Step 1: Intent classified → market_summary",
                    "Step 2: FII/DII institutional flow fetched from NSE India API",
                    "Step 3: Decision engine evaluated flow signal",
                    f"Step 4: {len(citations)} source citations compiled",
                ],
                explain_like_im_5=(
                    "The market is like a big report card for many companies together."
                    if payload.explain_like_im_5 else None
                ),
            )

        # ── Stock analysis path ───────────────────────────────────────────────
        # Step 3: Run all 4 agents sequentially (agentic chain — no human input)
        fundamental_signal = self.fundamental_agent.analyze(symbol)
        technical_signal = self.technical_agent.analyze(symbol)
        news_signal = self.news_agent.analyze(symbol)
        flow_signal = self.flow_agent.analyze()
        signals = [fundamental_signal, technical_signal, news_signal, flow_signal]

        # Step 4: Seed RAG + retrieve context
        self.seed_rag(symbol, news_signal.key_points)
        rag_context = self.rag.retrieve(
            f"{symbol} outlook latest filing sentiment", top_k=3
        )

        # Step 5: Decision
        decision = self.decision_engine.decide(symbol, signals, portfolio.summary, rag_context)

        # Step 6: Compile citations
        citations = _collect_citations(signals, decision)

        summary = self._compose_summary(symbol, signals, decision, portfolio.summary, citations)

        eli5 = None
        if payload.explain_like_im_5:
            eli5 = (
                f"For {symbol}, the charts look "
                f"{'strong' if signals[1].score > 0 else 'mixed'}, "
                f"the news feels {'helpful' if signals[2].score >= 0 else 'worrying'}, "
                f"so the final idea is to {decision.verdict.lower()}."
            )

        return StockAnalysisResponse(
            intent=intent,
            symbol=symbol,
            market_summary=summary,
            decision=decision,
            agent_signals=signals,
            rag_context=rag_context,
            citations=citations,
            agent_steps=[
                f"Step 1: Intent classified → stock_analysis for {symbol}",
                f"Step 2: Fundamental agent → P/E, EPS, mkt-cap fetched (score {fundamental_signal.score:+.2f})",
                f"Step 3: Technical agent → RSI/MACD/S-R analysed (score {technical_signal.score:+.2f})",
                f"Step 4: News agent → sentiment scored (score {news_signal.score:+.2f})",
                f"Step 5: Flow agent → FII/DII snapshot fetched (score {flow_signal.score:+.2f})",
                f"Step 6: RAG context retrieved → {len(rag_context)} snippets",
                f"Step 7: Decision engine → {decision.verdict} ({decision.confidence} confidence)",
                f"Step 8: Citations compiled → {len(citations)} sources tagged",
            ],
            explain_like_im_5=eli5,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_symbol(self, message: str) -> str:
        tokens = message.replace(",", " ").split()
        for token in tokens:
            upper = token.upper()
            if upper.endswith(".NS") or upper.endswith(".BO") or upper.startswith("^"):
                return upper
        lowered = message.lower()
        for alias in sorted(INDIAN_STOCK_ALIASES.keys(), key=len, reverse=True):
            if alias in lowered:
                return INDIAN_STOCK_ALIASES[alias]
        return "TCS.NS"

    def _compose_summary(
        self, symbol: str, signals: list, decision, portfolio_summary: str, citations: list
    ) -> str:
        cite_str = " ".join(c["label"] for c in citations[:4])
        signal_summary = " ".join(s.summary for s in signals)
        return (
            f"{symbol} analysis blends fundamentals, technicals, news, and institutional flow {cite_str}. "
            f"{signal_summary} Portfolio context: {portfolio_summary} "
            f"Verdict: {decision.verdict} ({decision.confidence} confidence)."
        )

    def _market_summary_text(self) -> str:
        try:
            nifty = self.indian_market.fetch_indian_quote("^NSEI")
            sensex = self.indian_market.fetch_indian_quote("^BSESN")
            movers = self.indian_market.fetch_top_movers(n=3)
            gainers = ", ".join(
                f"{q.nse_symbol} ({q.change_pct:+.2f}%)" for q in movers["gainers"]
            )
            losers = ", ".join(
                f"{q.nse_symbol} ({q.change_pct:+.2f}%)" for q in movers["losers"]
            )
            return (
                f"Nifty 50: {nifty.price:,.2f} ({nifty.change_pct:+.2f}%) | "
                f"Sensex: {sensex.price:,.2f} ({sensex.change_pct:+.2f}%). "
                f"Top gainers: {gainers}. Top losers: {losers}."
            )
        except Exception:
            return "Market summary unavailable — please try again."
        
    print("🚀 REAL DECISION ENGINE RUNNING")