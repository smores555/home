import os, requests, gspread, json, datetime
from oauth2client.service_account import ServiceAccountCredentials

def get_filtered_average(zip_code, min_price, api_key):
    url = f"https://api.rentcast.io/v1/listings/sale?zipCode={zip_code}&minPrice={min_price}&status=Active"
    headers = {"X-Api-Key": api_key, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    
    data = response.json()
    
    # If the response is not a list, RentCast sent an error message (str)
    if not isinstance(data, list):
        print(f"Error from RentCast for {zip_code}: {data}")
        return 0
        
    prices = [listing.get('price', 0) for listing in data if listing.get('price')]
    if not prices:
        return 0
    return sum(prices) / len(prices)

def scrape_to_sheets():
    api_key = os.getenv("RENTCAST_API_KEY")
    # Verify API Key exists
    if not api_key:
        print("Error: RENTCAST_API_KEY environment variable not set")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Auth for Google Sheets
    try:
        creds_json = os.getenv("GOOGLE_SHEETS_JSON")
        creds_dict = json.loads(creds_json)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Home_Price_Tracker")
    except Exception as e:
        print(f"Google Sheets Auth Error: {e}")
        return

    # 1. Standard Roseville Pull
    ros_url = "https://api.rentcast.io/v1/market/stats?zipCode=95661"
    ros_resp = requests.get(ros_url, headers={"X-Api-Key": api_key, "Accept": "application/json"}).json()
    
    # Safely get the average price
    ros_price = 0
    if isinstance(ros_resp, dict):
        ros_price = ros_resp.get('listings', {}).get('averageSalePrice', 0)
    
    spreadsheet.worksheet("Roseville_95661").append_row([today, ros_price])

    # 2. Filtered Westchester Pull (Only $2M+)
    west_price = get_filtered_average("90045", 2000000, api_key)
    if west_price > 0:
        spreadsheet.worksheet("Westchester_90045").append_row([today, west_price])
    else:
        print("Westchester price returned 0, skipping row append.")

if __name__ == "__main__":
    scrape_to_sheets()
