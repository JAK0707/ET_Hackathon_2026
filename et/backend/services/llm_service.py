from __future__ import annotations

import json

from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import get_settings


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None
        self.provider = None

        if self.settings.groq_api_key:
            from groq import Groq
            self.client = Groq(api_key=self.settings.groq_api_key)
            self.provider = "groq"

        elif self.settings.gemini_api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.settings.gemini_api_key)
            self.client = genai.GenerativeModel("gemini-2.0-flash")
            self.provider = "gemini"

        elif self.settings.openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            self.provider = "openai"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if self.client is None:
            return self._fallback_response(user_prompt)

        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt + "\nRespond ONLY with valid JSON. No markdown, no explanation."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())

        if self.provider == "gemini":
            full_prompt = (
                f"{system_prompt}\n\n{user_prompt}\n\n"
                "Respond ONLY with a valid JSON object. No markdown, no explanation, no code fences."
            )
            response = self.client.generate_content(full_prompt)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())

        # OpenAI path
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.client is None:
            return "Today the Indian market stayed mixed, with benchmark indices reacting to banking strength, IT consolidation, and institutional flow signals."

        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()

        if self.provider == "gemini":
            response = self.client.generate_content(f"{system_prompt}\n\n{user_prompt}")
            return response.text.strip()

        # OpenAI path
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def _fallback_response(self, prompt: str) -> dict:
        verdict = "HOLD"
        if "bullish" in prompt.lower() or "oversold" in prompt.lower():
            verdict = "BUY"
        if "overvalued" in prompt.lower() or "bearish" in prompt.lower():
            verdict = "SELL"
        return {
            "verdict": verdict,
            "confidence": "Medium",
            "reasons": [
                "Fallback reasoning blended technical momentum, fundamentals, and current headlines.",
                "The model ran in offline mode because no API key was configured.",
            ],
            "risks": ["Validate results against current filings and broker research before trading."],
        }