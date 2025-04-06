import statsapi




#def teamid_from_boxscore(gameid)
#statsapi.boxscore_data(gameid)
def get_last_game(team_id):
    last_game = statsapi.last_game(team_id)
    
    last_game_data = statsapi.boxscore_data(last_game)
    

    #print(last_game_data)


    home_team_id = last_game_data['teamInfo']['home']['id']
    away_team_id = last_game_data['teamInfo']['away']['id']

    # Now check which team the input team_id corresponds to
    if team_id == home_team_id:
        team_data = last_game_data.get("home", {})
    elif team_id == away_team_id:
        team_data = last_game_data.get("away", {})
    else:
        raise ValueError("Invalid team ID provided.")
    
    # Continue with processing the team data
    print(team_data)

    batting_order = list(team_data.get("battingOrder", []))

    print(batting_order)

    return batting_order

    




get_last_game(114)

