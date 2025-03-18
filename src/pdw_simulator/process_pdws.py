import pandas as pd
import numpy as np
from virtual_sdr import VirtualSDR
import os

def process_dataset(input_file):
    """
    Process PDW data through virtual SDR
    
    Args:
        input_file: Path to input PDW CSV file
    """
    print(f"Processing file: {input_file}")
    
    # Check if file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"PDW file not found: {input_file}")
    
    # Load PDW data
    print("Loading PDW data...")
    pdw_data = pd.read_csv(input_file)
    print(f"Loaded {len(pdw_data)} PDW records")
    
    # Create VirtualSDR instance
    vsdr = VirtualSDR()
    
    # Process the data
    print("Processing through virtual SDR...")
    processed_data = vsdr.process_pdw_data(pdw_data)
    print(f"Processed {len(processed_data)} PDW records")
    
    # Save processed data
    output_file = input_file.replace('.csv', '_sdr.csv')
    processed_data.to_csv(output_file, index=False)
    print(f"Saved processed data to: {output_file}")
    
    # Print summary of changes
    print("\nData Summary:")
    print("Original vs Processed:")
    for column in pdw_data.columns:
        if column in processed_data.columns:
            print(f"\n{column}:")
            print(f"Original mean: {pdw_data[column].mean():.4f}")
            print(f"Processed mean: {processed_data[column].mean():.4f}")
            print(f"Change %: {((processed_data[column].mean() - pdw_data[column].mean())/pdw_data[column].mean()*100):.2f}%")
    
    return processed_data

if __name__ == "__main__":
    # You can specify your PDW file path here
    input_file = "pdw_data.csv"  # Replace this with your actual file path
    
    try:
        processed_data = process_dataset(input_file)
    except Exception as e:
        print(f"Error processing PDW data: {str(e)}")