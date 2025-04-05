# lineup_utils.py
import requests
from datetime import datetime, timedelta
import pytz

# --- Get games for a specific date ---
def get_game_lineups(game_date: str):
    url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={game_date}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return {}

    games = resp.json().get("dates", [])[0].get("games", [])
    lineup_data = {}
    for game in games:
        home = game["teams"]["home"]["team"]["name"]
        away = game["teams"]["away"]["team"]["name"]
        game_pk = game["gamePk"]
        lineup_data[f"{away} @ {home}"] = {
            "gamePk": game_pk,
            "home": home,
            "away": away
        }
    return lineup_data

# --- Extract boxscore lineups (partial data for starters) ---
def get_lineup_for_game(game_pk: int):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None, None

    data = resp.json()
    home_players = data['teams']['home']['players']
    away_players = data['teams']['away']['players']

    def extract_lineup(players):
        lineup = []
        for pid, player in players.items():
            try:
                pos = player['position']['abbreviation']
                if pos in ["P", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "C"]:
                    lineup.append(f"{player['person']['fullName']} - {pos}")
            except:
                continue
        return lineup

    return extract_lineup(away_players), extract_lineup(home_players)

# --- Pull live game lineups (includes real-time battingOrder) ---


def get_live_lineup(game_pk: int, starters_only=True):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    resp = requests.get(url)
    if not resp.ok:
        return [], []

    data = resp.json()
    away_players = data["teams"]["away"]["players"]
    home_players = data["teams"]["home"]["players"]

    def extract_active_lineup(players):
        lineup = []
        for pid, player in players.items():
            if "battingOrder" in player:
                order = int(player["battingOrder"])
                name = player["person"]["fullName"]
                pos = player.get("position", {}).get("abbreviation", "")
                lineup.append((order, f"{name} - {pos}"))

        lineup.sort(key=lambda x: x[0])
        return [p for _, p in lineup[:9]] if starters_only else [p for _, p in lineup]

    return extract_active_lineup(away_players), extract_active_lineup(home_players)





# --- Pull official lineups with fallback and EST-based decision logic ---
def get_official_lineups(game_pk):
    # Use EST time window to determine reliability
    eastern = pytz.timezone("US/Eastern")
    now_est = datetime.now(pytz.utc).astimezone(eastern)

    # Fetch game preview
    preview_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    resp = requests.get(preview_url)
    if not resp.ok:
        return get_lineup_for_game(game_pk)

    data = resp.json()
    status = data.get("gameData", {}).get("status", {})
    game_time_str = data.get("gameData", {}).get("datetime", {}).get("dateTime")
    if not game_time_str:
        return get_lineup_for_game(game_pk)

    # Parse official scheduled time (EST)
    game_dt_utc = datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))
    game_time_est = game_dt_utc.astimezone(eastern)

    is_live = status.get("abstractGameState") in ["Live", "In Progress"]
    is_within_window = now_est >= game_time_est - timedelta(minutes=90)

    # Try live lineup if live or inside official window
    if is_live or is_within_window:
        away, home = get_live_lineup(game_pk)
        if away and home:
            return away, home

    # Fallback
    return get_lineup_for_game(game_pk)
