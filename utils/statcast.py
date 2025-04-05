import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
from utils.mlb_api import get_all_mlb_players  # Assuming this function gets all MLB player IDs

# Output directory
DATA_DIR = Path("data/player_stats")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_stats_to_csv(data, filename):
    """ Save the fetched data to a CSV file in the player_stats directory """
    file_path = DATA_DIR / filename
    data.to_csv(file_path, index=False)
    print(f"[✓] Saved: {file_path}")

def get_player_stats(player_id, player_type):
    """ Get player stats for both batters and pitchers """
    if player_type == 'batter':
        url = f"https://baseballsavant.mlb.com/stats/career?batter_name={player_id}"
    else:
        url = f"https://baseballsavant.mlb.com/stats/career?player_name={player_id}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"[ERROR] Failed to fetch stats for {player_id}")
            return None
    except Exception as e:
        print(f"[ERROR] Error fetching stats for {player_id}: {e}")
        return None

def pull_and_save_player_stats():
    print(f"📊 Running stat pull @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get all MLB players (both batters and pitchers)
    all_players = get_all_mlb_players()  # Assuming this returns a dictionary of player IDs

    # Pull stats for batters
    all_batter_data = []
    for batter_id in all_players["batters"]:
        batter_stats = get_player_stats(batter_id, 'batter')
        if batter_stats:
            all_batter_data.append(batter_stats)

    df_batters = pd.DataFrame(all_batter_data)
    save_stats_to_csv(df_batters, f"batters_stats_{datetime.today().date()}.csv")

    # Pull stats for pitchers
    all_pitcher_data = []
    for pitcher_id in all_players["pitchers"]:
        pitcher_stats = get_player_stats(pitcher_id, 'pitcher')
        if pitcher_stats:
            all_pitcher_data.append(pitcher_stats)

    df_pitchers = pd.DataFrame(all_pitcher_data)
    save_stats_to_csv(df_pitchers, f"pitchers_stats_{datetime.today().date()}.csv")

    print("✅ Stat pull complete.")

if __name__ == "__main__":
    pull_and_save_player_stats()
