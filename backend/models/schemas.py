from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Verdict = Literal["BUY", "HOLD", "SELL"]
Confidence = Literal["High", "Medium", "Low"]
IntentType = Literal["stock_analysis", "portfolio_advice", "market_summary"]


class HoldingInput(BaseModel):
    symbol: str = Field(..., description="Indian equity ticker such as TCS.NS")
    quantity: float = Field(..., gt=0)
    average_price: float = Field(..., gt=0)
    sector: str | None = None


class PortfolioRequest(BaseModel):
    holdings: list[HoldingInput]
    risk_profile: str = "moderate"
    explain_like_im_5: bool = False


class ChatRequest(BaseModel):
    message: str
    holdings: list[HoldingInput] = Field(default_factory=list)
    explain_like_im_5: bool = False
    user_id: str | None = None


class AgentSignal(BaseModel):
    agent: str
    summary: str
    score: float
    key_points: list[str]
    sources: list[str] = Field(default_factory=list)

class Citation(BaseModel):
    id: int
    label: str
    source: str
    agent: str


class DecisionPayload(BaseModel):
    verdict: Verdict
    confidence: Confidence
    reasons: list[str]
    risks: list[str]
    data_sources: list[str]


class StockAnalysisResponse(BaseModel):
    intent: IntentType
    symbol: str | None = None
    market_summary: str
    decision: DecisionPayload
    agent_signals: list[AgentSignal]
    rag_context: list[str] = Field(default_factory=list)
    agent_steps: list[str] = Field(default_factory=list)
    explain_like_im_5: str | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    citations: list[Citation] = []


class PortfolioHoldingAnalysis(BaseModel):
    symbol: str
    sector: str
    weight: float
    pnl_pct: float
    risk_flag: str


class PortfolioAnalysisResponse(BaseModel):
    diversification_score: float
    sector_exposure: dict[str, float]
    risk_alerts: list[str]
    holdings: list[PortfolioHoldingAnalysis]
    summary: str
    explain_like_im_5: str | None = None


class VideoRequest(BaseModel):
    market_date: str | None = None
    duration_seconds: int = Field(default=60, ge=30, le=90)
    include_subtitles: bool = True


class VideoResponse(BaseModel):
    script: str
    audio_path: str
    chart_paths: list[str]
    video_path: str
    scheduled: bool = False