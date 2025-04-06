import time
import statsapi

def refresh_player_data(game_id):
    d=statsapi.boxscore_data(game_id)

# Example usage: refresh player data for game ID '778458'
refresh_player_data(778458)
