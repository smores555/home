import os
import requests
import gspread
import json
import datetime
from oauth2client.service_account import ServiceAccountCredentials

def get_filtered_average(zip_code, min_price, api_key):
    """Fetches active listings from RentCast and calculates the average price above a floor."""
    url = f"https://api.rentcast.io/v1/listings/sale?zipCode={zip_code}&minPrice={min_price}&status=Active"
    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Check if the response is a list (valid data) or a dict (error message)
        if not isinstance(data, list):
            print(f"RentCast API Error for {zip_code}: {data}")
            return 0
            
        prices = [listing.get('price', 0) for listing in data if listing.get('price')]
        
        if not prices:
            print(f"No listings found for {zip_code} above ${min_price:,}")
            return 0
            
        return sum(prices) / len(prices)
        
    except Exception as e:
        print(f"Request failed for {zip_code}: {e}")
        return 0

def scrape_to_sheets():
    # 1. Setup Environment Variables
    api_key = os.getenv("RENTCAST_API_KEY")
    creds_json = os.getenv("GOOGLE_SHEETS_JSON")
    
    if not api_key or not creds_json:
        print("Missing API Key or Google Sheets JSON secret.")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # 2. Authenticate with Google Sheets
    try:
        creds_dict = json.loads(creds_json)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Home_Price_Tracker")
    except Exception as e:
        print(f"Google Sheets Auth Error: {e}")
        return

    # 3. Pull Roseville Data (Filter: >$500,000)
    print("Fetching Roseville listings above $500,000...")
    ros_price = get_filtered_average("95661", 500000, api_key)
    
    if ros_price > 0:
        spreadsheet.worksheet("Roseville_95661").append_row([today, round(ros_price, 2)])
        print(f"Roseville Updated: ${ros_price:,.2f}")
    else:
        print("Roseville update skipped (price was 0).")

    # 4. Pull Westchester Data (Filter: >$2,000,000)
    print("Fetching Westchester listings above $2,000,000...")
    west_price = get_filtered_average("90045", 2000000, api_key)
    
    if west_price > 0:
        spreadsheet.worksheet("Westchester_90045").append_row([today, round(west_price, 2)])
        print(f"Westchester Updated: ${west_price:,.2f}")
    else:
        print("Westchester update skipped (price was 0).")

if __name__ == "__main__":
    scrape_to_sheets()
