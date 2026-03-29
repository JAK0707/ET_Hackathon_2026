from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from backend.services.market_data_service import MarketDataService


def create_market_charts(output_dir: str = "storage/video_assets") -> list[str]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    service = MarketDataService()
    chart_paths: list[str] = []

    nifty_history = service.fetch_recent_closes("^NSEI", days=10)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot([row["date"] for row in nifty_history], [row["close"] for row in nifty_history], marker="o", color="#0f766e")
    ax.set_title("Nifty 50: Last 10 Sessions")
    ax.set_ylabel("Close")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.25)
    chart_path = destination / "nifty_chart.png"
    fig.tight_layout()
    fig.savefig(chart_path, dpi=180)
    plt.close(fig)
    chart_paths.append(str(chart_path))

    movers = service.top_movers(["RELIANCE.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS", "LT.NS", "SBIN.NS"])
    gainers = movers["gainers"]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar([item.symbol.replace(".NS", "") for item in gainers], [item.change_pct for item in gainers], color="#f97316")
    ax.bar_label(bars, fmt="%.2f%%")
    ax.set_title("Top Gainers")
    ax.set_ylabel("Daily Change %")
    chart_path = destination / "top_gainers.png"
    fig.tight_layout()
    fig.savefig(chart_path, dpi=180)
    plt.close(fig)
    chart_paths.append(str(chart_path))

    return chart_paths
