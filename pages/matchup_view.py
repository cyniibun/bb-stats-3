# matchup_view.py

import sys
import os
import streamlit as st
import pandas as pd
from urllib.parse import unquote
from datetime import datetime
from utils.stat_utils import get_pitcher_stats, get_batter_metrics_by_pitch
from utils.style_helpers import style_pitcher_table, style_batter_table, style_delta_table, sanitize_numeric_columns
from utils.mlb_api import get_player_id
from utils.formatting_utils import format_baseball_stats

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Batter vs Pitcher Matchup", layout="wide")

# --- Query Params ---
query_params = st.query_params
batter_name = unquote(query_params.get("batter", "Unknown"))
team_name = unquote(query_params.get("team", "Unknown"))
home_team = unquote(query_params.get("home", "Unknown"))
away_team = unquote(query_params.get("away", "Unknown"))
home_pitcher = unquote(query_params.get("home_pitcher", "Not Announced"))
away_pitcher = unquote(query_params.get("away_pitcher", "Not Announced"))

# --- Determine opponent pitcher ---
pitcher_name = away_pitcher if team_name == home_team else home_pitcher

# --- Title + Season Filter ---
st.title(f"Matchup: {batter_name} vs. {pitcher_name}")
st.markdown(f"**Team:** {team_name}")

season_choice = st.selectbox(
    "Select Season Range",
    options=["All", "2024", "2025"],
    index=0  # ✅ Default to "All"
)

if season_choice == "2024":
    start_date = "2024-03-01"
    end_date = "2024-12-31"
elif season_choice == "2025":
    start_date = "2025-03-01"
    end_date = "2025-12-31"
else:
    start_date = "2024-03-01"
    end_date = None  # Pull through today

# --- Get Batter ID ---
try:
    first, last = batter_name.strip().split(" ", 1)
    batter_id = get_player_id(first, last)
except ValueError:
    batter_id = None

# --- Fetch Stats (Scoped to Season) ---
pitcher_df = get_pitcher_stats(pitcher_name, start_date=start_date, end_date=end_date)
batter_df = get_batter_metrics_by_pitch(batter_id, start_date=start_date, end_date=end_date) if batter_id else pd.DataFrame()

# --- Display Content ---
if pitcher_df.empty or batter_df.empty:
    st.warning("Insufficient data to display matchup.")
else:
    # Sanitize numeric columns
    numeric_cols = ["BA", "SLG", "wOBA", "K%", "Whiff%", "PutAway%"]
    pitcher_df = sanitize_numeric_columns(pitcher_df, numeric_cols)
    batter_df = sanitize_numeric_columns(batter_df, numeric_cols)

    batter_df = batter_df.round(2)
    pitcher_df = pitcher_df.round(2)

    common_pitches = set(pitcher_df["pitch_type"]) & set(batter_df["pitch_type"])
    pitcher_df = pitcher_df[pitcher_df["pitch_type"].isin(common_pitches)]
    batter_df = batter_df[batter_df["pitch_type"].isin(common_pitches)]

    matchup_df = pd.merge(
        pitcher_df,
        batter_df,
        on="pitch_type",
        suffixes=("_P", "_B")
    )

    for metric in ["K%", "Whiff%", "PutAway%", "SLG", "wOBA", "BA"]:
        matchup_df[f"Δ {metric}"] = (matchup_df[f"{metric}_B"] - matchup_df[f"{metric}_P"]).round(2)

    # --- Display Pitcher Table ---
    st.markdown("### Pitcher Arsenal")
    pitcher_cols = ["pitch_type", "PA", "BA", "SLG", "wOBA", "K%", "Whiff%", "PutAway%"]
    pitcher_df = format_baseball_stats(pitcher_df)  # Apply formatting to pitcher stats
    st.dataframe(style_pitcher_table(pitcher_df[pitcher_cols]), use_container_width=True)

    # --- Display Batter Table ---
    st.markdown("### Batter Metrics by Pitch Type")
    batter_cols = ["pitch_type", "BA", "SLG", "wOBA", "K%", "Whiff%", "PutAway%"]
    batter_df = format_baseball_stats(batter_df)  # Apply formatting to batter stats
    st.dataframe(style_batter_table(batter_df[batter_cols]), use_container_width=True)

    # --- Delta Table ---
    st.markdown("### Matchup Delta Table")
    delta_cols = [
        "pitch_type", 
        "K%_P", "K%_B", "Δ K%",
        "Whiff%_P", "Whiff%_B", "Δ Whiff%",
        "PutAway%_P", "PutAway%_B", "Δ PutAway%",
        "SLG_P", "SLG_B", "Δ SLG",
        "wOBA_P", "wOBA_B", "Δ wOBA",
        "BA_P", "BA_B", "Δ BA"
    ]
    matchup_df = format_baseball_stats(matchup_df)  # Apply formatting to delta values
    st.dataframe(style_delta_table(matchup_df[delta_cols]), use_container_width=True)
