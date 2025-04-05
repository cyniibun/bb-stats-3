#schedule view

import streamlit as st
from utils.schedule_utils import fetch_schedule_by_date
from datetime import datetime, timedelta, date
import pytz
import pandas as pd
from utils.scoreboard_utils import render_scoreboard
from utils.lineup_utils import get_game_lineups

st.set_page_config(page_title="MLB Schedule", layout="wide")
st.title("📅 MLB Schedule")

# --- Date Selector ---
selected_date = st.date_input("Select a date", value=date.today())

# --- Load Schedule for Selected Date ---
games = fetch_schedule_by_date(datetime.combine(selected_date, datetime.min.time()))

if not games:
    st.warning(f"No games found for {selected_date.strftime('%B %d, %Y')}.")
else:
    eastern = pytz.timezone("US/Eastern")

    # Format games into a DataFrame for easier handling
    for game in games:
        try:
            game["Date"] = pd.to_datetime(game.get("time"), utc=True)
        except Exception:
            game["Date"] = pd.NaT

    schedule_df = pd.DataFrame(games).dropna(subset=["Date"]).sort_values(by="Date")

    # Get lineup data once
    lineup_map = get_game_lineups(selected_date.strftime("%Y-%m-%d"))

    for _, game in schedule_df.iterrows():
        home = game.get("home", "Unknown")
        away = game.get("opponent", "Unknown")
        game_time = game["Date"]

        try:
            if game_time.tzinfo is None:
                game_time = pytz.utc.localize(game_time)
            game_time = game_time.astimezone(eastern)
            formatted_time = game_time.strftime("%B %d, %Y at %I:%M %p EST")
            iso_time = game_time.isoformat()
        except:
            formatted_time = "TBD"
            iso_time = ""

        game_link = (
            f"/game_view?home={home.replace(' ', '%20')}"
            f"&away={away.replace(' ', '%20')}"
            f"&time={iso_time}"
        )

        with st.container():
            st.markdown(f"### [{away} @ {home}]({game_link})")
            st.markdown(f":clock1: **Game Time:** {formatted_time}")

            # Get gamePk from lineup data
            game_pk = lineup_map.get(f"{away} @ {home}", {}).get("gamePk")

            if game_pk:
                render_scoreboard(game_pk, home_team=home, away_team=away, autorefresh=False)

            st.markdown("---")
