#!/usr/bin/env python3
"""
Gold Buy Signal Monitor
Run regularly (e.g. daily after US close or weekly).
Fetches approximate live data and scores a simple buy/wait suggestion.
Not financial advice — educational framework only.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

def get_latest_price(ticker, period="5d"):
    try:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            return None
        return float(data["Close"].iloc[-1])
    except Exception:
        return None

def get_gold_spot_approx():
    # GC=F is front-month COMEX gold futures (good proxy)
    return get_latest_price("GC=F")

def get_10y_yield():
    # ^TNX is the CBOE 10-Year Treasury Note Yield index (multiply by 10 for % if needed; yfinance usually gives it scaled)
    val = get_latest_price("^TNX")
    if val is not None:
        # ^TNX is typically quoted as 50.0 for 5.00%
        return val / 10.0 if val > 10 else val
    return None

def get_dxy():
    return get_latest_price("DX-Y.NYB")  # or "DX=F"

def score_signal(gold, yield_10y, dxy, gold_high_52w=None):
    score = 0
    reasons = []

    # 1. Yield environment (most important short-term)
    if yield_10y is not None:
        if yield_10y < 4.5:
            score += 2
            reasons.append(f"10y yield supportive ({yield_10y:.2f}%)")
        elif yield_10y < 4.8:
            score += 1
            reasons.append(f"10y yield neutral-ish ({yield_10y:.2f}%)")
        else:
            score -= 1
            reasons.append(f"10y yield elevated/headwind ({yield_10y:.2f}%)")

    # 2. Dollar
    if dxy is not None:
        if dxy < 98:
            score += 2
            reasons.append(f"DXY weak ({dxy:.1f})")
        elif dxy < 100:
            score += 1
            reasons.append(f"DXY neutral ({dxy:.1f})")
        else:
            score -= 1
            reasons.append(f"DXY firm ({dxy:.1f})")

    # 3. Price action / value
    if gold is not None and gold_high_52w:
        drawdown = (gold_high_52w - gold) / gold_high_52w
        if drawdown > 0.15:
            score += 1
            reasons.append(f"Gold >15% off recent high (value)")
        elif drawdown < 0.05:
            score -= 0.5
            reasons.append("Gold near highs (less attractive entry)")

    # 4. Simple momentum proxy (last few days) — can expand
    # (Left as placeholder; you can add RSI or MA checks)

    # Structural overlay (manual or extend with news)
    # For automation you could hard-code a positive bias if you believe the CB thesis
    # score += 1  # uncomment if you want permanent structural tilt

    return score, reasons

def main():
    print(f"=== Gold Entry Signal — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    gold = get_gold_spot_approx()
    y10 = get_10y_yield()
    dxy = get_dxy()

    # Rough 52-week high proxy (you can hard-code recent high ~5318 or fetch longer history)
    gold_hist = yf.download("GC=F", period="1y", progress=False, auto_adjust=True)
    if gold_hist.empty:
        high_52w = 5318.0
    else:
        # This works in almost all yfinance versions
        high_52w = float(gold_hist["High"].values.max())
    high_52w = float(gold_hist["High"].max()) if not gold_hist.empty else 5318

    print(f"Gold (GC=F proxy): ${gold:,.2f}" if gold else "Gold: N/A")
    print(f"10y Yield: {y10:.2f}%" if y10 else "10y: N/A")
    print(f"DXY: {dxy:.2f}" if dxy else "DXY: N/A")
    print(f"Approx 52w high: ${high_52w:,.0f}\n")

    score, reasons = score_signal(gold, y10, dxy, high_52w)

    print("Score components:")
    for r in reasons:
        print(f"  • {r}")
    print(f"\nNet score: {score:+.1f}")

    if score >= 3:
        suggestion = "STRONG — favorable conditions to start or add meaningfully (dca still recommended)."
    elif score >= 1:
        suggestion = "MODERATE — reasonable to begin small systematic buys / scale in on dips."
    elif score >= -1:
        suggestion = "NEUTRAL / WAIT — short-term headwinds (rates/dollar) still present. Watch for yield or DXY rollover."
    else:
        suggestion = "CAUTIOUS — elevated yields + firm dollar = higher chance of further pressure. Prefer waiting or very small positions only."

    print(f"\nSuggestion: {suggestion}")
    print("\nNotes:")
    print("- This is a simple mechanical overlay, not advice.")
    print("- Structural case (CB buying, debt, dollar weaponization) can override short-term signals — decide your own weight.")
    print("- Always size positions to your risk tolerance and consider physical vs. ETF vs. miners.")
    print("- Re-run after FOMC, major data, or big yield/DXY moves.")

if __name__ == "__main__":
    main()