from datetime import datetime
from utils.mlb_api import get_game_state
from utils.schedule_utils import get_schedule
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import pytz
import pandas as pd
import textwrap

def render_scoreboard(game_pk, home_team="Home", away_team="Away", autorefresh=True):
    if autorefresh:
        st_autorefresh(interval=15 * 1000, key=f"autorefresh-{game_pk}")

    state = get_game_state(game_pk)
    if not state:
        st.info("Awaiting MLB live data feed.")
        return

    # --- Extract State Info ---
    status = ""
    is_final = False
    is_walkoff = False
    inning = state.get("inning", 0)
    half = state.get("half", "").lower()
    count = state.get("count", "0-0")
    outs = state.get("outs", 0)
    linescore = state.get("linescore", {})
    away = linescore.get("away", {})
    home = linescore.get("home", {})
    away_score = away.get("runs", 0)
    home_score = home.get("runs", 0)

    if "status" in state:
        status = state["status"].get("detailedState", "").lower()

    # --- Final Game Detection ---
    if status in ["final", "completed", "game over", "postgame", "completed early"]:
        is_final = True
    elif half == "bottom" and outs == 3 and inning >= 9:
        is_final = True
    elif half == "top" and outs == 3 and inning >= 9 and home_score > away_score:
        is_final = True
    elif half == "bottom" and outs == 3 and inning >= 9 and home_score > away_score:
        is_final = True
        is_walkoff = True
    elif half == "bottom" and inning >= 9 and home_score > away_score:
        is_final = True
        is_walkoff = True

    # --- Final Game Render ---
    if is_final:
        final_label = f"F/{inning}" if inning > 9 else "Final"
        if home_score > away_score:
            winner = "home"
            home_icon, away_icon = "🏆", "❌"
        elif away_score > home_score:
            winner = "away"
            home_icon, away_icon = "❌", "🏆"
        else:
            winner = "tie"
            home_icon = away_icon = "⚔️"
        if is_walkoff:
            home_icon += " 🚩"

        style = {
            "win": "color: #0af; font-weight: bold;",
            "loss": "color: #999;",
            "tie": "color: #ccc; font-style: italic;"
        }

        home_style = style["tie"] if winner == "tie" else style["win"] if winner == "home" else style["loss"]
        away_style = style["tie"] if winner == "tie" else style["win"] if winner == "away" else style["loss"]

        st.markdown(textwrap.dedent(f"""
            <div style="border: 1px solid #444; border-radius: 8px; padding: 16px; margin: 0.5rem 0 1.5rem 0;">
                <h4 style="margin-bottom: 0.5rem; text-align: center;">{final_label}</h4>
                <p style="{away_style}">{away_icon} <strong>{away_team}</strong>: {away_score} R</p>
                <p style="{home_style}">{home_icon} <strong>{home_team}</strong>: {home_score} R</p>
            </div>
        """), unsafe_allow_html=True)
        return

    # --- Scheduled Time Display ---
    game_time_display = "Scheduled"
    schedule_df = get_schedule()
    game_row = schedule_df[schedule_df["gamePk"] == game_pk]
    if not game_row.empty:
        try:
            est = pytz.timezone("US/Eastern")
            scheduled_time = pd.to_datetime(game_row.iloc[0]["Date"]).tz_convert(est)
            game_time_display = f"Scheduled: {scheduled_time.strftime('%I:%M %p EST')}"
        except Exception:
            pass

    # --- Determine Game State ---
    has_real_activity = any([
        outs > 0,
        count != "0-0",
        away.get("hits", 0) > 0,
        home.get("hits", 0) > 0,
        away_score > 0,
        home_score > 0,
    ])
    is_scheduled = status in ["scheduled", "pre-game", "pre game"]

    if is_scheduled or (inning <= 1 and not has_real_activity):
        display_title = game_time_display
    elif half in ["top", "bottom"]:
        display_title = f"{half.title()} {inning}"
    else:
        display_title = game_time_display

    # --- Optional Count Section ---
    balls, strikes = map(int, count.split("-"))
    if not is_scheduled and (inning > 1 or has_real_activity):
        count_html = f"""
        <strong>Count:</strong><br>
        <div style="display: flex; flex-direction: column; align-items: flex-start; line-height: 1.4;">
            <div><strong>Balls:</strong> {'🟢' * balls + '⚪️' * (3 - balls)}</div>
            <div><strong>Strikes:</strong> {'🔴' * strikes + '⚪️' * (2 - strikes)}</div>
        </div>
        <p style="margin: 0.25rem 0;"><strong>Outs:</strong> {'⚫️' * outs + '⚪️' * (3 - outs)}</p>
    """
    else:
        count_html = ""

    # --- Final Scoreboard HTML ---
    # --- Final Scoreboard Display ---
    st.markdown(f'<div style="border:1px solid #444;border-radius:8px;padding:16px;margin:0.5rem 0 1.5rem 0;"><h4 style="margin-bottom:0.5rem;text-align:center;">{display_title}</h4><div style="display:flex;justify-content:center;"><div style="display:flex;flex-direction:row;align-items:center;gap:36px;flex-wrap:wrap;max-width:800px;"><div style="min-width:240px;">{count_html}<p style="margin:0.25rem 0;"><strong>{away_team}</strong>: {away_score} R / {away.get("hits", 0)} H / {away.get("xba", ".000")}</p><p style="margin:0.25rem 0;"><strong>{home_team}</strong>: {home_score} R / {home.get("hits", 0)} H / {home.get("xba", ".000")}</p></div></div></div></div>', unsafe_allow_html=True)


