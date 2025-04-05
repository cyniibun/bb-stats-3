import json
import os

# Assuming get_all_players_for_selected_teams() is already defined elsewhere
from utils.mlb_api import get_all_players_for_selected_teams

def save_roster_to_file(team_name, roster_data):
    # Create the directory for storing rosters if it doesn't exist
    rosters_dir = 'data/rosters'
    os.makedirs(rosters_dir, exist_ok=True)

    # Define the file path to save the team roster (using team name as filename)
    file_path = os.path.join(rosters_dir, f"{team_name}_roster.json")

    # Save roster data to a JSON file
    with open(file_path, 'w') as f:
        json.dump(roster_data, f, indent=4)
    print(f"[✓] Saved roster for {team_name} to {file_path}")

def get_all_mlb_players():
    # Fetch players data
    all_players = get_all_players_for_selected_teams()

    # Process the roster data correctly
    players = {
        "batters": [],
        "pitchers": [],
    }

    for team, roster in all_players.items():
        # Saving roster data locally
        save_roster_to_file(team, roster)

        for player in roster:
            if isinstance(player, dict) and "position" in player:
                if player["position"] in {"P", "SP", "RP"}:
                    players["pitchers"].append(player["person"]["id"])
                else:
                    players["batters"].append(player["person"]["id"])

    return players
