import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.schedule_utils import get_today_schedule

st.title("⚾ Pitcher vs Batter Matchup Analyzer (Statcast Live)")
st.subheader("📅 Today's MLB Games")

with st.spinner("Fetching today's MLB games..."):
    games = get_today_schedule()

if not games:
    st.warning("No games found or error occurred fetching schedule.")
else:
    for game in games:
        home_away = "vs." if game["home"] else "@"
        matchup_str = f'{game["team"]} {home_away} {game["opponent"]} - {game["time"]}'
        st.markdown(f"- {matchup_str}")
