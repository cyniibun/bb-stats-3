import requests
import streamlit as st

def get_active_pitchers(game_pk):
    # MLB Stats API URL to fetch game data
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Debugging: Print the raw response to inspect its structure
        #print("Full Game Data: ", data)

        # Check if the away and home pitcher data exists in the response
        away_pitcher = data['liveData']['boxscore'].get('awayPitcher', {})
        home_pitcher = data['liveData']['boxscore'].get('homePitcher', {})

        # Debugging: Print the away and home pitcher data
        #print("Away Pitcher Data:", away_pitcher)
        #print("Home Pitcher Data:", home_pitcher)

        if away_pitcher and home_pitcher:
            return away_pitcher.get('id', None), home_pitcher.get('id', None)
        else:
            print("Pitcher data missing or invalid.")
            return None, None
    else:
        print("Failed to fetch game data")
        return None, None
