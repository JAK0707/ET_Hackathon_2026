from fastapi import APIRouter

from backend.models.schemas import PortfolioAnalysisResponse, PortfolioRequest
from backend.services.portfolio_service import PortfolioService


router = APIRouter(prefix="/portfolio", tags=["portfolio"])
service = PortfolioService()


@router.post("/analyze", response_model=PortfolioAnalysisResponse)
def analyze_portfolio(payload: PortfolioRequest) -> PortfolioAnalysisResponse:
    return service.analyze(payload.holdings, explain_like_im_5=payload.explain_like_im_5)
