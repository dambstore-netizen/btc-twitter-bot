"""
chart_generator.py
Generates a professional dark-themed BTC analysis chart with:
  - Panel 1: Candlestick + Bollinger Bands + EMA 20/50
  - Panel 2: Volume
  - Panel 3: RSI (14)
  - Panel 4: MACD
"""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for servers

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from datetime import datetime

from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


# ── Color palette (GitHub Dark inspired) ──────────────────────────────────────
BG       = "#0d1117"
SURFACE  = "#161b22"
BORDER   = "#30363d"
GRID     = "#21262d"
TEXT     = "#e6edf3"
MUTED    = "#8b949e"
BULL     = "#3fb950"   # green
BEAR     = "#f85149"   # red
BLUE     = "#58a6ff"
ORANGE   = "#f0883e"
PURPLE   = "#d2a8ff"
YELLOW   = "#e3b341"


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicator columns to the dataframe."""
    df = df.copy()

    # Bollinger Bands (20, 2)
    bb = BollingerBands(close=df["close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()

    # EMAs
    df["ema20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()

    # RSI (14)
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()

    # MACD (12, 26, 9)
    macd_obj       = MACD(close=df["close"])
    df["macd"]        = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_hist"]   = macd_obj.macd_diff()

    return df


def _style_ax(ax):
    """Apply dark theme to a matplotlib axis."""
    ax.set_facecolor(BG)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.grid(True, color=GRID, alpha=0.6, linewidth=0.5, linestyle="-")
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.yaxis.label.set_color(MUTED)
    ax.yaxis.label.set_fontsize(8)


def generate_chart(df: pd.DataFrame) -> tuple:
    """
    Generate the analysis chart.

    Args:
        df: OHLCV DataFrame (90 daily candles recommended)

    Returns:
        (chart_path: str, indicators: dict)
    """
    df = _add_indicators(df)

    # Use last 60 candles for chart display
    df_plot = df.tail(60).copy().reset_index(drop=True)
    x = df_plot.index

    # ── Figure layout ──────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(16, 11), facecolor=BG)
    gs  = gridspec.GridSpec(
        4, 1, figure=fig,
        height_ratios=[4, 1.2, 1.2, 1.2],
        hspace=0.0
    )
    ax_price  = fig.add_subplot(gs[0])
    ax_vol    = fig.add_subplot(gs[1], sharex=ax_price)
    ax_rsi    = fig.add_subplot(gs[2], sharex=ax_price)
    ax_macd   = fig.add_subplot(gs[3], sharex=ax_price)

    for ax in [ax_price, ax_vol, ax_rsi, ax_macd]:
        _style_ax(ax)
        ax.set_xlim(-1, len(df_plot))

    plt.setp(ax_price.get_xticklabels(), visible=False)
    plt.setp(ax_vol.get_xticklabels(),   visible=False)
    plt.setp(ax_rsi.get_xticklabels(),   visible=False)

    # ── Panel 1: Candlestick + BB + EMA ───────────────────────────────────────
    for i, row in df_plot.iterrows():
        color = BULL if row["close"] >= row["open"] else BEAR
        # Body
        ax_price.bar(
            i, abs(row["close"] - row["open"]),
            bottom=min(row["open"], row["close"]),
            color=color, width=0.6, alpha=0.95, zorder=2
        )
        # Wick
        ax_price.plot(
            [i, i], [row["low"], row["high"]],
            color=color, linewidth=0.8, alpha=0.9, zorder=2
        )

    # Bollinger Band fill
    ax_price.fill_between(
        x, df_plot["bb_upper"], df_plot["bb_lower"],
        alpha=0.06, color=BLUE, zorder=1
    )
    ax_price.plot(x, df_plot["bb_upper"], color=BLUE, linewidth=0.8,
                  alpha=0.65, linestyle="--", label="BB (20,2)", zorder=1)
    ax_price.plot(x, df_plot["bb_lower"], color=BLUE, linewidth=0.8,
                  alpha=0.65, linestyle="--", zorder=1)
    ax_price.plot(x, df_plot["bb_mid"],   color=BLUE, linewidth=0.6,
                  alpha=0.35, linestyle=":",  zorder=1)

    # EMAs
    ax_price.plot(x, df_plot["ema20"], color=ORANGE,  linewidth=1.3,
                  alpha=0.9, label="EMA 20", zorder=3)
    ax_price.plot(x, df_plot["ema50"], color=PURPLE,  linewidth=1.3,
                  alpha=0.9, label="EMA 50", zorder=3)

    ax_price.legend(
        loc="upper left", fontsize=7.5,
        facecolor=SURFACE, edgecolor=BORDER, labelcolor=MUTED, framealpha=0.95
    )
    ax_price.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"${v:,.0f}")
    )
    ax_price.set_ylabel("Price (USD)")

    # Dynamic title
    cur  = df_plot["close"].iloc[-1]
    prev = df_plot["close"].iloc[-2]
    pct  = (cur - prev) / prev * 100
    arrow = "▲" if pct >= 0 else "▼"
    c_txt = BULL if pct >= 0 else BEAR

    fig.text(
        0.5, 0.975,
        f"BTC / USDT — Daily Chart",
        ha="center", va="top", color=MUTED, fontsize=10
    )
    fig.text(
        0.5, 0.955,
        f"${cur:,.2f}  {arrow} {abs(pct):.2f}%",
        ha="center", va="top", color=c_txt, fontsize=18, fontweight="bold"
    )
    fig.text(
        0.5, 0.935,
        df_plot["timestamp"].iloc[-1].strftime("%B %d, %Y"),
        ha="center", va="top", color=MUTED, fontsize=9
    )

    # ── Panel 2: Volume ────────────────────────────────────────────────────────
    vol_colors = [
        BULL if df_plot["close"].iloc[i] >= df_plot["open"].iloc[i] else BEAR
        for i in range(len(df_plot))
    ]
    ax_vol.bar(x, df_plot["volume"], color=vol_colors, alpha=0.65, width=0.6)

    vol_ma = df_plot["volume"].rolling(20).mean()
    ax_vol.plot(x, vol_ma, color=YELLOW, linewidth=0.9, alpha=0.8, label="Vol MA20")
    ax_vol.legend(loc="upper left", fontsize=7, facecolor=SURFACE,
                  edgecolor=BORDER, labelcolor=MUTED, framealpha=0.9)
    ax_vol.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{v/1e9:.1f}B" if v >= 1e9 else f"{v/1e6:.0f}M")
    )
    ax_vol.set_ylabel("Volume")

    # ── Panel 3: RSI ───────────────────────────────────────────────────────────
    rsi_now = df_plot["rsi"].iloc[-1]
    ax_rsi.plot(x, df_plot["rsi"], color=ORANGE, linewidth=1.2)
    ax_rsi.axhline(70, color=BEAR,  linewidth=0.8, linestyle="--", alpha=0.7)
    ax_rsi.axhline(50, color=MUTED, linewidth=0.5, linestyle=":", alpha=0.5)
    ax_rsi.axhline(30, color=BULL,  linewidth=0.8, linestyle="--", alpha=0.7)
    ax_rsi.fill_between(x, df_plot["rsi"], 70,
                        where=(df_plot["rsi"] >= 70), alpha=0.12, color=BEAR)
    ax_rsi.fill_between(x, df_plot["rsi"], 30,
                        where=(df_plot["rsi"] <= 30), alpha=0.12, color=BULL)
    ax_rsi.set_ylim(0, 100)
    ax_rsi.set_yticks([30, 50, 70])
    ax_rsi.set_ylabel("RSI (14)")
    # Current RSI label
    ax_rsi.text(
        len(df_plot) - 0.5, rsi_now, f" {rsi_now:.1f}",
        color=ORANGE, fontsize=8.5, va="center", ha="left", fontweight="bold"
    )

    # ── Panel 4: MACD ──────────────────────────────────────────────────────────
    hist_colors = [BULL if h >= 0 else BEAR for h in df_plot["macd_hist"]]
    ax_macd.bar(x, df_plot["macd_hist"], color=hist_colors, alpha=0.6, width=0.6)
    ax_macd.plot(x, df_plot["macd"],        color=BLUE,   linewidth=1.2, label="MACD")
    ax_macd.plot(x, df_plot["macd_signal"], color=ORANGE, linewidth=1.2, label="Signal")
    ax_macd.axhline(0, color=MUTED, linewidth=0.5, alpha=0.4)
    ax_macd.legend(
        loc="upper left", fontsize=7, facecolor=SURFACE,
        edgecolor=BORDER, labelcolor=MUTED, framealpha=0.9
    )
    ax_macd.set_ylabel("MACD")

    # X-axis date labels (on MACD panel only)
    step = max(1, len(df_plot) // 10)
    ticks = list(range(0, len(df_plot), step))
    ax_macd.set_xticks(ticks)
    ax_macd.set_xticklabels(
        [df_plot["timestamp"].iloc[i].strftime("%d %b") for i in ticks],
        rotation=30, ha="right", color=MUTED, fontsize=7.5
    )

    # Watermark
    fig.text(
        0.99, 0.01, "BTC Analysis Bot",
        ha="right", va="bottom", color=MUTED, fontsize=7, alpha=0.4
    )

    # ── Save ───────────────────────────────────────────────────────────────────
    chart_path = f"/tmp/btc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(
        chart_path, dpi=150, bbox_inches="tight",
        facecolor=BG, edgecolor="none"
    )
    plt.close(fig)

    # Return last-row indicator values for the analysis prompt
    last = df.iloc[-1]
    indicators = {
        "price":        round(float(last["close"]),       2),
        "rsi":          round(float(last["rsi"]),         2),
        "macd":         round(float(last["macd"]),        4),
        "macd_signal":  round(float(last["macd_signal"]), 4),
        "macd_hist":    round(float(last["macd_hist"]),   4),
        "bb_upper":     round(float(last["bb_upper"]),    2),
        "bb_lower":     round(float(last["bb_lower"]),    2),
        "bb_mid":       round(float(last["bb_mid"]),      2),
        "ema20":        round(float(last["ema20"]),       2),
        "ema50":        round(float(last["ema50"]),       2),
    }

    print(f"  -> Chart saved: {chart_path}")
    return chart_path, indicators
