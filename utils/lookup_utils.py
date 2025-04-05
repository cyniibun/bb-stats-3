import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pybaseball
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

from datetime import datetime


def get_player_id_by_name(player_name):
    """
    Fetches the player ID for a given player name (first and last name).
    Returns the player ID of the first player returned from the lookup.
    """
    try:
        # Split the player name into first and last names
        names = player_name.split()
        last_name = names[-1]  # Last name is the last word
        first_name = names[0]  # First name is the first word
        
        # Log the player name being searched
        logging.debug(f"Searching for player: {first_name} {last_name}")

        # Use pybaseball's playerid_lookup function to fetch player data
        player_data = pybaseball.playerid_lookup(last_name, first_name)

        if player_data.empty:
            logging.warning(f"No player found for {player_name}")
            return None

        # If multiple players are returned, use the first one
        player_id = player_data.iloc[0]['key_mlbam']

        # Log the player ID of the first result
        logging.debug(f"Found player ID for {player_name}: {player_id}")

        return player_id

    except Exception as e:
        logging.error(f"Error fetching player ID for {player_name}: {e}")
        return None