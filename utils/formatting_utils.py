# utils/formatting_utils.py

import sys
import os

import pandas as pd

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def format_baseball_stats(df: pd.DataFrame) -> pd.DataFrame:
    formatted_df = df.copy()
    float_cols = formatted_df.select_dtypes(include=["float", "float64"]).columns

    for col in float_cols:
        # Format numbers to 3 decimal places, remove trailing zeros, and ensure 0 is displayed as 0.000
        formatted_df[col] = formatted_df[col].map(
            lambda x: f"{x:.3f}" if pd.notnull(x) else x
        )
        # Ensure all 0 values are formatted as '0.000'
        formatted_df[col] = formatted_df[col].replace("0", "0.000")

    return formatted_df
