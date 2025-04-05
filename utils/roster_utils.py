import json
import os
from utils.mlb_api import get_player_statcast_data_by_id

def load_rosters_from_file():
    rosters_dir = 'data/rosters'
    rosters = {}

    for filename in os.listdir(rosters_dir):
        if filename.endswith("_roster.json"):
            team_name = filename.split("_")[0]
            file_path = os.path.join(rosters_dir, filename)
            
            with open(file_path, 'r') as f:
                roster_data = json.load(f)
                rosters[team_name] = roster_data
    
    return rosters


'''
def fetch_player_stats(player_ids):
    player_stats = []

    for player_id in player_ids:
        stats = get_player_statcast_data_by_id(player_id)
        if stats is not None:
            player_stats.append({
                "player_id": player_id,
                "player_name": stats.get("player_name", "Unknown"),
                "PA": stats.get("PA", 0),
                "BA": stats.get("BA", 0),
                "SLG": stats.get("SLG", 0),
                "wOBA": stats.get("wOBA", 0),
                "K%": stats.get("K%", 0),
                "Whiff%": stats.get("Whiff%", 0),
                "PutAway%": stats.get("PutAway%", 0)
            })
    
    return player_stats
'''