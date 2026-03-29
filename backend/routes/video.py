from fastapi import APIRouter

from backend.models.schemas import VideoRequest, VideoResponse
from video_engine.video_builder import build_market_video


router = APIRouter(prefix="/generate-video", tags=["video"])


@router.post("", response_model=VideoResponse)
def generate_video(payload: VideoRequest) -> VideoResponse:
    return build_market_video(payload)
