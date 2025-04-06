import statsapi
from datetime import datetime, timedelta
import pytz
import json



# --- Helper function to validate date format ---
def validate_date_format(date_string: str):
    """Validate the format of a date string (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_string, "%Y-%m-%d")  # Ensure it's a valid date format
        return True
    except ValueError:
        print(f"Invalid date format: {date_string}")
        return False

# --- Get games for a specific date or range ---
def get_game_lineups(game_date: str):
    """Fetches all scheduled games for a given date."""
    if not validate_date_format(game_date):
        return {}

    try:
        games = statsapi.schedule(date=game_date)
        
        # Check if the response is empty or non-JSON
        if isinstance(games, str):
            print("Received string data, cannot parse as JSON.")
            return {}

        if not games:
            print(f"No games found for {game_date}")
            return {}

        lineup_data = {}
        for game in games:

            print(f"Game details: {game}")  # Inspect the full game data to see if 'home_players' and 'away_players' are present

            try:
                # Retrieve home and away team names and IDs directly from the game data
                home = game.get("home_name")
                away = game.get("away_name")
                home_id = game.get("home_id")
                away_id = game.get("away_id")
                game_pk = game.get("game_id")

                if home and away and home_id and away_id:
                    lineup_data[f"{away} @ {home}"] = {
                        "gamePk": game_pk,
                        "home": home,
                        "away": away,
                        "home_id": home_id,
                        "away_id": away_id
                    }
                    # Debugging: print the player info after pulling it
                    home_players = game.get("home_players", [])
                    away_players = game.get("away_players", [])
                    print(f"Home Players: {home_players}")
                    print(f"Away Players: {away_players}")
                else:
                    print(f"Missing some game data for game {game_pk}")
            except KeyError as e:
                print(f"KeyError: {e} in game {game}")
                continue
        return lineup_data

    except Exception as e:
        print(f"Error retrieving game data: {e}")
        return {}


# --- Pull initial boxscore lineup (starters only) ---
def get_lineup_for_game(game_pk):
    """Fetches the boxscore lineup for a game, including starters only."""
    print(f"Fetching lineup for gamePk: {game_pk}")  
    game_data = statsapi.boxscore_data(game_pk)
    
    # Check if game data is returned correctly and is not a string
    if isinstance(game_data, str):
        print("Received string data, cannot parse as JSON.")
        return [], []
    
    if not game_data:
        print(f"No game data found for gamePk: {game_pk}")  
        return [], []

    print(f"Fetched game data: {game_data}")  
    
    # Assuming 'home_id' and 'away_id' are provided as part of the response
    home_players = game_data.get('home', {}).get('players', {})
    away_players = game_data.get('away', {}).get('players', {})

    # Debugging to check players data
    print("Home players:", home_players)
    print("Away players:", away_players)
    

    # Extract batters, pitchers, bench, and bullpen for home and away teams
    def extract_player_info(team_players, team_id):
        """Extract the relevant player info for batters, pitchers, bench, and bullpen."""
        batters = team_players.get('battingOrder', [])
        pitchers = team_players.get('pitchers', [])
        bench = team_players.get('bench', [])
        bullpen = team_players.get('bullpen', [])
        
        # Debugging the extracted data
        print(f"Extracted for team {team_id}:")
        print(f"Batters: {batters}")
        print(f"Pitchers: {pitchers}")
        print(f"Bench: {bench}")
        print(f"Bullpen: {bullpen}")
        
        # Player IDs for batters (must ensure they match with battingOrder)
        player_ids = team_players.get('batters', [])
        # Debugging the player_ids mapping
        print(f"Player IDs for batters: {player_ids}")
        
        return {
            "batters": batters,
            "pitchers": pitchers,
            "bench": bench,
            "bullpen": bullpen,
            "player_ids": player_ids
        }

    # Extract information for both away and home teams
    away_team_info = extract_player_info(away_players, 'away')
    home_team_info = extract_player_info(home_players, 'home')

    print(f"Away Team Info: {away_team_info}")
    print(f"Home Team Info: {home_team_info}")

    # Assuming we only want batters (with their batting order)
    def map_batting_order_with_ids(batting_order, player_ids):
        """Map the batting order numbers to the player ids."""
        mapped_batting_order = []
        for order in batting_order:
            try:
                player_id = player_ids[order // 100 - 1]  # Since battingOrder are in increments of 100
                mapped_batting_order.append(player_id)
            except IndexError:
                print(f"Error: Index out of bounds while mapping batting order {order} to player_ids.")
                continue
        return mapped_batting_order

    # Map batting order to player IDs
    away_batting_order = map_batting_order_with_ids(away_team_info['batters'], away_team_info['player_ids'])
    home_batting_order = map_batting_order_with_ids(home_team_info['batters'], home_team_info['player_ids'])

    # Debugging to verify the final lineup data
    print(f"Away Batting Order with Player IDs: {away_batting_order}")
    print(f"Home Batting Order with Player IDs: {home_batting_order}")

    return away_batting_order, home_batting_order
