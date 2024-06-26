import requests
import pandas as pd
from datetime import datetime, time
from get_data import fetch_data_from_api

# Global variable to store the data
data_store = pd.DataFrame()

# Function to process data
def process_data(data):
    if data is None:
        print("No data received from API")
        return pd.DataFrame()
    
    try:
        # Check if data is a list or a single dictionary
        if isinstance(data, dict):
            data = [data]  # Convert single dictionary to a list
        elif not isinstance(data, list):
            print(f"Unexpected data format. Expected list or dict, got {type(data)}")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if df.empty:
            print("DataFrame is empty after conversion")
            return df

        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d-%b-%Y %H:%M:%S', errors='coerce')
        
        # Ensure all required columns are present
        required_columns = ['timestamp', 'source_pH', 'source_TDS', 'source_FRC', 'source_pressure', 'source_flow']
        for col in required_columns:
            if col not in df.columns:
                print(f"Missing column: {col}")
                df[col] = None
        
        return df.sort_values('timestamp')
    except Exception as e:
        print(f"Error processing data: {e}")
        return pd.DataFrame()

def process_and_store_data(api_url):
    global data_store
    data = fetch_data_from_api(api_url)
    if data:
        new_data = process_data(data)
        data_store = pd.concat([data_store, new_data]).drop_duplicates().sort_values('timestamp')
        print("Data updated successfully")
    else:
        print("No new data to update")
    
def get_todays_data():
    global data_store
    today = datetime.now().date()
    try:
        print("Data store before filtering:", data_store)
        # Ensure the 'timestamp' column is a datetime object
        if not pd.api.types.is_datetime64_any_dtype(data_store['timestamp']):
            data_store['timestamp'] = pd.to_datetime(data_store['timestamp'])
        # Filter for today's data
        today_data = data_store[data_store['timestamp'].dt.date == today]
        print("Today's data:", today_data)
        return today_data
    except Exception as e:
        print("Error occurred in get_todays_data:", e)
        return pd.DataFrame()  # Return an empty DataFrame in case of error