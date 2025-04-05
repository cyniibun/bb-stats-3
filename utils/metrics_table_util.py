#metrics_table_util
import pandas as pd
from utils.calculate_util import calculate_metrics

def generate_player_metrics_table(player_ids):
    """
    Generates a table of player metrics for each player ID.
    The table rows contain the metrics, and the columns are the pitch types.
    
    Args:
    - player_ids (list): List of player IDs to fetch metrics for.
    
    Returns:
    - pd.DataFrame: A DataFrame with pitch types as columns and metrics as rows.
    """
    
    all_metrics = []
    pitch_types = set()  # Set to collect all unique pitch types
    
    # Fetch metrics for each player
    for player_id in player_ids:
        player_metrics = calculate_metrics(player_id)
        
        if player_metrics:
            # Loop through the metrics and collect pitch data
            for pitch_name, stats in player_metrics.items():
                # Add this pitch type to the pitch_types set
                pitch_types.add(pitch_name)
                
                # Prepare row data for this pitch
                row = {
                    "Player ID": player_id,
                    "Pitch Name": pitch_name,
                    "K%": stats.get("K%", "-"),
                    "Whiff Rate": stats.get("Whiff Rate", "-"),
                    "PutAway%": stats.get("PutAway%", "-"),
                    "OBA": stats.get("OBA", "-"),
                    "SLG": stats.get("SLG", "-"),
                    "Hits": stats.get("Hits", "-"),
                    "Total Plate Appearances": stats.get("Total Plate Appearances", "-")
                }
                all_metrics.append(row)
    
    # Convert to DataFrame
    metrics_df = pd.DataFrame(all_metrics)
    
    # Pivot the table so pitch types are columns
    metrics_df = metrics_df.pivot_table(index=["Player ID"], columns=["Pitch Name"], values=["K%", "Whiff Rate", "PutAway%", "OBA", "SLG", "Hits", "Total Plate Appearances"], aggfunc="first")
    
    # Clean up the columns for easy reading
    metrics_df.columns = [f"{metric} - {pitch}" for metric, pitch in metrics_df.columns]
    
    return metrics_df
