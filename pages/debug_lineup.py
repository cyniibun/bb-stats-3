import streamlit as st
import requests
from datetime import datetime
from urllib.parse import unquote
import pytz

st.set_page_config(page_title="Lineup Debugger", layout="wide")

st.title("🔍 Live Lineup Debugger")

game_pk = st.text_input("Enter GamePk", "")

if game_pk:
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    resp = requests.get(url)

    if not resp.ok:
        st.error("Failed to fetch boxscore data.")
    else:
        data = resp.json()

        teams = data["teams"]
        for team_key in ["away", "home"]:
            st.markdown(f"## {team_key.title()} Team")
            players = teams[team_key]["players"]
            debug_table = []

            for pid, player in players.items():
                name = player["person"]["fullName"]
                pos = player.get("position", {}).get("abbreviation", "N/A")
                batting_order = player.get("battingOrder", None)
                debug_table.append({
                    "Player ID": pid,
                    "Name": name,
                    "Position": pos,
                    "Batting Order": batting_order
                })

            st.dataframe(debug_table, use_container_width=True)
