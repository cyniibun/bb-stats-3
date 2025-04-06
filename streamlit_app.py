import statsapi
import pandas as pd
from datetime import datetime
import pytz
import streamlit as st

def fetch_schedule_for_date(selected_date):
    """Fetches the MLB schedule for the selected date."""
    try:
        schedule = statsapi.schedule(date=selected_date)
        if not schedule:
            st.warning(f"No games found for {selected_date.strftime('%B %d, %Y')}.")
            return None
        st.write(f"[DEBUG] Schedule fetched successfully for {selected_date.strftime('%B %d, %Y')}")
        return schedule
    except Exception as e:
        st.error(f"[ERROR] Failed to fetch schedule for {selected_date.strftime('%Y-%m-%d')}: {e}")
        return None

def convert_to_est(game_datetime):
    """Converts a given game datetime string from UTC to EST."""
    utc_time = datetime.strptime(game_datetime, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = pytz.utc.localize(utc_time)
    est_time = utc_time.astimezone(pytz.timezone('US/Eastern'))
    return est_time

def process_schedule_data(schedule):
    """Processes the schedule data, converting datetime to EST and sorting the games."""
    games = []

    # Process each game and convert its datetime to EST
    for game in schedule:
        home_team = game.get("home_name", "Unknown")
        away_team = game.get("away_name", "Unknown")
        game_datetime = game.get("game_datetime", "")
        game_id = game.get("game_id", "Unknown")
        print(game_id)

        if game_datetime:
            # Convert to EST
            est_time = convert_to_est(game_datetime)
            formatted_time = est_time.strftime("%B %d, %Y at %I:%M %p EST")
            iso_time = est_time.isoformat()

            # Add to the list of games
            games.append({
                "home": home_team,
                "away": away_team,
                "game_time": formatted_time,
                "iso_time": iso_time,
                "game_id": game_id,
                "datetime": est_time  # For sorting
            })

    # Sort games by datetime in ascending order (earlier games first)
    games_sorted = sorted(games, key=lambda x: x['datetime'])
    return games_sorted

def display_schedule(games_sorted):
    """Displays the schedule in Streamlit."""
    if games_sorted:
        for game in games_sorted:
            home = game.get("home", "Unknown")
            away = game.get("away", "Unknown")
            game_time = game.get("game_time", "TBD")
            game_id = game.get("game_id", "Unknown")

            # Construct the link to the game view page, including the game_id
            # Example to pass the actual game_id dynamically
            game_link = f"/game_view?home={home.replace(' ', '%20')}&away={away.replace(' ', '%20')}&game_id={game_id}&time={game['iso_time']}"


            with st.container():
                st.markdown(f"### [{away} @ {home}]({game_link})")
                st.markdown(f":clock1: **Game Time:** {game_time}")
                st.markdown(f"Game ID: {game_id}")
                st.markdown("---")
    else:
        st.warning("No games available for display.")

# Streamlit Page Configuration
st.set_page_config(page_title="MLB Schedule", layout="wide")
st.title("📅 MLB Schedule")

# --- Date Selector ---
selected_date = st.date_input("Select a date", value=datetime.today())

# --- Fetch Schedule for the Selected Date ---
if selected_date:
    # Fetch the schedule for the selected date
    schedule = fetch_schedule_for_date(selected_date)

    if schedule:
        # Process the schedule data
        games_sorted = process_schedule_data(schedule)

        # Display the sorted schedule
        display_schedule(games_sorted)
