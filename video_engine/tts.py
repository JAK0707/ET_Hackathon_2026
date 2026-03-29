from __future__ import annotations

from pathlib import Path

from gtts import gTTS

from backend.config import get_settings


def text_to_speech(script: str, output_dir: str = "storage/video_assets") -> str:
    settings = get_settings()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    audio_path = destination / "market_update.mp3"

    if settings.elevenlabs_api_key:
        try:
            from elevenlabs.client import ElevenLabs

            client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            audio = client.text_to_speech.convert(
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                output_format="mp3_44100_128",
                text=script,
                model_id="eleven_multilingual_v2",
            )
            with audio_path.open("wb") as file:
                for chunk in audio:
                    file.write(chunk)
            return str(audio_path)
        except Exception:
            if not settings.use_gtts_fallback:
                raise

    gTTS(text=script, lang="en", tld="co.in").save(str(audio_path))
    return str(audio_path)
