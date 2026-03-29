from __future__ import annotations

import numpy as np
import pandas as pd


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series]:
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd = ema_fast - ema_slow
    macd_signal = _ema(macd, signal)
    return macd, macd_signal


def _bollinger_bands(series: pd.Series, window: int = 20, std_multiplier: float = 2.0) -> tuple[pd.Series, pd.Series]:
    middle = _sma(series, window)
    deviation = series.rolling(window=window, min_periods=window).std()
    upper = middle + (deviation * std_multiplier)
    lower = middle - (deviation * std_multiplier)
    return upper, lower


def enrich_with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = enriched["Close"].astype(float)
    enriched["rsi_14"] = _rsi(close, window=14)
    enriched["macd"], enriched["macd_signal"] = _macd(close, fast=12, slow=26, signal=9)
    enriched["sma_20"] = _sma(close, window=20)
    enriched["sma_50"] = _sma(close, window=50)
    enriched["bb_upper"], enriched["bb_lower"] = _bollinger_bands(close, window=20, std_multiplier=2.0)
    return enriched.dropna().reset_index(drop=True)


def calculate_support_resistance(df: pd.DataFrame) -> tuple[float, float]:
    recent = df.tail(20)
    support = round(float(recent["Low"].min()), 2)
    resistance = round(float(recent["High"].max()), 2)
    return support, resistance


def trend_strength(df: pd.DataFrame) -> float:
    closes = df["Close"].tail(20).to_numpy(dtype=float)
    x = np.arange(len(closes))
    slope = np.polyfit(x, closes, deg=1)[0]
    baseline = closes.mean() if closes.size else 1.0
    return round(float((slope / baseline) * 100), 4)
