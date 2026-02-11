import os, requests, gspread, json, datetime
from oauth2client.service_account import ServiceAccountCredentials

def get_filtered_average(zip_code, min_price, api_key):
    # This specifically looks at active listings to filter by price
    url = f"https://api.rentcast.io/v1/listings/sale?zipCode={zip_code}&minPrice={min_price}&status=Active"
    response = requests.get(url, headers={"X-Api-Key": api_key}).json()
    
    prices = [listing.get('price', 0) for listing in response if listing.get('price')]
    if not prices:
        return 0
    return sum(prices) / len(prices)

def scrape_to_sheets():
    api_key = os.getenv("RENTCAST_API_KEY")
    today = datetime.date.today().strftime("%Y-%m-%d")

    # Auth for Google Sheets
    creds_dict = json.loads(os.getenv("GOOGLE_SHEETS_JSON"))
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Home_Price_Tracker")

    # 1. Standard Roseville Pull
    ros_url = "https://api.rentcast.io/v1/market/stats?zipCode=95661"
    ros_data = requests.get(ros_url, headers={"X-Api-Key": api_key}).json()
    ros_price = ros_data.get('listings', {}).get('averageSalePrice', 0)
    spreadsheet.worksheet("Roseville_95661").append_row([today, ros_price])

    # 2. Filtered Westchester Pull (Only $2M+)
    west_price = get_filtered_average("90045", 2000000, api_key)
    spreadsheet.worksheet("Westchester_90045").append_row([today, west_price])

if __name__ == "__main__":
    scrape_to_sheets()
