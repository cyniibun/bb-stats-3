#calculate_util.py

import logging
import pybaseball
import pandas as pd
from datetime import datetime
import numpy as np

# Set up logging for debugging
log_filename = './data/statcast_metrics.log'  # Log file path
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # For console output
        logging.FileHandler(log_filename, mode='w')  # For file output
    ]
)

def calculate_metrics(player_id, start_date='2024-01-01', end_date=None, player_type='batter'):
    """
    Calculate K%, OBA, SLG, and other metrics for a given player using their player ID,
    grouped by pitch_name (pitch type).
    """
    # If no end_date is provided, use today's date
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')

    try:
        # Fetch Statcast data for the given player ID and date range
        if player_type == 'batter':
            stats = pybaseball.statcast_batter(start_date, end_date, player_id)
        elif player_type == 'pitcher':
            stats = pybaseball.statcast_pitcher(start_date, end_date, player_id)
        else:
            logging.error("Invalid player_type. Should be 'batter' or 'pitcher'.")
            return {}

        # Check if the dataframe is empty
        if stats.empty:
            logging.warning(f"No Statcast data found for player {player_id} ({player_type}) in the specified date range.")
            return {}

        # Handle missing or empty data
        stats['events'] = stats['events'].fillna('No event')
        stats['description'] = stats['description'].fillna('No decision')

        # Group data by pitch_name (pitch type)
        grouped = stats.groupby('pitch_name')

        # Initialize counters for the metrics
        metrics = {}

        # Process each group (pitch_name) and calculate the metrics
        for pitch_name, group in grouped:

            # Initialize counters for each metric
            strikeouts_swinging = 0
            strikeouts_looking = 0
            total_strikes = 0
            total_swings = 0  # Count for swinging strikes
            field_outs = 0  # Count for field outs
            foul_balls = 0  # Count for foul balls
            total_ks = 0
            total_pa = len(group)  # Total plate appearances (all rows for this pitch type)

            # Count Hits: Check the "events" column for valid hit events
            hits = group[group['events'].isin(['single', 'double', 'triple', 'home_run'])].shape[0]
            #logging.debug(f"Hits for {pitch_name}: {hits}")

            # Count Walks: Check the "description" column for walks
            walks = group[group['description'].str.contains('walk', case=False, na=False)].shape[0]
            #logging.debug(f"Walks for {pitch_name}: {walks}")

            # Count Hit by Pitches (HBP)
            hbp = group[group['description'].str.contains('hit_by_pitch', case=False, na=False)].shape[0]
            #logging.debug(f"HBP for {pitch_name}: {hbp}")

            at_bats = total_pa - walks - hbp  # At-bats exclude walks and hit-by-pitches
            #logging.debug(f"At-Bats for {pitch_name}: {at_bats}")

            # Count all strikes (both swinging and looking)
            total_strikes = group[group['description'].str.contains('strike', case=False, na=False)].shape[0]

            # Loop through the data and classify the different strike events
            for index, row in group.iterrows():
                if row['events'] == 'strikeout':  # Strikeout event
                    if row['description'] == 'swinging_strike':  # Swinging strike
                        strikeouts_swinging += 1
                        total_swings += 1  # Increment for swinging strike
                    elif row['description'] == 'called_strike':  # Looking strike
                        strikeouts_looking += 1
                    total_ks += 1  # Increment total strikeouts

                elif 'foul' in row['description'].lower():  # Foul ball event (counts as a strike)
                    foul_balls += 1
                    total_strikes += 1  # Increment total strikes for foul balls

                elif row['events'] == 'field_out':  # Field out event (counts as a swing)
                    field_outs += 1
                    total_strikes += 1  # Increment total strikes for field outs

            # Calculate Whiff Rate (Swinging Strikes / Total Swings)
            total_swinging = strikeouts_swinging + foul_balls + field_outs  # Total swings = swinging strikes + foul balls + field outs
            whiff_rate = (((total_swings + hits) / total_swinging) * 100) if total_swinging > 0 else 0
            #logging.debug(f"Whiff Rate for {pitch_name}: {whiff_rate}%")

            # Calculate K%
            k_percentage = (strikeouts_swinging + strikeouts_looking) / total_pa * 100 if total_pa > 0 else 0
            #logging.debug(f"K% for {pitch_name}: {k_percentage}")

            # Calculate PutAway% (Percentage of strikeouts for this pitch type)
            putaway_percentage = total_ks / total_strikes * 100 if total_strikes > 0 else 0
            #logging.debug(f"PutAway% for {pitch_name}: {putaway_percentage}")

            # Calculate OBA (On-Base Average)
            oba = (hits + walks + hbp) / (at_bats + walks + hbp) if (at_bats + walks + hbp) > 0 else 0
            #logging.debug(f"OBA for {pitch_name}: {oba}")

            # Calculate SLG (Slugging Average)
            total_bases = (
                group[group['events'] == 'single'].shape[0] +
                2 * group[group['events'] == 'double'].shape[0] +
                3 * group[group['events'] == 'triple'].shape[0] +
                4 * group[group['events'] == 'home_run'].shape[0]
            )
            slg = total_bases / at_bats if at_bats > 0 else 0
            #logging.debug(f"SLG for {pitch_name}: {slg}")

            # Store the calculated metrics for this pitch type
            metrics[pitch_name] = {
                'player_id': str(player_id),  # Convert player_id to string explicitly
                'K%': float(k_percentage) if isinstance(k_percentage, np.generic) else float(k_percentage),
                'Whiff Rate': float(whiff_rate) if isinstance(whiff_rate, np.generic) else float(whiff_rate),
                'PutAway%': float(putaway_percentage) if isinstance(putaway_percentage, np.generic) else float(putaway_percentage),
                'OBA': float(oba) if isinstance(oba, np.generic) else float(oba),
                'SLG': float(slg) if isinstance(slg, np.generic) else float(slg),
                'Hits': int(hits) if isinstance(hits, np.generic) else int(hits),
                'Total Plate Appearances': int(total_pa) if isinstance(total_pa, np.generic) else int(total_pa),
            }




        # Log metrics to the file
        #logging.info(f"Metrics for player {player_id}: {metrics}")
        
        return metrics

    except Exception as e:
        logging.error(f"Error fetching Statcast data for player ID {player_id}: {e}")
        return None


