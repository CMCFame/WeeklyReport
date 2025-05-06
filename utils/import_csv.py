# utils/import_csv.py
"""Script to import project data from CSV file."""

import os
import shutil
import pandas as pd
from pathlib import Path

def import_project_data(source_path):
    """Import project data from a source CSV file.
    
    Args:
        source_path (str): Path to the source CSV file
        
    Returns:
        bool: True if import was successful, False otherwise
    """
    try:
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Validate source file
        if not os.path.exists(source_path):
            print(f"Error: Source file '{source_path}' not found.")
            return False
        
        # Read the source CSV to validate it has the correct columns
        df = pd.read_csv(source_path)
        
        # Check required columns
        required_columns = ["Project", "Milestone: Milestone Name", "Timecard: Owner Name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Source file is missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Copy the file to the data directory
        destination_path = "data/project_data.csv"
        shutil.copy2(source_path, destination_path)
        
        print(f"Successfully imported project data from '{source_path}' to '{destination_path}'")
        print(f"Imported {len(df)} rows with {len(df['Project'].unique())} unique projects")
        return True
        
    except Exception as e:
        print(f"Error importing project data: {str(e)}")
        return False

# If run directly, use a command-line argument for the source path
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python utils/import_csv.py <path/to/csv/file>")
        sys.exit(1)
    
    source_path = sys.argv[1]
    import_project_data(source_path)