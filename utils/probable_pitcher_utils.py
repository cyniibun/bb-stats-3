import requests
from datetime import datetime

def get_probable_pitchers(gamePk, end_date=None):
    """
    This function returns the probable pitchers for a given game (gamePk).
    :param gamePk: The game ID
    :param end_date: The end date for fetching the schedule data. Defaults to today.
    :return: A dictionary containing the probable pitchers for the game.
    """
    # Default start date
    start_date = "2024-01-01"
    
    # Set the end date to today's date if not provided
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')  # Get current date in YYYY-MM-DD format
    
    # API endpoint URL with startDate and endDate parameters
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=probablePitcher&startDate={start_date}&endDate={end_date}&gamePk={gamePk}"

    # Send the request to the MLB API
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Look for the game matching the gamePk
        for game in data['dates']:
            for game_data in game['games']:
                if game_data['gamePk'] == gamePk:
                    away_pitcher = game_data['teams']['away'].get('probablePitcher', {})
                    home_pitcher = game_data['teams']['home'].get('probablePitcher', {})
                    
                    # Return the pitchers data
                    return {
                        "away_pitcher": away_pitcher if away_pitcher else "Not Available",
                        "home_pitcher": home_pitcher if home_pitcher else "Not Available"
                    }
        return {"error": "Game not found."}
    else:
        return {"error": "Failed to fetch data."}

