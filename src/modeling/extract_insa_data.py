"""
Extract Insa Actual Visit Data from KPI Report

Purpose: Parse Insa retail KPI CSV and extract monthly transaction counts
Converts transactions to visits (transactions ≈ visits for our purposes)
Matches to cities in our training dataset

Author: Claude Code
Date: October 24, 2025
"""

import pandas as pd
import numpy as np
import re


def extract_insa_transactions(kpi_file_path, target_month='April', target_year='2025'):
    """
    Extract Insa FL store transaction counts from KPI CSV.

    Parameters:
    -----------
    kpi_file_path : str
        Path to Insa KPI CSV file
    target_month : str
        Month to extract (Jan, Feb, Mar, Apr, etc.)
    target_year : str
        Year to extract (2024 or 2025)

    Returns:
    --------
    dict : Mapping of city names to monthly transactions
    """

    # Read raw CSV
    df_raw = pd.read_csv(kpi_file_path, header=None, low_memory=False)

    # Find column index for target month
    # Row 2 contains month names (Jan, Feb, Mar, Apr, May...)
    month_row = df_raw.loc[2]

    # Column structure for 2025 data:
    # Col 0: Location names
    # Col 1: Metric names (Revenue, Units, Transactions, etc.)
    # Col 2: Jan 2025
    # Col 3: Feb 2025
    # Col 4: Mar 2025
    # Col 5: Apr 2025
    # ...

    month_to_col_2025 = {
        'Jan': 2, 'Feb': 3, 'Mar': 4, 'Apr': 5,
        'May': 6, 'Jun': 7, 'Jul': 8, 'Aug': 9,
        'Sep': 10, 'Oct': 11, 'Nov': 12, 'Dec': 13
    }

    target_col = month_to_col_2025.get(target_month[:3])

    if target_col is None:
        raise ValueError(f"Invalid month: {target_month}")

    print(f"Extracting {target_month} {target_year} data from column {target_col}")
    print()

    # Find all Insa FL store rows
    insa_data = {}

    for idx, row in df_raw.iterrows():
        if pd.notna(row[0]) and 'Insa FL' in str(row[0]):
            store_name = row[0]

            # Transactions row is 3 rows below store name
            trans_row_idx = idx + 3

            if trans_row_idx < len(df_raw):
                trans_row = df_raw.loc[trans_row_idx]

                # Get transaction count for target month
                transactions = trans_row[target_col]

                # Clean transactions (remove commas, convert to float)
                if pd.notna(transactions):
                    trans_clean = str(transactions).replace(',', '').strip()
                    try:
                        trans_value = float(trans_clean)
                    except:
                        trans_value = None
                else:
                    trans_value = None

                # Extract city from store name
                # Format: "Insa FL [City] [Street] - [MED/REC]"
                city = extract_city_from_store_name(store_name)

                if city and trans_value is not None:
                    # For monthly visits, transactions ≈ visits
                    # Each transaction represents one customer visit

                    # Handle duplicate cities (e.g., Orlando has 2 stores)
                    if city in insa_data:
                        # Append number to distinguish
                        city_key = f"{city}_2"
                    else:
                        city_key = city

                    insa_data[city_key] = trans_value

    return insa_data


def extract_city_from_store_name(store_name):
    """
    Extract city name from Insa store name.

    Examples:
    - "Insa FL Tampa South Dale Mabry - MED" -> "Tampa"
    - "Insa FL Hudson US Hwy 19 - MED" -> "Hudson"
    - "Insa FL Orlando E Colonial Dr - MED" -> "Orlando"
    """
    # Remove prefix and suffix
    name = store_name.replace('Insa FL ', '').replace(' - MED', '').replace(' - REC', '')

    # City is typically the first word(s) before street name
    # Common patterns: "[City] [Street info]"
    parts = name.split()

    # Known cities (multi-word cities need special handling)
    multi_word_cities = ['Lake Placid', 'The Villages']

    for multi_city in multi_word_cities:
        if name.startswith(multi_city):
            return multi_city

    # For single-word cities, return first word
    if len(parts) > 0:
        return parts[0]

    return None


def main():
    """Extract and display Insa transaction data."""

    print("="*70)
    print("INSA ACTUAL TRANSACTION DATA EXTRACTION")
    print("="*70)
    print()

    kpi_file = '/Users/daniel_insa/Claude/multi-state-dispensary-model/Insa_April 2025 Retail KPIs.csv'

    # Extract April 2025 data (to match our Placer data collection period)
    insa_transactions = extract_insa_transactions(kpi_file, 'April', '2025')

    print("Insa FL Stores - April 2025 Actual Transactions:")
    print("-" * 70)

    for city in sorted(insa_transactions.keys()):
        transactions = insa_transactions[city]
        print(f"{city:20} | {transactions:>10,.0f} transactions/month")

    print()
    print(f"Total stores: {len(insa_transactions)}")
    print()

    # Note about transactions vs visits
    print("NOTE: For Placer comparison:")
    print("  - Insa 'Transactions' = actual customer visits")
    print("  - Placer 'Visits' = estimated customer visits")
    print("  - These are directly comparable for correction factor calculation")
    print()

    return insa_transactions


if __name__ == "__main__":
    insa_data = main()
