from __future__ import annotations

import time

import schedule

from backend.models.schemas import VideoRequest
from video_engine.video_builder import build_market_video


def start_daily_video_scheduler(run_time: str = "18:30") -> None:
    schedule.every().day.at(run_time).do(lambda: build_market_video(VideoRequest()))
    while True:
        schedule.run_pending()
        time.sleep(30)
