import statsapi
import json
import logging
from datetime import datetime

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def fetch_schedule_for_date(date_str):
    """Fetches the MLB schedule for a given date."""
    try:
        # Use statsapi to fetch the schedule for the specific date
        schedule = statsapi.schedule(date=date_str)
        if not schedule:
            print(f"[ERROR] No games found for {date_str}.")
            return None
        print(f"[DEBUG] Schedule fetched successfully for {date_str}")
        return schedule
    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule for {date_str}: {e}")
        return None

def extract_game_details(schedule):
    """Extracts game details including teams, time, and game ID."""
    game_details = []
    if schedule:
        for game in schedule:
            # Extract game details
            home_team = game.get("home_name", "Unknown")
            away_team = game.get("away_name", "Unknown")
            game_time = game.get("game_date", "TBD")
            game_id = game.get("game_id", "Unknown")

            # Append to the list as a dictionary
            game_details.append({
                "home_team": home_team,
                "away_team": away_team,
                "game_time": game_time,
                "game_id": game_id
            })
    else:
        print("[ERROR] No schedule to extract.")

    return game_details

def fetch_and_return_schedule(date_str):
    """Fetches the schedule for a given date and returns the game details as a list of dictionaries."""
    # Fetch the schedule for the selected date
    schedule = fetch_schedule_for_date(date_str)

    # Extract game details
    return extract_game_details(schedule)



# Example usage: Calling the function with any dynamic date
if __name__ == "__main__":
    # Pass in any date dynamically here
    selected_date = "2025-04-05"  # Example date
    game_data = fetch_and_return_schedule(selected_date)

    # Print the extracted data for debugging or other use
    print(f"Extracted Game Data: {json.dumps(game_data, indent=2)}")
