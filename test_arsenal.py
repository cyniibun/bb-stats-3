import requests

# Replace with the player ID you want to test
player_id = '694973'  # Example player ID, replace it with a valid ID

# Define the base URL for the API
base_url = f"https://statsapi.mlb.com/api/v1/pitcher/{player_id}/arsenal"

# Make a request to the API
response = requests.get(base_url)

# Check if the request was successful (HTTP 200)
if response.status_code == 200:
    print("Pitcher Arsenal Data:")
    # Print out the JSON response if successful
    pitcher_data = response.json()
    print(pitcher_data)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
    print(f"Error: {response.text}")
