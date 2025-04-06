import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import streamlit as st
import statsapi
from utils.metrics_table_util import generate_player_metrics_table  # Assuming you have a utility to generate the tables
#from utils.stat_utils import get_pitcher_stats
from utils.calculate_util import calculate_metrics
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Streamlit page configuration
st.set_page_config(page_title="Game View", layout="wide")


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

# Display the basic game information
#st.write(f"Home Team: {home_team}")
#st.write(f"Away Team: {away_team}")
#st.write(f"Game ID: {game_id}")
#st.write(f"Game Time: {game_time}")


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
async def fetch_game_data(game_id):
    try:
        game_data = statsapi.boxscore_data(game_id)
        if game_data:
            home_team_data = game_data.get("home", {})
            home_team_id = home_team_data.get('team', {}).get('id', None)
            st.write(home_team_id)
            away_team_id = away_team_data.get('team', {}).get('id', None)
            st.write(away_team_id)
            away_team_data = game_data.get("away", {})
            player_info = game_data.get("playerInfo", {})
            logging.debug(f"Got Home Away Data and player info")

            if isinstance(home_team_data, dict) and isinstance(away_team_data, dict):
                # Make sure these variables are always lists, not sets or strings.
                home_batting_order = list(home_team_data.get("battingOrder", []))
                away_batting_order = list(away_team_data.get("battingOrder", []))
                home_pitchers = list(home_team_data.get("pitchers", []))
                away_pitchers = list(away_team_data.get("pitchers", []))
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
                # Determine the total number of player IDs and set max_count

                
                

                # Now calculate max_count safely
                max_count = len(home_batting_order + away_batting_order + home_pitchers + away_pitchers + home_bench + away_bench + home_bullpen + away_bullpen)
                logging.debug(f"max count: {max_count}")
                

                counter = 0


                # Initialize player_names dictionary to store player names
                async def get_player_names(player_list, team_key):
                    nonlocal counter
                    for player_id in player_list:
                        if player_id:
                            if counter >= max_count:
                                break

                            # Get player name using the player ID
                            player_name = player_info.get(f"ID{player_id}", {}).get("fullName", "Unknown")
                            player_names[team_key][str(player_id)] = player_name
                            counter += 1
                            logging.debug(f"counter: {counter}")

                # Using asyncio.gather to run tasks concurrently
                await asyncio.gather(
                    get_player_names(home_batting_order, 'home_batting'),
                    get_player_names(away_batting_order, 'away_batting'),
                    get_player_names(home_pitchers, 'home_pitchers'),
                    get_player_names(away_pitchers, 'away_pitchers'),
                    get_player_names(home_bench, 'home_bench'),
                    get_player_names(away_bench, 'away_bench'),
                    get_player_names(home_bullpen, 'home_bullpen'),
                    get_player_names(away_bullpen, 'away_bullpen')
                )


                # Get player names for each category
                get_player_names(home_batting_order,'home_batting')
                get_player_names(away_batting_order,'away_batting')
                get_player_names(home_pitchers,'home_pitchers')
                get_player_names(away_pitchers,'away_pitchers')
                get_player_names(home_bench,'home_bench')
                get_player_names(away_bench,'away_bench')
                get_player_names(home_bullpen,'home_bullpen')
                get_player_names(away_bullpen,'away_bullpen')

                logging.debug(f"player names: {player_names}")

                stat_counter = 0
                max_count = 52
                player_metrics_combined = {}
                

                # Track progress with the player stats
                async def get_stats_for_player(player_list, player_type):
                    nonlocal stat_counter, max_count
                    futures = []
                    for player_id in player_list:
                        if player_id:
                            futures.append(executor.submit(calculate_metrics, player_id, start_date, end_date, player_type))
                    
                    # Await the results of the tasks
                    results = await asyncio.gather(*futures)

                    for i, result in enumerate(results):
                        if result:
                            player_metrics_combined[player_list[i]] = result
                            logging.debug(f"Stats for player {player_list[i]}: {result}")
                        else:
                            st.write(f"Warning: No stats found for player {player_list[i]} ({player_type})")

                

                

                print('Initializing stat counter')
                
                batting_counter_max = len(home_batting_order + away_batting_order + home_bench + away_bench)

                print("batting counter max")
                print(batting_counter_max)

                pitching_counter_max = len(home_pitchers + away_pitchers + home_bullpen + away_bullpen)
                print("pitching counter max")
                print(pitching_counter_max)

                
                
                while batting_counter_max > 0:
                    logging.debug("getting batter stats")
                    await get_stats_for_player(home_batting_order + away_batting_order + home_bench + away_bench, 'batter')
                    batting_counter_max -= 1  # Decrement after each pass
                    logging.debug(f"batting_counter_max: {batting_counter_max}")
                
                while pitching_counter_max > 0:
                    logging.debug("getting pitcher stats")
                    await get_stats_for_player(home_pitchers + away_pitchers + home_bullpen + away_bullpen, 'pitcher')
                    pitching_counter_max -= 1  # Decrement after each pass
                    logging.debug(f"pitching_counter_max: {pitching_counter_max}")
                    st.write([player_names])

                #asyncio.run(fetch_player_stats())



#####################
# RENDERING SECTION #
#####################




                # Render Game Time
                st.write(f"### Game Time: {game_time}")

                # Add a space between game time and the teams
                st.markdown("---")

                home_pitcher = home_pitchers[0] if home_pitchers else 'Unknown'
                away_pitcher = away_pitchers[0] if away_pitchers else 'Unknown'

                # If no pitchers are found, use the schedule API to fetch the probable pitchers
                if home_pitcher == 'Unknown' or away_pitcher == 'Unknown':
                    
                    # Fetch the schedule for the given game date and game_id
                    schedule = statsapi.schedule('2025-04-06', game_id=game_id)
                    
                    for game in schedule:
                        home_pitcher = game.get('home_probable_pitcher', 'Unknown')
                        away_pitcher = game.get('away_probable_pitcher', 'Unknown')

                # Add two columns below the game time to show teams
                col1, col2 = st.columns([1, 1])

                # Render away team in the left column
                with col1:
                    st.write(f"## Away Team: {away_team}")
                    st.write(f"#### Pitcher: {away_pitcher}")

                    # Example of rendering the batting stats for the away team
                    st.write(f"##### Batting Stats for Away Team")
                    for player_id in player_ids['away_batting']:
                        player_name = player_names['away_batting'].get(str(player_id), "Unknown")  # Fetch the name from the dictionary using player ID
                        st.write(f"{player_name} (ID: {player_id})")



                    # Render more stats as needed, e.g., calculate_metrics(player_id)
                    
                # Render home team in the right column
                with col2:
                    st.write(f" ")
                    st.write(f"## Home Team: {home_team}")
                    st.write(f"#### Pitcher: {home_pitcher}")

                    # Example of rendering the batting stats for the home team
                    st.write(f"#### Batting Stats for Home Team")
                    if len(player_ids['home_batting']) == 0:
                        st.write(f"#Lineups unavailable")
                    for player_id in player_ids['home_batting']:
                        player_name = player_names['home_batting'].get(str(player_id), "Unknown")  # Fetch the name from the dictionary using player ID
                        st.write(f"{player_name} (ID: {player_id})")

                

                            









            else:
                st.write("Invalid game data format.")
        else:
            st.write("No data found for this game.")
    except Exception as e:
        st.error(f"Error fetching game data: {e}")

# If game_id is provided, fetch and display game data
if game_id:
    asyncio.create_task(fetch_game_data(game_id))





