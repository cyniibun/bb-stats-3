import statsapi
import json
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def fetch_game_data(game_pk):
    """Fetches game data for the given gamePk."""
    try:
        print(f"[DEBUG] Fetching game data for gamePk: {game_pk}")
        # Fetch the game data from statsapi using the correct endpoint
        game_data = statsapi.boxscore_data(game_pk)
        if not game_data:
            print(f"[ERROR] No game data found for gamePk {game_pk}")
            return None
        print(f"[DEBUG] Game data successfully fetched for gamePk {game_pk}")
        return game_data
    except Exception as e:
        print(f"[ERROR] Failed to fetch game data for gamePk {game_pk}: {e}")
        return None


def extract_player_ids(game_data):
    """Extracts player IDs from home and away teams."""
    try:
        home_players = game_data.get('home', {}).get('players', {})
        away_players = game_data.get('away', {}).get('players', {})

        # Debugging the extracted data
        print(f"[DEBUG] Home players: {home_players}")
        print(f"[DEBUG] Away players: {away_players}")

        # If the home or away player data is missing or empty
        if not home_players:
            print(f"[ERROR] Missing home players in the game data.")
        if not away_players:
            print(f"[ERROR] Missing away players in the game data.")

        # Extract player IDs for both teams
        home_player_ids = [player_info.get("person", {}).get("id") for player_info in home_players.values() if player_info.get("person")]
        away_player_ids = [player_info.get("person", {}).get("id") for player_info in away_players.values() if player_info.get("person")]

        # Print out the IDs for both home and away teams
        print(f"[DEBUG] Home team player IDs: {home_player_ids}")
        print(f"[DEBUG] Away team player IDs: {away_player_ids}")

        return home_player_ids, away_player_ids
    except Exception as e:
        print(f"[ERROR] Failed to extract player IDs: {e}")
        return [], []


def fetch_and_print_player_ids(game_pk):
    """Fetches and prints the player IDs for a given gamePk."""
    game_data = fetch_game_data(game_pk)
    if game_data:
        home_player_ids, away_player_ids = extract_player_ids(game_data)
        
        # Print the player IDs to the console
        print(f"\nHome Team Player IDs: {home_player_ids}")
        print(f"Away Team Player IDs: {away_player_ids}")
        
        # Save the output to a text file
        try:
            with open("player_ids_output.txt", "w") as file:
                file.write(f"Home Team Player IDs: {json.dumps(home_player_ids, indent=2)}\n\n")
                file.write(f"Away Team Player IDs: {json.dumps(away_player_ids, indent=2)}\n")
            print("[DEBUG] Player IDs successfully written to 'player_ids_output.txt'.")
        except Exception as e:
            print(f"[ERROR] Failed to write player IDs to file: {e}")
    else:
        print(f"[ERROR] No game data available for gamePk {game_pk}")





'''
# You can now call this function from any other file by passing in the desired `gamePk` value
# For example, to call the function with a dynamic gamePk:
if __name__ == "__main__":
    game_pk = 778440  # Replace with dynamic gamePk as needed
    fetch_and_print_player_ids(game_pk)
'''