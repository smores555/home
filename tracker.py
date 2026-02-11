import os, requests, gspread, json, datetime
from oauth2client.service_account import ServiceAccountCredentials

def scrape_and_save():
    targets = [
        {"zip": "95661", "tab": "Roseville_95661"},
        {"zip": "90045", "tab": "Westchester_90045"}
    ]
    api_key = os.getenv("RENTCAST_API_KEY")
    today = datetime.date.today().strftime("%Y-%m-%d")

    # Connect to Google Sheets
    creds_dict = json.loads(os.getenv("GOOGLE_SHEETS_JSON"))
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Home_Price_Tracker")

    for item in targets:
        # Get Price
        url = f"https://api.rentcast.io/v1/market/stats?zipCode={item['zip']}"
        data = requests.get(url, headers={"X-Api-Key": api_key}).json()
        avg_price = data.get('listings', {}).get('averageSalePrice', 0)
        
        # Append to the specific tab
        worksheet = spreadsheet.worksheet(item['tab'])
        worksheet.append_row([today, avg_price])

if __name__ == "__main__":
    scrape_and_save()
