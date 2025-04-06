import pybaseball
from datetime import datetime, timedelta
import statsapi

def scheduletest():
    schedule = statsapi.schedule('2025-04-06', game_id=778431)
    
    # Iterate through each game in the schedule (though in this case it's just one game)
    for game in schedule:
        home_probable_pitcher = game.get('home_probable_pitcher', 'Unknown')
        away_probable_pitcher = game.get('away_probable_pitcher', 'Unknown')

        print(f"Home Probable Pitcher: {home_probable_pitcher}")
        print(f"Away Probable Pitcher: {away_probable_pitcher}")

# Call the function to test
scheduletest()










'''
# Get yesterday's date for start_dt
start_date = ('2024-01-01')
today = datetime.today().strftime('%Y-%m-%d')


player_id = 515676

# Fetch the data using pybaseball for yesterday to today
stats = pybaseball.statcast_pitcher(start_date, today, player_id)

# Check if the data is empty
if stats.empty:
    print("No data returned for 515676 from yesterday.")
else:
    # Save the data to a CSV file if it's not empty
    file_path = 'braking_us_stats_2024_to_today.csv'
    stats.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")


'''
