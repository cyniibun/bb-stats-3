#mlb_api.py

'''
import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
'''

import requests
import pandas as pd
from datetime import datetime
import json
import statsapi
import pytz


# --- Fetch Pitcher Stats from Statcast API ---
# --- Fetch Batter Stats for Specific Pitch ---
def get_batter_performance_by_pitch(batter_name, pitcher_name, season="2025"):
    """
    Pulls the batter's performance data for specific pitches thrown by a pitcher.
    The function uses Statcast data to fetch performance for batter against each pitch type.
    """
    url = f"https://baseballsavant.mlb.com/stats/career?batter_name={batter_name}&pitcher_name={pitcher_name}&season={season}&type=batting"
    
    try:
        response = requests.get(url, timeout=5)  # 5 seconds timeout
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch batter performance for {batter_name} against {pitcher_name}. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return pd.DataFrame()  # Return empty DataFrame in case of error
        
        data = response.json()
        
        if data:
            df = pd.DataFrame(data['performance_by_pitch'])
            df['pitch_type'] = df['pitch_type'].apply(lambda x: x.strip())
            return df
        else:
            print(f"[ERROR] Empty response for batter performance of {batter_name} against {pitcher_name}.")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"[ERROR] Error fetching batter performance against {pitcher_name} for {batter_name}: {e}")
        return pd.DataFrame()

# --- Fetch Pitcher Stats from Statcast ---
def get_pitcher_arsenal_from_statcast(pitcher_name, season="2025"):
    """
    Pulls per-pitch-type performance data (Whiff%, PutAway%, etc.) for a given pitcher from Statcast.
    """
    url = f"https://baseballsavant.mlb.com/stats/career?player_name={pitcher_name}&season={season}&type=pitching"
    
    try:
        response = requests.get(url, timeout=5)  # 5 seconds timeout
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch pitch arsenal for {pitcher_name}. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return pd.DataFrame()  # Return empty DataFrame in case of error
        
        data = response.json()
        
        if 'arsenal' in data:
            df = pd.DataFrame(data['arsenal'])
            df['pitch_type'] = df['pitch_type'].apply(lambda x: x.strip())
            return df
        else:
            print(f"[ERROR] Arsenal data missing from Statcast response for {pitcher_name}.")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"[ERROR] Error fetching pitch arsenal for {pitcher_name}: {e}")
        return pd.DataFrame()


# --- Get Player ID using the Stats API ---
def get_player_id(first_name, last_name):
    search_url = f"https://statsapi.mlb.com/api/v1/people/search?names={first_name}%20{last_name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if data.get("people"):
            return data["people"][0]["id"]
    return None

# --- Calculate Advanced Pitching Metrics from Statcast Data ---
def calculate_advanced_pitching_metrics(stats):
    try:
        total_pitches = stats.get("numberOfPitches", 0)
        swinging_strikes = stats.get("swinging_strikes", 0)
        strikeouts = stats.get("strikeOuts", 0)
        batters_faced = stats.get("battersFaced", 0)
        two_strike_counts = stats.get("twoStrikeCounts", 0)

        # Whiff% Calculation
        whiff_rate = (swinging_strikes / total_pitches * 100) if total_pitches > 0 else 0

        # K% Calculation
        k_rate = (strikeouts / batters_faced * 100) if batters_faced > 0 else 0

        # PutAway% Calculation
        putaway_rate = (strikeouts / two_strike_counts * 100) if two_strike_counts > 0 else 0

        return {
            "BA": stats.get("BA", "N/A"),
            "SLG": stats.get("SLG", "N/A"),
            "wOBA": stats.get("wOBA", "N/A"),
            "Whiff%": round(whiff_rate, 2),
            "K%": round(k_rate, 2),
            "PutAway%": round(putaway_rate, 2)
        }
    except Exception as e:
        print(f"[ERROR] Failed to calculate pitching metrics: {e}")
        return {}

# --- Get Advanced Pitching Metrics for a Pitcher by Name ---
def get_pitcher_advanced_metrics_by_name(full_name, season="2025"):
    try:
        first, last = full_name.strip().split(" ", 1)
        player_id = get_player_id(first, last)
        if not player_id:
            return {}

        raw_stats = get_pitcher_arsenal_from_statcast(full_name, season)
        if not raw_stats.empty:
            return calculate_advanced_pitching_metrics(raw_stats)
        else:
            return {}
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch advanced pitching metrics for {full_name}: {e}")
        return {}

# --- Main function to fetch lineups and relevant stats ---
def fetch_game_lineups_and_stats(game_pk, season="2025"):
    # Use lineup_utils to get the lineups for the game
    away_lineup, home_lineup = get_live_lineup(game_pk, starters_only=True)

    away_pitcher = away_lineup[0]  # Assuming the first batter is the pitcher (just for example)
    home_pitcher = home_lineup[0]  # Same for home pitcher

    away_pitcher_metrics = get_pitcher_advanced_metrics_by_name(away_pitcher, season)
    home_pitcher_metrics = get_pitcher_advanced_metrics_by_name(home_pitcher, season)

    # Fetch performance of batters against the pitchers
    away_batter_performance = {batter: get_batter_performance_by_pitch(batter, home_pitcher, season) for batter in away_lineup}
    home_batter_performance = {batter: get_batter_performance_by_pitch(batter, away_pitcher, season) for batter in home_lineup}

    return {
        "away_pitcher_metrics": away_pitcher_metrics,
        "home_pitcher_metrics": home_pitcher_metrics,
        "away_batter_performance": away_batter_performance,
        "home_batter_performance": home_batter_performance
    }



# --- Get probable pitchers for a specific date ---
# --- Get probable pitchers for a specific date ---
def get_probable_pitchers_for_date(date_str):
    """
    Fetches the probable pitchers for a given date.
    It queries the MLB Stats API and returns a dictionary of probable pitchers.
    """
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    response = requests.get(url, timeout=5)  # 5 seconds timeout
    
    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch probable pitchers for {date_str}")
        return {}
    
    data = response.json()

    probable_pitchers = {}
    
    # Iterate over games to get the probable pitchers
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            home_team = game.get("home_name", "Unknown")
            away_team = game.get("away_name", "Unknown")
            
            # Try to get the probable pitchers, or fallback to 'Not Announced'
            home_pitcher = game["teams"]["home"].get("probablePitcher", {}).get("fullName", "Not Announced")
            away_pitcher = game["teams"]["away"].get("probablePitcher", {}).get("fullName", "Not Announced")

            # Create a key for this matchup
            key = f"{away_team} @ {home_team}"
            
            # Store the probable pitchers in the dictionary
            probable_pitchers[key] = {
                "home_pitcher": home_pitcher,
                "away_pitcher": away_pitcher
            }

    return probable_pitchers


def parse_boxscore(lines):
    teams = {}
    
    # The first line contains the headers, skip it
    header = lines[0]
    
    # Parse the data for each team (skipping the first line with headers)
    for line in lines[1:]:
        parts = line.split()
        team_name = parts[0]
        runs = int(parts[-3])  # R (Runs) is the third last column
        hits = int(parts[-2])  # H (Hits) is the second last column
        errors = int(parts[-1])  # E (Errors) is the last column
        
        teams[team_name] = {
            'runs': runs,
            'hits': hits,
            'errors': errors
        }
    # Output the parsed data

    return teams









def get_game_state(game_pk):
    try:
        game_data = statsapi.boxscore(game_pk)
        
        # Debug: Check if the API returned valid data
        print("Game Data:", game_data)

        if not game_data:
            print(f"[ERROR] No data returned for gamePk {game_pk}")
            return None

        inning = game_data.get("inning", "N/A")
        half = game_data.get("halfInning", "N/A")
        away_score = game_data["result"]["awayScore"]
        home_score = game_data["result"]["homeScore"]
        
        # Check if we got valid scores
        if home_score is None or away_score is None:
            print(f"[ERROR] Invalid scores: Home: {home_score}, Away: {away_score}")
            return None
        
        # Extract win probabilities
        home_win_probability = game_data["homeTeamWinProbability"]
        away_win_probability = game_data["awayTeamWinProbability"]
        
        game_state = {
            "inning": inning,
            "half": half,
            "away_score": away_score,
            "home_score": home_score,
            "home_win_probability": home_win_probability,
            "away_win_probability": away_win_probability
        }
        
        return game_state

    except Exception as e:
        print(f"[ERROR] Failed to fetch or parse game state for gamePk {game_pk}: {e}")
        return None

def render_scoreboard(game_pk):
    game_state = get_game_state(game_pk)
    
    # Debug: Check if we got valid game state
    print("Game State for Scoreboard:", game_state)

    if game_state:
        home_score = game_state.get("home_score", "N/A")
        away_score = game_state.get("away_score", "N/A")
        
        # Ensure valid data is passed to the scoreboard
        if home_score == "N/A" or away_score == "N/A":
            print("[ERROR] Missing score data for rendering scoreboard.")
            return

        # Render the scoreboard (for example purposes, printing it here)
        print(f"Scoreboard: Home Team: {home_score} - Away Team: {away_score}")
        
        # Further rendering logic...
    else:
        print("[ERROR] Could not retrieve valid game state to render scoreboard.")




    
    
# --- Fetch Live Game Lineups (with pitcher identification) ---
# --- Fetch Live Game Lineups (with pitcher identification) ---
def get_live_lineup(game_pk: int, starters_only=True):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    response = requests.get(url, timeout=5)  # 5 seconds timeout
    if not response.ok:
        return [], []

    data = response.json()
    away_players = data["teams"]["away"]["players"]
    home_players = data["teams"]["home"]["players"]

    def extract_active_lineup(players):
        lineup = []
        pitcher = None
        for pid, player in players.items():
            if "battingOrder" in player:
                order = int(player["battingOrder"])
                name = player["person"]["fullName"]
                pos = player.get("position", {}).get("abbreviation", "")
                if pos == "P":
                    pitcher = name  # Explicitly capture the pitcher
                lineup.append((order, f"{name} - {pos}"))

        lineup.sort(key=lambda x: x[0])
        return pitcher, [p for _, p in lineup[:9]] if starters_only else [p for _, p in lineup]

    # Extract pitcher and lineup
    away_pitcher, away_lineup = extract_active_lineup(away_players)
    home_pitcher, home_lineup = extract_active_lineup(home_players)

    return away_pitcher, home_pitcher, away_lineup, home_lineup



# --- Fetch Pitcher Stats from Statcast ---
def get_pitcher_arsenal_from_statcast(pitcher_name, season="2025"):
    """
    Pulls per-pitch-type performance data (Whiff%, PutAway%, etc.) for a given pitcher from Statcast.
    """
    url = f"https://baseballsavant.mlb.com/stats/career?player_name={pitcher_name}&season={season}&type=pitching"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data:
            if 'arsenal' in data:
                df = pd.DataFrame(data['arsenal'])
                # Clean up data, ensure it's in proper format
                df['pitch_type'] = df['pitch_type'].apply(lambda x: x.strip())
                return df
            else:
                print("[ERROR] Arsenal data missing from Statcast response.")
                return pd.DataFrame()
        else:
            print(f"[ERROR] Statcast response for {pitcher_name} failed with status {response.status_code}")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"[ERROR] Error fetching pitch arsenal for {pitcher_name}: {e}")
        return pd.DataFrame()

# --- Fetch Batter Performance by Pitch ---
def get_batter_performance_by_pitch(batter_name, pitcher_name, season="2025"):
    """
    Pulls the batter's performance data for specific pitches thrown by a pitcher from Statcast.
    """
    url = f"https://baseballsavant.mlb.com/stats/career?batter_name={batter_name}&pitcher_name={pitcher_name}&season={season}&type=batting"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data:
            if 'performance_by_pitch' in data:
                df = pd.DataFrame(data['performance_by_pitch'])
                df['pitch_type'] = df['pitch_type'].apply(lambda x: x.strip())
                return df
            else:
                print("[ERROR] Performance data missing from Statcast response.")
                return pd.DataFrame()
        else:
            print(f"[ERROR] Statcast response for {batter_name} vs {pitcher_name} failed with status {response.status_code}")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"[ERROR] Error fetching batter performance for {batter_name} against {pitcher_name}: {e}")
        return pd.DataFrame()



'''

# List of active MLB teams for 2025 (name or abbreviation)
MLB_TEAMS_2025 = [
    "Arizona Diamondbacks", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox", 
    "Chicago Cubs", "Chicago White Sox", "Cincinnati Reds", "Cleveland Indians", 
    "Colorado Rockies", "Detroit Tigers", "Houston Astros", "Kansas City Royals", 
    "Los Angeles Angels", "Los Angeles Dodgers", "Miami Marlins", "Milwaukee Brewers", 
    "Minnesota Twins", "New York Mets", "New York Yankees", "Oakland Athletics", 
    "Philadelphia Phillies", "Pittsburgh Pirates", "San Diego Padres", "San Francisco Giants", 
    "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers", 
    "Toronto Blue Jays", "Washington Nationals"
]

# Endpoint to get teams
teams_url = "https://statsapi.mlb.com/api/v1/teams"

def get_all_teams_2025():
    try:
        # Fetch all teams
        response = requests.get(teams_url)
        if response.status_code == 200:
            teams = response.json()['teams']
            # Filter teams that are in the 2025 season
            filtered_teams = [team for team in teams if team['name'] in MLB_TEAMS_2025]
            return filtered_teams
        else:
            print(f"Error fetching teams: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching teams: {e}")
        return []

# Endpoint to get the roster for a specific team by team_id
def get_roster_by_team(team_id):
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    try:
        response = requests.get(roster_url)
        if response.status_code == 200:
            return response.json()['roster']
        else:
            print(f"Error fetching roster for team {team_id}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching roster for team {team_id}: {e}")
        return []



def save_players_to_file(players_data):
    # Define the directory to store the players data
    players_dir = 'data/players'
    os.makedirs(players_dir, exist_ok=True)

    # Save the players data to a JSON file
    file_path = os.path.join(players_dir, 'players_by_team.json')
    with open(file_path, 'w') as f:
        json.dump(players_data, f, indent=4)

    print("[✓] Saved player data to players_by_team.json")

def get_all_players_for_selected_teams():
    teams = get_all_teams_2025()
    all_players = {}
    
    for team in teams:
        team_name = team['name']
        team_id = team['id']
        
        print(f"Fetching roster for {team_name}...")
        
        # Get the roster for each team
        roster = get_roster_by_team(team_id)
        
        # Fetch player names and IDs
        all_players[team_name] = [
            {"name": player['person']['fullName'], "id": player['person']['id']} for player in roster
        ]
    
    save_players_to_file(all_players)  # Save player data to file
    return all_players

'''