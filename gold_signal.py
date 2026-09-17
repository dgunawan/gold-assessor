#!/usr/bin/env python3
"""
Gold Buy Signal Monitor
Fixed version - handles yfinance Series/DataFrame properly
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

def get_latest_price(ticker, period="5d"):
    try:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            return None
        # Handle possible multi-index columns
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return float(close.iloc[-1])
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def get_gold_spot_approx():
    return get_latest_price("GC=F")

def get_10y_yield():
    val = get_latest_price("^TNX")
    if val is not None:
        # ^TNX is usually quoted as 50.0 meaning 5.00%
        return val / 10.0 if val > 10 else val
    return None

def get_dxy():
    return get_latest_price("DX-Y.NYB")

def score_signal(gold, yield_10y, dxy, gold_high_52w=None):
    score = 0.0
    reasons = []

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

    if gold is not None and gold_high_52w is not None:
        drawdown = (gold_high_52w - gold) / gold_high_52w
        if drawdown > 0.15:
            score += 1
            reasons.append(f"Gold >15% off recent high (value)")
        elif drawdown < 0.05:
            score -= 0.5
            reasons.append("Gold near highs (less attractive entry)")

    return score, reasons

def main():
    print(f"=== Gold Entry Signal — {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC ===\n")

    gold = get_gold_spot_approx()
    y10 = get_10y_yield()
    dxy = get_dxy()

    # Download 1 year of gold data
    gold_hist = yf.download("GC=F", period="1y", progress=False, auto_adjust=True)

    # Robust extraction of 52-week high
    if gold_hist.empty:
        high_52w = 5318.0
    else:
        high_col = gold_hist["High"]
        # Handle both Series and DataFrame (multi-index) cases
        if isinstance(high_col, pd.DataFrame):
            high_col = high_col.iloc[:, 0]
        high_52w = float(high_col.max())

    print(f"Gold (GC=F proxy): ${gold:,.2f}" if gold is not None else "Gold: N/A")
    print(f"10y Yield: {y10:.2f}%" if y10 is not None else "10y: N/A")
    print(f"DXY: {dxy:.2f}" if dxy is not None else "DXY: N/A")
    print(f"Approx 52w high: ${high_52w:,.0f}\n")

    score, reasons = score_signal(gold, y10, dxy, high_52w)

    print("Score components:")
    for r in reasons:
        print(f"  • {r}")
    print(f"\nNet score: {score:+.1f}")

    if score >= 3:
        suggestion = "STRONG — favorable conditions to start or add meaningfully (DCA still recommended)."
    elif score >= 1:
        suggestion = "MODERATE — reasonable to begin small systematic buys / scale in on dips."
    elif score >= -1:
        suggestion = "NEUTRAL / WAIT — short-term headwinds (rates/dollar) still present. Watch for yield or DXY rollover."
    else:
        suggestion = "CAUTIOUS — elevated yields + firm dollar = higher chance of further pressure. Prefer waiting or very small positions only."

    print(f"\nSuggestion: {suggestion}")
    print("\nNotes:")
    print("- This is a simple mechanical overlay, not financial advice.")
    print("- Structural case (central bank buying, debt dynamics) can override short-term signals.")
    print("- Re-run after FOMC, major data releases, or big yield/DXY moves.")

if __name__ == "__main__":
    main()