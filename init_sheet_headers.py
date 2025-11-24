"""
Initialize Google Sheet with proper headers
Run this to set up or reset the sheet with correct column headers
"""

import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def init_headers():
    """Initialize Google Sheet with proper headers"""
    try:
        # Connect to Google Sheets
        creds = Credentials.from_service_account_file(
            'google_credentials.json',
            scopes=SCOPES
        )
        client = gspread.authorize(creds)

        # Get the spreadsheet
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        if not sheet_id:
            print("❌ Error: GOOGLE_SHEET_ID not found in .env file")
            return

        spreadsheet = client.open_by_key(sheet_id)

        # Get or create the worksheet
        worksheet_name = "All Properties"
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"✅ Found worksheet: {worksheet_name}")
        except:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=35)
            print(f"✅ Created new worksheet: {worksheet_name}")

        # Clear all existing data
        worksheet.clear()
        print("🧹 Cleared existing data")

        # Define headers - must match exactly with app.py
        headers = [
            'Date Pulled',           # 1
            'Search Location',       # 2
            'Rank',                  # 3
            'Address',               # 4
            'City',                  # 5
            'State',                 # 6
            'ZIP',                   # 7
            'Zillow URL',            # 8
            'List Price',            # 9
            'Beds',                  # 10
            'Baths',                 # 11
            'Sqft',                  # 12
            'Price/Sqft',            # 13
            'Zestimate (ARV)',       # 14
            'MAO Light ($25/sqft)',  # 15
            'MAO Medium ($40/sqft)', # 16
            'MAO Heavy ($60/sqft)',  # 17
            'Profit Light',          # 18
            'Profit Medium',         # 19
            'Profit Heavy',          # 20
            'Best Scenario',         # 21
            'Best Profit',           # 22
            'Is Fixer?',             # 23
            'Keywords Found',        # 24
            'Deal Score',            # 25
            'Deal Grade',            # 26
            'Recommendation',        # 27
            'Monthly Rent',          # 28
            'Cash Flow',             # 29
            'Cash-on-Cash %',        # 30
            'Cap Rate %',            # 31
            'Price Trend',           # 32
            '1-Year Change %'        # 33
        ]

        # Write headers to first row
        worksheet.update('A1', [headers])
        print(f"✅ Added {len(headers)} column headers")

        # Format header row
        worksheet.format('A1:AG1', {
            'textFormat': {'bold': True, 'fontSize': 11},
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'horizontalAlignment': 'CENTER',
            'verticalAlignment': 'MIDDLE'
        })
        print("🎨 Formatted header row")

        # Freeze header row
        worksheet.freeze(rows=1)
        print("❄️  Froze header row")

        # Auto-resize columns
        worksheet.columns_auto_resize(0, len(headers))
        print("📏 Auto-resized columns")

        print(f"\n✨ Sheet initialized successfully!")
        print(f"🔗 URL: {spreadsheet.url}")
        print(f"\n📋 Column structure (33 columns):")
        print("   Columns 1-7:   Basic Info (Date, Location, Address)")
        print("   Column 8:      Zillow URL (clickable link)")
        print("   Columns 9-14:  Property Details (Price, Beds, Baths, Sqft, Zestimate)")
        print("   Columns 15-22: All Rehab Scenarios (Light/Medium/Heavy MAO & Profits)")
        print("   Columns 23-24: Fixer Keywords Detection")
        print("   Columns 25-27: Deal Quality (Score, Grade, Recommendation)")
        print("   Columns 28-31: Rental Analysis")
        print("   Columns 32-33: Price Trends")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Initializing Google Sheet Headers\n")
    init_headers()
