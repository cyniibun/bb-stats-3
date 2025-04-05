import logging
import pandas as pd

# Load the data from CSV
file_path = './data/pitcher_stats/Aaron_Nola_605400.csv'
data = pd.read_csv(file_path)

# Fill missing events and descriptions
data['events'] = data['events'].fillna('No event')
data['des'] = data['des'].fillna('No decision')

# Function to calculate K%, PutAway%, OBA, SLG, and BA by pitch type
def calculate_metrics_by_pitch_type(data):
    # Group the data by pitch name (pitch type)
    grouped = data.groupby('pitch_name')

    metrics = {}

    # Iterate over each pitch type and calculate metrics
    for pitch_name, group in grouped:
        # Total Plate Appearances (PA) is the total number of rows
        total_pa = len(group)

        # Count Strikeouts (Swinging and Looking)
        strikeouts_swinging = group[group['des'] == 'Swinging Strike'].shape[0]
        strikeouts_looking = group[group['des'] == 'Called Strike'].shape[0]
        total_strikeouts = strikeouts_swinging + strikeouts_looking

        # Calculate K%
        k_percentage = (total_strikeouts / total_pa) * 100 if total_pa > 0 else 0

        # Count Hits, Walks, HBP, and At-bats
        hits = group[group['events'].isin(['Single', 'Double', 'Triple', 'Home Run'])].shape[0]
        walks = group[group['des'].str.contains('Walk', case=False, na=False)].shape[0]
        hbp = group[group['des'].str.contains('Hit by Pitch', case=False, na=False)].shape[0]
        at_bats = total_pa - walks - hbp

        # Calculate OBA
        oba = (hits + walks + hbp) / (at_bats + walks + hbp) if (at_bats + walks + hbp) > 0 else 0

        # Calculate SLG
        total_bases = (
            group[group['events'] == 'Single'].shape[0] +
            2 * group[group['events'] == 'Double'].shape[0] +
            3 * group[group['events'] == 'Triple'].shape[0] +
            4 * group[group['events'] == 'Home Run'].shape[0]
        )
        slg = total_bases / at_bats if at_bats > 0 else 0

        # Calculate PutAway% (Percentage of strikeouts for this pitch type)
        putaway_percentage = (total_strikeouts / total_pa) * 100 if total_pa > 0 else 0

        # Calculate BA (Batting Average)
        ba = hits / at_bats if at_bats > 0 else 0

        # Store the calculated metrics for this pitch type
        metrics[pitch_name] = {
            'K%': k_percentage,
            'PutAway%': putaway_percentage,
            'OBA': oba,
            'SLG': slg,
            'BA': ba,
            'Hits': hits,
            'At-Bats': at_bats,
            'Walks': walks,
            'HBP': hbp,
            'Total Plate Appearances': total_pa
        }

    return metrics

# Calculate metrics by pitch type
metrics = calculate_metrics_by_pitch_type(data)

# Display the results
for pitch, stat in metrics.items():
    print(f"Metrics for {pitch}:")
    for key, value in stat.items():
        print(f"{key}: {value}")
    print("\n")
