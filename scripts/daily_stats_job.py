import sys
import os
import warnings
import pandas as pd
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import io
import time
import random
import concurrent.futures
from functools import lru_cache
import pybaseball  # Import pybaseball for data fetching

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Add the root project directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Output directory
if os.environ.get("RENDER"):
    DATA_DIR = Path("/data/daily_stats")
else:
    DATA_DIR = Path("data/daily_stats")

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Caching the player data fetching to avoid redundant API calls
@lru_cache(maxsize=100)  # Cache up to 100 player ID lookups
def get_player_id_cached(first_name, last_name):
    """
    Handle suffixes like 'Jr.', 'II', and return correct player ID.
    """
    suffixes = ["Jr.", "Sr.", "II", "III", "IV"]
    if last_name.split()[-1] in suffixes:
        last_name = " ".join(last_name.split()[:-1])
    
    player_data = pybaseball.playerid_lookup(f"{first_name} {last_name}")
    
    # Handle multiple player entries, just return the first one.
    if player_data:
        return player_data['key_mlbam'][0]
    else:
        logger.error(f"Player ID lookup failed for {first_name} {last_name}")
        return None

def save_stats_to_csv(data, filename):
    file_path = DATA_DIR / filename
    data.to_csv(file_path, index=False)
    logger.info(f"[✓] Saved: {file_path}")

def get_all_team_rosters():
    """
    Use pybaseball to get the active rosters for all MLB teams.
    """
    all_players = []  # Store all player names here

    # List of MLB team codes (can be found in various places or on MLB website)
    team_codes = [
        "ARI", "ATL", "BAL", "BOS", "CHC", "CIN", "CLE", "COL", "DET", "HOU", "KCR", "LAA", 
        "LAD", "MIA", "MIL", "MIN", "NYM", "NYY", "OAK", "PHI", "PIT", "SDP", "SFG", "SEA", 
        "STL", "TBR", "TEX", "TOR", "WAS"
    ]

    # Get the roster for each team
    for team in team_codes:
        logger.info(f"Processing roster for {team}...")  # Log team being processed
        try:
            # Fetch the roster for the current team using pybaseball
            team_roster_data = pybaseball.get_team_rosters(2025)  # Replace with desired year

            if team_roster_data.empty:
                logger.warning(f"No data found for team {team}.")
                continue
            
            # Loop through the roster data and add player names to the list
            for player in team_roster_data[team]:
                player_name = player['name']
                logger.debug(f"Processing player: {player_name}")  # Log each player being processed
                all_players.append(player_name)

        except Exception as e:
            logger.error(f"Error fetching roster for {team}: {e}")
    
    logger.info(f"Found {len(all_players)} total players.")  # Final count of players
    return all_players


def save_raw_data(player_name, season, data, filename):
    """
    Save raw data (CSV, JSON, or any other format) to a file for future processing.
    """
    raw_data_dir = "data/statcast_raw"
    os.makedirs(raw_data_dir, exist_ok=True)
    
    file_path = os.path.join(raw_data_dir, f"{filename}.txt")
    with open(file_path, "w") as file:
        file.write(data)
    print(f"[INFO] Raw data saved for player {player_name}, season {season} at {file_path}")
    
    # Log first few lines of the raw response to check the format
    print(f"[DEBUG] First 100 characters of the raw data: {data[:100]}")


# Fetch statcast data with debug logs
def fetch_statcast_data(player_id, season="2024", pitch_type="all", player_role="batter"):
    """
    Fetch Statcast data for a player using pybaseball's statcast function.
    """
    try:
        # Fetch Statcast data using pybaseball
        data = pybaseball.statcast(start_dt="2024-04-01", end_dt="2024-04-10", player_id=player_id)
        
        if data.empty:
            logger.warning(f"No data for player {player_id} in season {season}.")
            return None

        # Clean and log the data
        logger.debug(f"Fetched Statcast Data for {player_id}: {data.head()}")  # Log first few rows of the data
        return data
    except Exception as e:
        logger.error(f"Error fetching Statcast data for player {player_id}: {e}")
        return None


# Fetch player stats for each player asynchronously with dynamic loading
async def fetch_all_stats_for_players(players, season="2025"):
    """
    Asynchronously fetch Statcast data for all players.
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for player_name in players:
            task = asyncio.create_task(fetch_player_data(player_name, session, season))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results


# Fetch statcast data for each player
async def fetch_player_data(player_name, session, season="2025"):
    """
    Fetches and saves Statcast data asynchronously for the given player.
    """
    # Split the player name into first and last names
    name_parts = player_name.split()
    if len(name_parts) == 2:
        first_name, last_name = name_parts
    else:
        logger.error(f"Invalid player name format: {player_name}")
        return None

    # Fetch player ID using first_name and last_name from the cache
    player_id = get_player_id_cached(first_name, last_name)  # Fetch player ID using the player name

    if player_id:
        logger.info(f"Fetching Statcast data for player {player_name} (ID: {player_id})...")

        # Fetch Statcast data for the player based on their role (handled by pybaseball)
        statcast_data = fetch_statcast_data(player_id, season)

        if statcast_data is not None:
            return statcast_data
        else:
            logger.warning(f"No Statcast data found for {player_name}.")
            return None
    else:
        logger.error(f"Unable to fetch player ID for {player_name}.")
        return None


def run_daily_stat_pull():
    print(f"📊 Running daily stat pull @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --- Get all MLB player names using pybaseball ---
    all_players = get_all_team_rosters()  # This will give us all players in list form

    # --- Fetch stats asynchronously ---
    loop = asyncio.get_event_loop()
    results_2025 = loop.run_until_complete(fetch_all_stats_for_players(all_players, season="2025"))
    results_2024 = loop.run_until_complete(fetch_all_stats_for_players(all_players, season="2024"))

    # --- Process and Save the Data ---
    all_player_data_2025 = [result for result in results_2025 if result is not None]
    all_player_data_2024 = [result for result in results_2024 if result is not None]

    if all_player_data_2025:
        df_all_players_2025 = pd.concat(all_player_data_2025, ignore_index=True)
        save_stats_to_csv(df_all_players_2025, f"all_players_stats_2025_{datetime.today().date()}.csv")
    else:
        print("[WARNING] No 2025 player stats found")

    if all_player_data_2024:
        df_all_players_2024 = pd.concat(all_player_data_2024, ignore_index=True)
        save_stats_to_csv(df_all_players_2024, f"all_players_stats_2024_{datetime.today().date()}.csv")
    else:
        print("[WARNING] No 2024 player stats found")

    print("✅ Stat pull complete.")


if __name__ == "__main__":
    run_daily_stat_pull()
