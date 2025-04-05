import streamlit as st
import pandas as pd
from datetime import datetime
from utils.mlb_api import (
    get_pitcher_arsenal_from_statcast,
    get_batter_performance_by_pitch,
    get_player_id
)

PITCH_TYPE_MAP = {
    "FF": "4-Seam Fastball", "SL": "Slider", "CH": "Changeup", "CU": "Curveball",
    "SI": "Sinker", "FC": "Cutter", "FS": "Splitter", "FT": "2-Seam Fastball",
    "KC": "Knuckle Curve", "ST": "Sweeper", "SV": "Slurve"
}

@st.cache_data(ttl=600)
def get_pitcher_stats(name: str, start_date="2024-03-01", end_date=None) -> pd.DataFrame:
    try:
        first, last = name.strip().split(" ", 1)
    except ValueError:
        return pd.DataFrame()

    # Get player ID using the updated method from mlb_api
    pid = get_player_id(first, last)
    if not pid:
        return pd.DataFrame()

    # Use the function from mlb_api to get pitcher stats
    df = get_pitcher_arsenal_from_statcast(pid, start_date, end_date)
    if df.empty:
        return pd.DataFrame()

    return df


@st.cache_data(ttl=600)
def get_batter_k_rate_by_pitch(batter_name: str, start_date="2024-03-01", end_date=None) -> dict:
    try:
        first, last = batter_name.strip().split(" ", 1)
    except ValueError:
        return {}

    batter_id = get_player_id(first, last)
    if not batter_id:
        return {}

    # Get the batter's performance data using the function from mlb_api
    df = get_batter_performance_by_pitch(batter_name, batter_id, start_date, end_date)
    if df.empty or "pitch_type" not in df.columns:
        return {}

    # Processing the batter's data to get K rate
    grouped = df.groupby("pitch_type")
    k_rate = grouped.apply(lambda x: (x["events"] == "strikeout").sum() / len(x) * 100).round(2)

    return {
        PITCH_TYPE_MAP.get(pitch, pitch): f"{k_rate.get(pitch, 0.0):.2f}%"
        for pitch in df["pitch_type"].unique()
    }


def get_batter_metrics_by_pitch(batter_id: int, start_date="2024-03-01", end_date=None) -> pd.DataFrame:
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Fetch batter performance data using the function from mlb_api
    df = get_batter_performance_by_pitch(batter_id, start_date, end_date)
    if df.empty or "pitch_type" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby("pitch_type")

    summary = grouped.agg(
        PA=("pitch_type", "count"),
        BA=("estimated_ba_using_speedangle", "mean"),
        SLG=("estimated_slg_using_speedangle", "mean"),
        wOBA=("estimated_woba_using_speedangle", "mean"),
        K_rate=("events", lambda x: (x == "strikeout").sum() / len(x) * 100),
        Whiff_rate=("description", lambda x: x.str.contains("swinging_strike").sum() / len(x) * 100),
        PutAway_rate=("description", lambda x: (x.str.contains("strikeout|swinging_strike")).sum() / len(x) * 100)
    )

    summary = summary.rename(columns={
        "K_rate": "K%", "Whiff_rate": "Whiff%", "PutAway_rate": "PutAway%"
    })

    summary.index = summary.index.map(lambda code: PITCH_TYPE_MAP.get(code, code))
    return summary.reset_index().rename(columns={"index": "pitch_type"})

def get_pitcher_arsenal_stats(player_id: int, start_date="2024-03-01", end_date=None) -> pd.DataFrame:
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Get the pitcher's arsenal stats using the function from mlb_api
    df = get_pitcher_arsenal_from_statcast(player_id, start_date, end_date)
    if df.empty or "pitch_type" not in df.columns:
        return pd.DataFrame()

    df = df[df["pitch_type"].notna()]
    grouped = df.groupby("pitch_type")

    summary = grouped.agg(
        PA=("batter", "count"),
        BA=("estimated_ba_using_speedangle", "mean"),
        SLG=("estimated_slg_using_speedangle", "mean"),
        wOBA=("estimated_woba_using_speedangle", "mean"),
        K_rate=("events", lambda x: (x == "strikeout").sum() / len(x) * 100),
        Whiff_rate=("description", lambda x: x.str.contains("swinging_strike").sum() / len(x) * 100),
        PutAway_rate=("description", lambda x: (x.str.contains("strikeout|swinging_strike")).sum() / len(x) * 100)
    )

    summary = summary.rename(columns={
        "K_rate": "K%", "Whiff_rate": "Whiff%", "PutAway_rate": "PutAway%"
    })

    summary.index = summary.index.map(lambda code: PITCH_TYPE_MAP.get(code, code))
    return summary.reset_index().rename(columns={"index": "pitch_type"})
