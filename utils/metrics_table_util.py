import pandas as pd

def generate_player_metrics_table(player_metrics):
    """
    Generates a table of player metrics for each player ID.
    The table rows contain the metrics, and the columns are the pitch types.
    
    Args:
    - player_metrics (dict): A dictionary containing player metrics (K%, OBA, SLG, etc.).
    - player_names (dict): A dictionary containing player names for each player ID.
    
    Returns:
    - pd.DataFrame: A DataFrame with pitch types as columns and metrics as rows.
    """
    
    # Prepare an empty list to hold rows of data
    all_metrics = []
    
    # Loop through the player_metrics dictionary to gather data
    for player_id, metrics in player_metrics.items():
        # Get the player name from the player_names dictionary
        #player_name = player_names.get(player_id, "Unknown")
        
        # Loop through each pitch type for the player
        for pitch_name, stats in metrics.items():
            # Create a row for the DataFrame
            row = {
                #"Player Name": player_name,  # Add player name to the row
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
            # Append the row to the list
            all_metrics.append(row)
    
    # Convert the list of rows to a DataFrame
    metrics_df = pd.DataFrame(all_metrics)
    
    # Pivot the table so pitch types are columns
    metrics_df = metrics_df.pivot_table(
        index=["Player Name", "Player ID"], 
        columns=["Pitch Name"], 
        values=["K%", "Whiff Rate", "PutAway%", "OBA", "SLG", "Hits", "Total Plate Appearances"], 
        aggfunc="first"
    )
    
    # Clean up the columns for easier reading
    metrics_df.columns = [f"{metric} - {pitch}" for metric, pitch in metrics_df.columns]
    
    return metrics_df
