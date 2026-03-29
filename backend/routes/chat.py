from fastapi import APIRouter

from backend.agents.orchestrator import MarketMindOrchestrator
from backend.models.schemas import ChatRequest, StockAnalysisResponse


router = APIRouter(prefix="/chat", tags=["chat"])
orchestrator = MarketMindOrchestrator()


@router.post("", response_model=StockAnalysisResponse)
def chat(payload: ChatRequest) -> StockAnalysisResponse:
    return orchestrator.analyze(payload)
