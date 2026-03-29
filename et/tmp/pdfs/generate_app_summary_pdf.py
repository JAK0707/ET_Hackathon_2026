from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Frame, KeepInFrame, Paragraph
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_PATH = OUTPUT_DIR / "marketmind_app_summary.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=2,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=10.2,
            textColor=colors.HexColor("#111827"),
            spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=9.4,
            textColor=colors.HexColor("#374151"),
            spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=9.8,
            leftIndent=0,
            textColor=colors.HexColor("#111827"),
            spaceAfter=1,
        ),
    }


def bullet_list(items: list[str], style: ParagraphStyle) -> list[Paragraph]:
    return [Paragraph(f"- {item}", style) for item in items]


def section(title: str, content: list, styles: dict[str, ParagraphStyle]) -> list:
    return [Paragraph(title, styles["section"]), *content]


def add_header(c: canvas.Canvas, page_width: float, page_height: float) -> None:
    c.saveState()
    c.setFillColor(colors.HexColor("#e2e8f0"))
    c.roundRect(0.5 * inch, page_height - 1.6 * inch, page_width - inch, 1.0 * inch, 16, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(0.75 * inch, page_height - 0.98 * inch, "MarketMind AI")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(0.75 * inch, page_height - 1.23 * inch, "One-page repo summary")

    chip_text = "FastAPI + Next.js + video pipeline"
    chip_width = stringWidth(chip_text, "Helvetica-Bold", 8) + 16
    c.setFillColor(colors.HexColor("#0f766e"))
    c.roundRect(page_width - 0.75 * inch - chip_width, page_height - 1.18 * inch, chip_width, 0.28 * inch, 8, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(page_width - 0.75 * inch - chip_width + 8, page_height - 1.08 * inch, chip_text)
    c.restoreState()


def build_story(styles: dict[str, ParagraphStyle]) -> tuple[list, list]:
    left = []
    left.extend(
        section(
            "What It Is",
            [
                Paragraph(
                    "MarketMind AI is an Indian-market copilot app with a chat workflow, portfolio diagnostics, and an AI video generator. "
                    "The repo pairs a Next.js frontend with a FastAPI backend, modular analysis agents, and a video pipeline that creates narrated market updates.",
                    styles["body"],
                )
            ],
            styles,
        )
    )
    left.extend(
        section(
            "Who It's For",
            [
                Paragraph(
                    "Primary persona: Indian retail investors who want stock analysis and portfolio context, plus builders creating demos, hackathon projects, or recruiter showcases around that workflow.",
                    styles["body"],
                )
            ],
            styles,
        )
    )
    left.extend(
        section(
            "What It Does",
            bullet_list(
                [
                    "Runs a portfolio-aware chat flow for Indian stock questions through `POST /chat`.",
                    "Combines fundamental, technical, news, and institutional flow agents before returning a BUY/HOLD/SELL decision.",
                    "Supports market-summary requests using index quotes and top-mover data.",
                    "Analyzes holdings for diversification, sector exposure, drawdown, and concentration risk.",
                    "Offers an ELI5 mode for simpler explanations in chat and portfolio responses.",
                    "Generates a 30-90 second market video with script, TTS audio, charts, subtitles, and MP4 output.",
                ],
                styles["bullet"],
            ),
            styles,
        )
    )

    right = []
    right.extend(
        section(
            "How It Works",
            [
                Paragraph(
                    "<b>UI:</b> `frontend/app/page.tsx` renders Chat, Portfolio, and Video panels. "
                    "`frontend/lib/api.ts` posts JSON to the backend at `NEXT_PUBLIC_API_BASE_URL`.",
                    styles["small"],
                ),
                Paragraph(
                    "<b>API:</b> `backend/main.py` mounts `/chat`, `/portfolio/analyze`, `/generate-video`, and `/health` with CORS enabled.",
                    styles["small"],
                ),
                Paragraph(
                    "<b>Chat flow:</b> `MarketMindOrchestrator` detects intent, resolves a stock symbol, runs fundamental/technical/news/flow agents, seeds a TF-IDF RAG store, and passes signals into `DecisionEngine`.",
                    styles["small"],
                ),
                Paragraph(
                    "<b>Data/services:</b> `MarketDataService` uses `yfinance`; `NewsService` uses NewsAPI when configured, else Google News RSS; `LLMService` supports Groq, Gemini, or OpenAI with offline fallbacks.",
                    styles["small"],
                ),
                Paragraph(
                    "<b>Persistence:</b> SQLAlchemy reads `postgres_url`; config defaults to local SQLite `marketmind.db`, while `docker-compose.yml` defines a Postgres service. Vector snippets are stored under `storage/faiss`.",
                    styles["small"],
                ),
                Paragraph(
                    "<b>Video pipeline:</b> `/generate-video` calls `video_engine/video_builder.py`, which generates a script, converts it to speech, builds charts, overlays subtitles, and writes `storage/video_assets/market_update.mp4`.",
                    styles["small"],
                ),
            ],
            styles,
        )
    )
    right.extend(
        section(
            "How To Run",
            bullet_list(
                [
                    "Install backend deps: `pip install -r requirements.txt`",
                    "Create config: copy `.env.example` to `.env` and add API keys only if needed.",
                    "Start backend: `uvicorn backend.main:app --reload`",
                    "Start frontend in a second terminal: `cd frontend && npm install && npm run dev`",
                    "Open `http://localhost:3000`",
                ],
                styles["bullet"],
            ),
            styles,
        )
    )
    right.extend(
        section(
            "Not Found In Repo",
            [
                Paragraph(
                    "Auth/user accounts, deployment instructions beyond local/Docker setup, automated tests, and production monitoring details were not found in repo.",
                    styles["body"],
                )
            ],
            styles,
        )
    )
    return left, right


def generate_pdf() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    page_width, page_height = letter
    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=letter)

    add_header(c, page_width, page_height)

    margin_x = 0.62 * inch
    bottom = 0.55 * inch
    top = page_height - 1.78 * inch
    gutter = 0.3 * inch
    col_width = (page_width - (2 * margin_x) - gutter) / 2
    frame_height = top - bottom

    left_story, right_story = build_story(styles)

    left_box = KeepInFrame(col_width, frame_height, left_story, mode="shrink")
    right_box = KeepInFrame(col_width, frame_height, right_story, mode="shrink")

    left_frame = Frame(margin_x, bottom, col_width, frame_height, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    right_frame = Frame(margin_x + col_width + gutter, bottom, col_width, frame_height, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    left_frame.addFromList([left_box], c)
    right_frame.addFromList([right_box], c)

    c.save()


def verify_pdf() -> None:
    reader = PdfReader(str(OUTPUT_PATH))
    if len(reader.pages) != 1:
        raise RuntimeError(f"Expected 1 page, found {len(reader.pages)}")


if __name__ == "__main__":
    generate_pdf()
    verify_pdf()
    print(OUTPUT_PATH)
