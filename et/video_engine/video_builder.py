"""
video_builder.py — UPGRADED
New segments added:
  1. Animated race-bar chart for top NSE movers (matplotlib bar_h animation)
  2. FII/DII flow bar visualization segment
  3. Cleaner title card + closing card

Drop this at: backend/video_engine/video_builder.py
Requires: matplotlib, moviepy, gtts (all already in requirements.txt)
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
matplotlib.use("Agg")   # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

from backend.services.indian_market_service import IndianMarketService
from backend.services.llm_service import LLMService


OUTPUT_DIR = Path("./storage/video_assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "market_update.mp4"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

BRAND_COLOR = "#0f766e"
BG_COLOR = "#f8fafc"
TEXT_COLOR = "#0f172a"
GAIN_COLOR = "#16a34a"
LOSS_COLOR = "#dc2626"
FII_COLOR = "#1d4ed8"
DII_COLOR = "#b45309"


# ── Script generation ────────────────────────────────────────────────────────

def generate_script(market_summary: str, movers: dict, flow) -> str:
    llm = LLMService()
    prompt = f"""
Write a 60-second market update video script for Indian retail investors.
Use the data below. Be conversational, specific, and end with one clear takeaway.
Format: plain paragraphs only, no bullet points, no headers.

Market: {market_summary}
Top gainers: {', '.join(f"{q.nse_symbol} {q.change_pct:+.1f}%" for q in movers['gainers'][:3])}
Top losers: {', '.join(f"{q.nse_symbol} {q.change_pct:+.1f}%" for q in movers['losers'][:3])}
FII flow: Rs. {flow.fii_net_cr:,.0f} Cr ({'buying' if flow.fii_net_cr >= 0 else 'selling'})
DII flow: Rs. {flow.dii_net_cr:,.0f} Cr ({'buying' if flow.dii_net_cr >= 0 else 'selling'})
"""
    try:
        result = llm.complete(prompt)
        return result if isinstance(result, str) else str(result)
    except Exception:
        return (
            f"Good morning investors. Here's your market update. "
            f"{market_summary} "
            f"On the institutional front, FIIs were net {'buyers' if flow.fii_net_cr >= 0 else 'sellers'} "
            f"at Rs. {abs(flow.fii_net_cr):,.0f} crore. "
            "Stay diversified and invest wisely."
        )


# ── TTS ───────────────────────────────────────────────────────────────────────

def generate_audio(script: str, out_path: Path) -> Path:
    audio_path = out_path.with_suffix(".mp3")
    try:
        from elevenlabs import ElevenLabs
        api_key = os.getenv("ELEVENLABS_API_KEY", "")
        if api_key:
            client = ElevenLabs(api_key=api_key)
            audio = client.text_to_speech.convert(
                text=script,
                voice_id="Rachel",
                model_id="eleven_multilingual_v2",
            )
            with open(audio_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            return audio_path
    except Exception:
        pass

    # gTTS fallback
    from gtts import gTTS
    tts = gTTS(text=script, lang="en", tld="co.in")   # Indian English accent
    tts.save(str(audio_path))
    return audio_path


# ── Chart: animated race-bar for top movers ───────────────────────────────────

def make_race_bar_chart(movers: dict) -> Path:
    """
    Animated horizontal bar chart showing top gainers and losers.
    Bars grow from 0 to final value over 60 frames (~2 seconds at 30fps).
    """
    gainers = movers["gainers"][:5]
    losers = movers["losers"][:5]

    symbols = [q.nse_symbol.replace(".NS", "") for q in gainers + losers]
    values = [q.change_pct for q in gainers + losers]
    colors = [GAIN_COLOR if v >= 0 else LOSS_COLOR for v in values]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(symbols, [0] * len(symbols), color=colors, height=0.6)
    ax.set_xlim(min(values) * 1.4 - 0.5, max(values) * 1.4 + 0.5)
    ax.axvline(0, color=TEXT_COLOR, linewidth=0.8, alpha=0.4)
    ax.set_xlabel("Daily Change (%)", color=TEXT_COLOR, fontsize=11)
    ax.set_title("NSE Top Movers", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color("#cbd5e1")

    FRAMES = 45

    def animate(frame: int):
        progress = frame / FRAMES
        for bar, val in zip(bars, values):
            bar.set_width(val * progress)
        return bars

    ani = animation.FuncAnimation(fig, animate, frames=FRAMES + 10, interval=33, blit=True)

    out = CHARTS_DIR / "race_bar.mp4"
    writer = animation.FFMpegWriter(fps=30, bitrate=1800)
    ani.save(str(out), writer=writer, dpi=120)
    plt.close(fig)
    return out


# ── Chart: FII/DII flow bars ──────────────────────────────────────────────────

def make_flow_chart(flow) -> Path:
    """
    Side-by-side bar chart for FII buy/sell/net and DII buy/sell/net.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor(BG_COLOR)
    fig.suptitle(f"FII / DII Institutional Flow — {flow.date}",
                 color=TEXT_COLOR, fontsize=13, fontweight="bold")

    for ax, (name, buy, sell, net, color) in zip(axes, [
        ("FII", flow.fii_buy_cr, flow.fii_sell_cr, flow.fii_net_cr, FII_COLOR),
        ("DII", flow.dii_buy_cr, flow.dii_sell_cr, flow.dii_net_cr, DII_COLOR),
    ]):
        ax.set_facecolor(BG_COLOR)
        bars = ax.bar(["Buy", "Sell", "Net"], [buy, sell, net],
                      color=[GAIN_COLOR, LOSS_COLOR, color], width=0.5, alpha=0.85)
        ax.set_title(name, color=color, fontsize=12, fontweight="bold")
        ax.set_ylabel("Rs. Crore", color=TEXT_COLOR, fontsize=9)
        ax.tick_params(colors=TEXT_COLOR, labelsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color("#cbd5e1")
        ax.axhline(0, color="#cbd5e1", linewidth=0.8)
        for bar, val in zip(bars, [buy, sell, net]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + abs(max(buy, sell, net)) * 0.02,
                    f"{val:,.0f}", ha="center", va="bottom",
                    fontsize=8, color=TEXT_COLOR)

    plt.tight_layout()
    out = CHARTS_DIR / "fii_dii_flow.png"
    plt.savefig(str(out), dpi=120, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    return out


# ── Chart: title card ────────────────────────────────────────────────────────

def make_title_card(summary: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 3))
    fig.patch.set_facecolor(BRAND_COLOR)
    ax.set_facecolor(BRAND_COLOR)
    ax.axis("off")

    ax.text(0.5, 0.72, "MarketMind AI", transform=ax.transAxes,
            ha="center", va="center", fontsize=22, fontweight="bold", color="white")
    ax.text(0.5, 0.45, "Daily Market Update", transform=ax.transAxes,
            ha="center", va="center", fontsize=13, color="#a7f3d0")

    wrapped = "\n".join(textwrap.wrap(summary[:160], width=90))
    ax.text(0.5, 0.18, wrapped, transform=ax.transAxes,
            ha="center", va="center", fontsize=9, color="#e2e8f0")

    out = CHARTS_DIR / "title_card.png"
    plt.savefig(str(out), dpi=120, bbox_inches="tight", facecolor=BRAND_COLOR)
    plt.close(fig)
    return out


# ── Compose final video ───────────────────────────────────────────────────────

def compose_video(
    audio_path: Path,
    title_card: Path,
    race_bar_video: Path,
    flow_chart: Path,
) -> Path:
    """
    Stitch charts + audio into final MP4 using moviepy.
    """
    try:
        from moviepy.editor import (
            ImageClip, VideoFileClip, AudioFileClip,
            concatenate_videoclips, CompositeVideoClip,
        )

        audio = AudioFileClip(str(audio_path))
        total_duration = audio.duration

        # Title card: 4 seconds
        title_clip = ImageClip(str(title_card)).set_duration(4).resize((1280, 360))

        # Race bar video: up to 3 seconds or the clip's natural length
        race_clip = VideoFileClip(str(race_bar_video)).subclip(0, min(3, VideoFileClip(str(race_bar_video)).duration))
        race_clip = race_clip.resize((1280, 640))

        # Flow chart: rest of duration
        remaining = max(2, total_duration - 4 - race_clip.duration)
        flow_clip = ImageClip(str(flow_chart)).set_duration(remaining).resize((1280, 480))

        final = concatenate_videoclips([title_clip, race_clip, flow_clip], method="compose")
        final = final.set_audio(audio.subclip(0, final.duration))

        final.write_videofile(
            str(OUTPUT_PATH),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        return OUTPUT_PATH

    except Exception as e:
        # Fallback: title card only + audio as a static video
        try:
            from moviepy.editor import ImageClip, AudioFileClip
            audio = AudioFileClip(str(audio_path))
            clip = ImageClip(str(title_card)).set_duration(audio.duration).set_audio(audio)
            clip.write_videofile(str(OUTPUT_PATH), fps=24, codec="libx264",
                                 audio_codec="aac", logger=None)
        except Exception:
            pass
        return OUTPUT_PATH


# ── Main entry point ──────────────────────────────────────────────────────────

def build_market_video() -> str:
    """
    Full autonomous pipeline:
      1. Fetch market data (NSE via IndianMarketService)
      2. Generate LLM script
      3. TTS audio
      4. Build animated race-bar + FII/DII chart
      5. Compose MP4
    Returns: path to output video
    """
    indian = IndianMarketService()

    # 1. Data
    nifty = indian.fetch_indian_quote("^NSEI")
    sensex = indian.fetch_indian_quote("^BSESN")
    movers = indian.fetch_top_movers(n=5)
    flow = indian.fetch_fii_dii_flow()

    market_summary = (
        f"Nifty 50: {nifty.price:,.2f} ({nifty.change_pct:+.2f}%) | "
        f"Sensex: {sensex.price:,.2f} ({sensex.change_pct:+.2f}%)."
    )

    # 2. Script
    script = generate_script(market_summary, movers, flow)

    # 3. Audio
    audio_path = generate_audio(script, OUTPUT_DIR / "narration")

    # 4. Charts
    title_card = make_title_card(market_summary)
    flow_chart = make_flow_chart(flow)
    race_bar = make_race_bar_chart(movers)

    # 5. Compose
    out = compose_video(audio_path, title_card, race_bar, flow_chart)
    return str(out)


if __name__ == "__main__":
    path = build_market_video()
    print(f"Video saved to: {path}")