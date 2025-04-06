import statsapi
from datetime import datetime

def fetch_schedule_for_today():
    """Fetches the MLB schedule for today."""
    try:
        today_date = datetime.today().strftime('%Y-%m-%d')
        schedule = statsapi.schedule(date=today_date)
        if not schedule:
            print(f"[ERROR] No games found for today ({today_date}).")
            return None
        print(f"[DEBUG] Schedule fetched successfully for {today_date}")
        return schedule
    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule for {today_date}: {e}")
        return None

if __name__ == "__main__":
    # Fetch the schedule for today
    schedule = fetch_schedule_for_today()

    # Print the raw unformatted data (the entire response)
    if schedule:
        print("[DEBUG] Raw Schedule Data:")
        print(schedule)  # Print the raw data from the API response
    else:
        print("[ERROR] No schedule data found.")
