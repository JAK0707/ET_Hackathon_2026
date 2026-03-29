# MarketMind AI

MarketMind AI is a production-ready, GitHub-friendly starter for a portfolio-aware Indian market copilot plus an AI video generation engine. It combines FastAPI, a modular agent pipeline, a Next.js frontend, and an automated video workflow that turns market data into short updates for demos, hackathons, and recruiter showcases.

## 1. High-Level Architecture

```text
                                  +----------------------+
                                  |   Next.js Frontend   |
                                  | Chat UI + Dashboard  |
                                  +----------+-----------+
                                             |
                                             v
                                +------------+-------------+
                                |       FastAPI API        |
                                | /chat /portfolio /video  |
                                +------+---------+---------+
                                       |         |
                     +-----------------+         +-------------------+
                     v                                           v
        +------------+------------+                 +-------------+--------------+
        |   Market GPT Orchestrator|                 |    AI Video Engine         |
        | intent + multi-agent flow|                 | script + TTS + charts + MP4|
        +------+---------+---------+                 +------+-----------+----------+
               |         |                                  |           |
               v         v                                  v           v
     +---------+--+ +----+---------+              +---------+--+ +-----+--------+
     | Fundamental| | Technical    |              | Market Data | | Voice / FFmpeg|
     | Agent      | | Agent        |              | + News      | | MoviePy       |
     +------------+ +--------------+              +------------+ +--------------+
               |         |                                  ^
               +----+----+                                  |
                    v                                       |
             +------+--------+        +---------------------+------------------+
             | News + Flow   |        | PostgreSQL + Local TF-IDF Vector Store |
             | Agents        |        | users, holdings, chat logs, RAG docs   |
             +------+--------+        +-----------------------------------------+
                    |
                    v
             +------+--------+
             | Decision Engine|
             | BUY/HOLD/SELL  |
             +---------------+
```

## 2. Backend Implementation

1. Intent detection classifies prompts into stock analysis, portfolio advice, or market summary.
2. Fundamental, technical, news, and flow agents each emit scored signals with evidence.
3. Portfolio analysis computes diversification score, sector exposure, and risk alerts.
4. RAG stores recent headline snippets locally with TF-IDF retrieval.
5. Decision engine returns structured `BUY / HOLD / SELL` output and supports OpenAI fallback.

## 3. Video Engine

1. Gather benchmark moves, movers, news, and FII/DII activity.
2. Generate a 60-second script with an LLM or offline fallback.
3. Synthesize voice via ElevenLabs or gTTS.
4. Render charts and compose subtitles into an MP4 with MoviePy.

## 4. Frontend

The Next.js app provides a ChatGPT-style interface, portfolio insight card, and a one-click market video generator.

## 5. Run

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```
