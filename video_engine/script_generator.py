from __future__ import annotations

from backend.models.schemas import VideoRequest
from backend.services.flow_service import FlowService
from backend.services.llm_service import LLMService
from backend.services.market_data_service import MarketDataService
from backend.services.news_service import NewsService


SCRIPT_SYSTEM_PROMPT = """
You are a financial news anchor writing a crisp Indian market video script.
Create a 30 to 90 second narration with:
1. Nifty and Sensex movement
2. Top gainers and losers
3. Key market news
4. FII/DII activity
The script should sound natural, energetic, and suitable for subtitles.
"""


def generate_market_script(payload: VideoRequest) -> tuple[str, dict]:
    market_data = MarketDataService()
    news_service = NewsService()
    flow_service = FlowService()
    llm = LLMService()

    indices = market_data.fetch_index_summary()
    movers = market_data.top_movers(["RELIANCE.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS", "LT.NS", "SBIN.NS"])
    headlines = news_service.fetch_news("Nifty OR Sensex OR India stock market", limit=4)
    flow = flow_service.fetch_flow_snapshot()

    prompt = (
        f"Date: {payload.market_date or 'latest trading session'}\n"
        f"Nifty: {indices['^NSEI']}\n"
        f"Sensex: {indices['^BSESN']}\n"
        f"Gainers: {movers['gainers']}\n"
        f"Losers: {movers['losers']}\n"
        f"Headlines: {[item.title for item in headlines]}\n"
        f"Flows: {flow}\n"
        f"Duration target: {payload.duration_seconds} seconds\n"
    )
    script = llm.complete_text(SCRIPT_SYSTEM_PROMPT, prompt)
    if "Nifty" not in script:
        script = (
            f"Nifty closed at {indices['^NSEI'].price} while Sensex ended at {indices['^BSESN'].price}. "
            f"Leading gainers included {', '.join(item.symbol for item in movers['gainers'])}, while the weaker names were {', '.join(item.symbol for item in movers['losers'])}. "
            f"Key headlines were {'; '.join(item.title for item in headlines[:2])}. "
            f"Foreign investors posted Rs. {flow['fii_net_cr']} crore versus domestic flows of Rs. {flow['dii_net_cr']} crore."
        )
    return script, {"indices": indices, "movers": movers, "headlines": headlines, "flow": flow}
