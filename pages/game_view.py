import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(sys.path)

#import warnings
import logging
import streamlit as st
import statsapi
from utils.metrics_table_util import generate_player_metrics_table  # Assuming you have a utility to generate the tables
#from utils.stat_utils import get_pitcher_stats
from utils.calculate_util import calculate_metrics
import utils.last_lineup
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

#warnings.filterwarnings('ignore', message='.st.experimental_get_query_params.*')

# Streamlit page configuration
st.set_page_config(page_title="Game View", layout="wide")

global home_lineup_flag
global away_lineup_flag
global home_pitchers_flag
global away_pitchers_flag


home_lineup_flag = 0
away_lineup_flag = 0
home_pitchers_flag = 0
away_pitchers_flag = 0

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # For console output
    ]
)

executor = ThreadPoolExecutor(max_workers=10)

# Fetch the raw query string
raw_query = st.experimental_get_query_params()  # Raw query params without any processing
home_team = raw_query.get('home', ['Unknown'])[0]
away_team = raw_query.get('away', ['Unknown'])[0]
game_id = raw_query.get('game_id', ['Unknown'])[0]
game_time = raw_query.get('time', ['Unknown'])[0]



# Global dictionary to store player IDs for future use
player_ids = {
    'home_batting': [],
    'away_batting': [],
    'home_pitchers': [],
    'away_pitchers': [],
    'home_bullpen': [],
    'away_bullpen': [],
    'home_bench': [],
    'away_bench': []
}

# Initialize player_names dictionary to store player names
player_names = {
    'home_batting': {},
    'away_batting': {},
    'home_pitchers': {},
    'away_pitchers': {},
    'home_bullpen': {},
    'away_bullpen': {},
    'home_bench': {},
    'away_bench': {}
}

start_date = '2024-01-01'
end_date = datetime.today().strftime('%Y-%m-%d')

# Fetch game data using the game_id
@st.cache_resource
def fetch_game_data(game_id):
    try:
        game_data = statsapi.boxscore_data(game_id)
        #st.write(game_data)
        if game_data:
            home_team_data = game_data.get("home", {})
            away_team_data = game_data.get("away", {})
            home_team_id = home_team_data.get('team', {}).get('id', None)
            #st.write(home_team_id)
            away_team_id = away_team_data.get('team', {}).get('id', None)
            #st.write(away_team_id)
            player_info = game_data.get("playerInfo", {})
            logging.debug(f"Got Home Away Data and player info")

            if isinstance(home_team_data, dict) and isinstance(away_team_data, dict):
                # Make sure these variables are always lists, not sets or strings.
                home_batting_order = list(home_team_data.get("battingOrder", []))
                if len(home_batting_order) == 0:
                    home_batting_order=list(get_last_batting_order(home_team_id))
                    home_lineup_flag = 1
                    print(home_batting_order)
                else:
                    return

                away_batting_order = list(away_team_data.get("battingOrder", []))
                if len(away_batting_order) == 0:
                    away_batting_order=list(get_last_batting_order(away_team_id))
                    away_lineup_flag = 1
                else:
                    return


                home_pitchers = list(home_team_data.get("pitchers", []))

                away_pitchers = list(away_team_data.get("pitchers", []))

                home_pitcher = home_pitchers[0] if home_pitchers else 'Unknown'
                away_pitcher = away_pitchers[0] if away_pitchers else 'Unknown'

                # If no pitchers are found, use the schedule API to fetch the probable pitchers
                if home_pitcher == 'Unknown' or away_pitcher == 'Unknown':
                    
                    # Fetch the schedule for the given game date and game_id
                    schedule = statsapi.schedule('2025-04-06', game_id=game_id)
                    
                    for game in schedule:
                        home_pitcher = game.get('home_probable_pitcher', 'Unknown')
                        away_pitcher = game.get('away_probable_pitcher', 'Unknown')
                        print('probable pitchers: ')
                        print(f"Away: " - {away_pitcher})
                        print(f"Home: " - {home_pitcher})

                home_bench = list(home_team_data.get("bench", []))
                away_bench = list(away_team_data.get("bench", []))
                home_bullpen = list(home_team_data.get("bullpen", []))
                away_bullpen = list(away_team_data.get("bullpen", []))

                # Fill player_ids dictionary
                player_ids['home_batting'] = home_batting_order
                player_ids['away_batting'] = away_batting_order
                player_ids['home_pitchers'] = home_pitchers
                player_ids['away_pitchers'] = away_pitchers
                player_ids['home_bench'] = home_bench
                player_ids['away_bench'] = away_bench
                player_ids['home_bullpen'] = home_bullpen
                player_ids['away_bullpen'] = away_bullpen
                logging.debug(f"Player IDs {home_batting_order} - {away_batting_order} - {home_pitchers} - {away_pitchers} - {home_bench} - {away_bench} - {home_bullpen} - {away_bullpen}")

                # Now calculate max_count safely
                max_count = len(home_batting_order + away_batting_order + home_pitchers + away_pitchers + home_bench + away_bench + home_bullpen + away_bullpen)
                logging.debug(f"max count: {max_count}")
                counter = 0

                # Initialize player_names dictionary to store player names
                def get_player_names(player_list, team_key):
                    nonlocal counter
                    for player_id in player_list:
                        if player_id:  # Skip invalid player IDs
                            # Check if we've reached max_count
                            if counter >= max_count:
                                break

                            # Retrieve the player name based on player_id
                            player_name = player_info.get(f"ID{player_id}", {}).get("fullName", "Unknown")
                            logging.debug(f"Got player name for ID {player_id}: {player_name}")
                            
                            # Instead of appending to player_names, store the name linked to the player_id
                            player_names[team_key][player_id] = player_name

                            counter += 1  # Increment the counter
                            logging.debug(f"counter: {counter}")

                # Get player names for each category
                get_player_names(home_batting_order,'home_batting')
                get_player_names(away_batting_order,'away_batting')
                get_player_names(home_pitchers,'home_pitchers')
                get_player_names(away_pitchers,'away_pitchers')
                get_player_names(home_bench,'home_bench')
                get_player_names(away_bench,'away_bench')
                get_player_names(home_bullpen,'home_bullpen')
                get_player_names(away_bullpen,'away_bullpen')

                #st.write(player_names)

                stat_counter = 0
                max_count = 52
                player_metrics_combined = {}

                # Track progress with the player stats
                def get_stats_for_player(player_list, player_type):
                    nonlocal stat_counter
                    for stat_counter, player_id in enumerate(player_list):
                        if stat_counter >= max_count:  # Break once we reach the max_count
                            break
                        if player_id:  # Skip invalid player IDs
                            stats = calculate_metrics(player_id, start_date, end_date, player_type)
                            stat_counter += 1
                            logging.debug(f"stat counter {stat_counter}")
                            if stats:
                                player_metrics_combined[player_id] = stats
                            else:
                                st.write(f"Warning: No stats found for player {player_id} ({player_type})")

                print('Initializing stat counter')
                
                batting_counter_max = len(home_batting_order + away_batting_order + home_bench + away_bench)
                print("batting counter max")
                print(batting_counter_max)

                pitching_counter_max = len(home_pitchers + away_pitchers + home_bullpen + away_bullpen)
                print("pitching counter max")
                print(pitching_counter_max)

                pitching_counter = 0
                batting_counter = 0

                if batting_counter < batting_counter_max:
                    logging.debug("getting batter stats")
                    get_stats_for_player(home_batting_order + away_batting_order + home_bench + away_bench, 'batter')
                    batting_counter += 1
                else:
                    print("got all batter stats")
                    return

                if pitching_counter < pitching_counter_max:
                    print("getting pitcher stats")
                    get_stats_for_player(home_pitchers + away_pitchers + home_bullpen + away_bullpen, 'pitcher')
                    pitching_counter += 1
                else:
                    print("got all pitcher stats")
                    return

                #st.write(player_metrics_combined)

                # Render Game Time
                st.write(f"### Game Time: {game_time}")

                # Add a space between game time and the teams
                st.markdown("---")

                

                # Add two columns below the game time to show teams
                col1, col2 = st.columns([1, 1])

                # Render away team in the left column
                with col1:
                    st.write(f"## Away Team: {away_team}")
                    st.write(f"#### Pitcher: {away_pitcher}")

                    # Example of rendering the batting stats for the away team
                    st.write(f"##### Batting Stats for Away Team")
                    for player_id, player_name in zip(player_ids['away_batting'], player_names['away_batting'].values()):
                        st.write(f"{player_name} (ID: {player_id})")
                    # Render more stats as needed, e.g., calculate_metrics(player_id)
                    
                # Render home team in the right column
                with col2:
                    st.write(f" ")
                    st.write(f"## Home Team: {home_team}")
                    st.write(f"### Pitcher: {home_pitcher}")

                    # Example of rendering the batting stats for the home team
                    st.write(f"#### Batting Stats for Home Team")
                    for player_id, player_name in zip(player_ids['home_batting'], player_names['home_batting'].values()):
                        st.write(f"{player_name} (ID: {player_id})")
                        # Render more stats as needed, e.g., calculate_metrics(player_id)

            else:
                st.write("Invalid game data format.")
        else:
            st.write("No data found for this game.")
    except Exception as e:
        st.error(f"Error fetching game data: {e}")

# If game_id is provided, fetch and display game data using the existing event loop
if game_id:
    fetch_game_data(game_id)

    