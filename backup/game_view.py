#game_view.py code
import sys
import os
import requests

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from utils.probable_pitcher_utils import get_probable_pitchers
from utils.boxscore_utils import get_active_pitchers
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote, quote
import pandas as pd
import pytz
import streamlit as st
from datetime import datetime
import logging
from utils.style_utils import get_red_shade, get_pitcher_red_green_shade, get_pitcher_blue_red_shade
from utils.lineup_utils import get_game_lineups, get_live_lineup
from utils.calculate_util import calculate_metrics
from utils.lookup_utils import get_player_id_by_name
from utils.mlb_api import get_probable_pitchers_for_date, get_game_state, get_pitcher_arsenal_from_statcast
from utils.style_helpers import sanitize_numeric_columns
from utils.scoreboard_utils import render_scoreboard
from utils.formatting_utils import format_baseball_stats


# Logging configuration
log_filename = './data/statcast_metrics.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename, mode='w')
    ]
)

# Streamlit page config
st.set_page_config(page_title="Game View", layout="wide")

# Query Parameters and Time Conversion
query_params = st.query_params
home = unquote(query_params.get("home", "Unknown"))
away = unquote(query_params.get("away", "Unknown"))
game_time_utc = query_params.get("time", "Unknown")

# Convert UTC time to Eastern Time
try:
    utc_dt = datetime.fromisoformat(game_time_utc.replace("Z", "+00:00"))
    eastern = pytz.timezone("US/Eastern")
    est_dt = utc_dt.astimezone(eastern)
    formatted_time = est_dt.strftime("%B %d, %Y at %I:%M %p EST")
    date_only = est_dt.strftime("%Y-%m-%d")
except Exception:
    formatted_time = game_time_utc
    date_only = game_time_utc.split("T")[0] if "T" in game_time_utc else "Unknown"

# Page Header
st.title(f"\U0001F3DF️ {away} @ {home}")
st.markdown(f"\U0001F552 **Game Time:** {formatted_time}")
st.markdown("---")

# Get GamePK & Lineups
lineup_map = get_game_lineups(date_only)
game_pk = lineup_map.get(f"{away} @ {home}", {}).get("gamePk")

# Call the get_probable_pitchers function with the gamePk
pitchers = get_probable_pitchers(game_pk)

# Live active lineup (9 players only)
away_lineup_raw, home_lineup_raw = get_live_lineup(game_pk, starters_only=True) if game_pk else ([], [])

away_pitcher_id, home_pitcher_id = get_active_pitchers(game_pk)

# Output the pitcher IDs for debugging
st.write(f"Away Pitcher ID: {away_pitcher_id}")
st.write(f"Home Pitcher ID: {home_pitcher_id}")

# Fallback pitcher if not announced
def fallback_pitcher_from_lineup(lineup):
    return next((p.replace(" - P", "") for p in lineup if " - P" in p), "Not Announced")



# Render Scoreboard
if game_pk:
    render_scoreboard(game_pk, home_team=home, away_team=away)

st.write("gamePk:", game_pk)

# Create a list (matrix) to store player IDs
player_ids = []

# Function to extract player IDs from the lineups
def get_player_ids_from_lineup(lineup):
    return [get_player_id_by_name(player.split(" - ")[0].strip()) for player in lineup]

# Extract player IDs for both teams
away_player_ids = get_player_ids_from_lineup(away_lineup_raw)
home_player_ids = get_player_ids_from_lineup(home_lineup_raw)

# Combine both away and home player IDs into a single list
player_ids.extend(away_player_ids)
player_ids.extend(home_player_ids)

# Now loop through player_ids and get their metrics
# Cache the player metrics data to avoid recalculating on every run
@st.cache_data
def fetch_player_metrics(player_ids):
    metrics = {}
    for player_id in player_ids:
        player_metrics = calculate_metrics(player_id)
        if player_metrics:
            # Flatten and convert the metrics to serializable types
            for pitch_name, stats in player_metrics.items():
                # Ensure all values are JSON serializable (int, float, str)
                metrics[pitch_name] = {
                    'player_id': str(stats['player_id']),
                    'K%': float(stats['K%']) if isinstance(stats['K%'], (np.generic, float)) else float(stats['K%']),
                    'Whiff Rate': float(stats['Whiff Rate']) if isinstance(stats['Whiff Rate'], (np.generic, float)) else float(stats['Whiff Rate']),
                    'PutAway%': float(stats['PutAway%']) if isinstance(stats['PutAway%'], (np.generic, float)) else float(stats['PutAway%']),
                    'OBA': float(stats['OBA']) if isinstance(stats['OBA'], (np.generic, float)) else float(stats['OBA']),
                    'SLG': float(stats['SLG']) if isinstance(stats['SLG'], (np.generic, float)) else float(stats['SLG']),
                    'Hits': int(stats['Hits']) if isinstance(stats['Hits'], (np.generic, int)) else int(stats['Hits']),
                    'Total Plate Appearances': int(stats['Total Plate Appearances']) if isinstance(stats['Total Plate Appearances'], (np.generic, int)) else int(stats['Total Plate Appearances'])
                }
    return metrics

# Fetch the metrics
player_metrics = fetch_player_metrics(player_ids)
st.write(player_metrics)


def get_active_pitchers(game_pk):
    # MLB Stats API URL to fetch game data
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Print the entire response to see the structure
        print("Full Game Data: ", data)
        
        # Extract pitcher data for away and home teams (Check if they exist)
        away_pitcher_id = data['gameData']['players'].get(data['liveData']['boxscore'].get('awayPitcher', {}).get('id'))
        home_pitcher_id = data['gameData']['players'].get(data['liveData']['boxscore'].get('homePitcher', {}).get('id'))
        
        return away_pitcher_id, home_pitcher_id
    else:
        print("Failed to fetch game data")
        return None, None


# Fetch pitcher data
away_pitcher_id, home_pitcher_id = get_active_pitchers(game_pk)

# Fetch the player metrics for the pitcher from the player_metrics data
def display_pitcher_metrics(player_metrics, pitcher_id, team_name):
    if pitcher_id and pitcher_id in player_metrics:
        pitcher_data = player_metrics[pitcher_id]
        st.subheader(f"{team_name} Pitcher Metrics")
        for pitch, stats in pitcher_data.items():
            st.write(f"**{pitch}:**")
            st.write(f"K%: {stats['K%']}")
            st.write(f"Whiff Rate: {stats['Whiff Rate']}")
            st.write(f"PutAway%: {stats['PutAway%']}")
            st.write(f"OBA: {stats['OBA']}")
            st.write(f"SLG: {stats['SLG']}")
            st.write(f"Hits: {stats['Hits']}")
            st.write(f"Total Plate Appearances: {stats['Total Plate Appearances']}")
    else:
        st.warning(f"No metrics found for {team_name} pitcher")




# Display away pitcher metrics if available
if away_pitcher_id:
    display_pitcher_metrics(player_metrics, away_pitcher_id, away)

# Display home pitcher metrics if available
if home_pitcher_id:
    display_pitcher_metrics(player_metrics, home_pitcher_id, home)



# Create two columns below the scoreboard for the away and home team data
col1, col2 = st.columns(2)

with col1:
    # Render Away Team starting pitcher label
    st.subheader(f"{away} Starting Pitcher")
    # Render Away Team pitcher name below the label
    if 'away_pitcher' in pitchers and isinstance(pitchers['away_pitcher'], dict):
        st.markdown(f"**Pitcher Name:** {pitchers['away_pitcher'].get('fullName', 'Not Available')}")

    # Render Away Team lineup
    st.subheader(f"{away} Starting Lineup")
    if away_lineup_raw:
        st.markdown("\n".join([f"{i+1}. {player}" for i, player in enumerate(away_lineup_raw)]))
    else:
        st.markdown("Lineup not available yet.")

with col2:
    # Render Home Team starting pitcher label
    st.subheader(f"{home} Starting Pitcher")
    # Render Home Team pitcher name below the label
    if 'home_pitcher' in pitchers and isinstance(pitchers['home_pitcher'], dict):
        st.markdown(f"**Pitcher Name:** {pitchers['home_pitcher'].get('fullName', 'Not Available')}")

    # Render Home Team lineup
    st.subheader(f"{home} Starting Lineup")
    if home_lineup_raw:
        st.markdown("\n".join([f"{i+1}. {player}" for i, player in enumerate(home_lineup_raw)]))
    else:
        st.markdown("Lineup not available yet.")
