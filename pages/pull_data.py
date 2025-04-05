import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.stat_utils import get_pitcher_stats, get_batter_metrics_by_pitch
from utils.schedule_utils import fetch_schedule_by_date
from utils.mlb_api import get_player_id
from datetime import datetime

st.title("📊 Manual Stat & Schedule Pull")

# Pitcher Stats Section
st.header("Pull Pitcher Stats")
pitcher_name = st.text_input("Enter Pitcher Name (e.g. 'Jacob deGrom')")
if st.button("Fetch Pitcher Stats"):
    if pitcher_name:
        df = get_pitcher_stats(pitcher_name, refresh=True)
        st.success(f"Pulled {len(df)} pitch types for {pitcher_name}")
        st.dataframe(df)

# Batter Stats Section
st.header("Pull Batter Stats")
batter_name = st.text_input("Enter Batter Name (e.g. 'Mookie Betts')")
if st.button("Fetch Batter Stats"):
    if batter_name:
        first, last = batter_name.strip().split(" ", 1)
        batter_id = get_player_id(first, last)
        if batter_id:
            df = get_batter_metrics_by_pitch(batter_id, refresh=True)
            st.success(f"Pulled batter stats for {batter_name}")
            st.dataframe(df)

# Schedule Section
st.header("Refresh Game Schedule")
if st.button("Fetch Today's Schedule"):
    today = datetime.now().strftime("%Y-%m-%d")
    schedule_df = fetch_schedule_by_date(today)
    st.success("MLB schedule refreshed.")
    st.dataframe(schedule_df)
