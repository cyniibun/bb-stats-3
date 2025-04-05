import os
import json
import requests
from datetime import datetime
import pandas as pd

CACHE_DIR = "cached_schedules"

def fetch_schedule_by_date(date, force_refresh=False):
    date_str = date.strftime("%Y-%m-%d")
    cache_file = os.path.join(CACHE_DIR, f"{date_str}.json")

    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load cache for {date_str}: {e}")

    print(f"[FETCHING] Using MLB API for {date_str}")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
    try:
        response = requests.get(url)
        data = response.json()

        games = []
        for date_data in data.get("dates", []):
            for game in date_data.get("games", []):
                games.append({
                    "gamePk": game.get("gamePk"),
                    "home": game["teams"]["home"]["team"]["name"],
                    "opponent": game["teams"]["away"]["team"]["name"],
                    "time": game.get("gameDate", ""),
                    "status": game.get("status", {}).get("detailedState", "")
                })

        # Cache result
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(games, f)

        print(f"[CACHED] {len(games)} games saved for {date_str}")
        return games

    except Exception as e:
        print(f"[ERROR] Failed to fetch from MLB API for {date_str}: {e}")
        return []



def get_schedule():
    all_games = []
    from datetime import datetime, timedelta
    import os

    for offset in [0, 1]:  # Today and Tomorrow
        target_date = (datetime.utcnow() + timedelta(days=offset)).date()
        cache_file = os.path.join(CACHE_DIR, f"{target_date}.json")
        games = []

        # Try to load from cache
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    games = json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load cache: {e}")

        # Fallback to live fetch if cache is missing or empty
        if not games:
            print(f"[FALLBACK] Fetching schedule for {target_date}")
            games = fetch_schedule_by_date(datetime.combine(target_date, datetime.min.time()), force_refresh=True)

        # Add game metadata
        # Add game metadata
        for game in games:
            try:
                game["Date"] = pd.to_datetime(game.get("time"), utc=True)
            except Exception:
                game["Date"] = pd.NaT

            game["Home"] = game.get("home", "Unknown")
            game["Away"] = game.get("opponent", "Unknown")
            all_games.append(game)


    if not all_games:
        return pd.DataFrame()

    df = pd.DataFrame(all_games)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True)
    return df.dropna(subset=["Date"])
