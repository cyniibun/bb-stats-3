import json
import os

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
