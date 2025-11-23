"""
FYNIX Deal Finder - Web Application
Flask web app with Google Sheets integration
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

from deal_finder import DealFinder

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


def get_google_sheets_client():
    """Initialize Google Sheets client"""
    try:
        creds = Credentials.from_service_account_file(
            'google_credentials.json',
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None


def save_to_google_sheets(results, spreadsheet_id=None):
    """
    Save search results to Google Sheets

    Args:
        results: Analysis results from DealFinder
        spreadsheet_id: Optional Google Sheets ID (uses env var if not provided)

    Returns:
        URL to the Google Sheet or error message
    """
    try:
        client = get_google_sheets_client()
        if not client:
            return {"error": "Could not connect to Google Sheets"}

        # Get or create spreadsheet
        sheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEET_ID')

        if sheet_id:
            spreadsheet = client.open_by_key(sheet_id)
        else:
            spreadsheet = client.create('FYNIX Deal Finder Results')
            sheet_id = spreadsheet.id

        # Use or create a single worksheet for all properties
        worksheet_name = "All Properties"

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            # Create new worksheet if doesn't exist
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=25)

        # Check if sheet has headers (check if A1 is empty)
        existing_data = worksheet.get_all_values()
        has_headers = len(existing_data) > 0 and existing_data[0]

        # Build index of existing properties with their last pulled date
        # Key: "address, city, state zip" -> Last date pulled
        existing_properties = {}
        if has_headers and len(existing_data) > 1:
            # Skip header row, index starting from 1
            for row in existing_data[1:]:
                if len(row) >= 7:  # Has enough columns
                    date_str = row[0]  # Date Pulled
                    address = row[3]   # Address
                    city = row[4]      # City
                    state = row[5]     # State
                    zipcode = row[6]   # ZIP

                    if address:  # Only track if we have an address
                        # Create unique key
                        prop_key = f"{address}, {city}, {state} {zipcode}".lower().strip()

                        # Parse date and track most recent
                        try:
                            pulled_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                            if prop_key not in existing_properties or pulled_date > existing_properties[prop_key]:
                                existing_properties[prop_key] = pulled_date
                        except:
                            pass  # Skip if date parsing fails

        # Header row with Date Pulled as first column + All Rehab Scenarios
        headers = [
            'Date Pulled', 'Search Location', 'Rank', 'Address', 'City', 'State', 'ZIP',
            'List Price', 'Beds', 'Baths', 'Sqft', 'Price/Sqft',
            'Zestimate (ARV)',
            'MAO Light ($25/sqft)', 'MAO Medium ($40/sqft)', 'MAO Heavy ($60/sqft)',
            'Profit Light', 'Profit Medium', 'Profit Heavy',
            'Best Scenario', 'Best Profit',
            'Is Fixer?', 'Keywords Found',
            'Deal Score', 'Deal Grade', 'Recommendation',
            'Monthly Rent', 'Cash Flow', 'Cash-on-Cash %', 'Cap Rate %',
            'Price Trend', '1-Year Change %'
        ]

        # Prepare rows to append
        rows = []

        # Add headers only if sheet is empty
        if not has_headers:
            rows.append(headers)

        # Add property data with timestamp and duplicate checking
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_time = datetime.now()
        search_location = results['search_criteria']['location']

        skipped_count = 0

        for i, prop in enumerate(results.get('all_results', []), 1):
            analysis = prop.get('detailed_analysis', {})

            if not analysis.get('success'):
                continue

            # Check for duplicate
            address = prop.get('address', '')
            city = prop.get('city', '')
            state = prop.get('state', '')
            zipcode = prop.get('zipcode', '')
            prop_key = f"{address}, {city}, {state} {zipcode}".lower().strip()

            # Check if property exists and if it was pulled recently
            if prop_key in existing_properties:
                last_pulled = existing_properties[prop_key]
                days_since_pull = (current_time - last_pulled).days

                # Skip if pulled within last 30 days
                if days_since_pull < 30:
                    skipped_count += 1
                    print(f"⏭️  Skipping {address} - Last pulled {days_since_pull} days ago")
                    continue

            property_data = analysis.get('property', {})
            valuation = analysis.get('valuation', {})
            investor = analysis.get('investor_analysis', {})
            deal = analysis.get('deal_quality', {})
            rental = prop.get('rental_analysis', {})
            price_hist = prop.get('price_history', {})
            keywords_data = analysis.get('keywords', {})

            row = [
                timestamp,  # Date Pulled
                search_location,  # Search Location
                i,  # Rank
                address,
                city,
                state,
                zipcode,
                prop.get('price', 0),
                property_data.get('beds', 0),
                property_data.get('baths', 0),
                property_data.get('sqft', 0),
                prop.get('price_per_sqft', 0),
                valuation.get('zestimate', 0),
                # All three MAO scenarios
                investor.get('mao_light_rehab', 0),
                investor.get('mao_medium_rehab', 0),
                investor.get('mao_heavy_rehab', 0),
                # Profit for each scenario
                investor.get('profit_light', 0),
                investor.get('profit_medium', 0),
                investor.get('profit_heavy', 0),
                # Best scenario
                investor.get('best_scenario', ''),
                investor.get('best_profit', 0),
                # Keywords
                'YES' if keywords_data.get('is_fixer', False) else 'NO',
                ', '.join(keywords_data.get('keywords_found', [])) if keywords_data.get('keywords_found') else '',
                # Deal quality
                deal.get('score', 0),
                deal.get('label', ''),
                deal.get('recommendation', ''),
                # Rental analysis
                rental.get('income', {}).get('monthly_rent', 0) if rental else 0,
                rental.get('cash_flow', {}).get('monthly_cash_flow', 0) if rental else 0,
                rental.get('roi_metrics', {}).get('cash_on_cash_return', 0) if rental else 0,
                rental.get('roi_metrics', {}).get('cap_rate', 0) if rental else 0,
                # Price trends
                price_hist.get('trend', '') if price_hist else '',
                price_hist.get('one_year_change_pct', 0) if price_hist else 0
            ]

            rows.append(row)
            print(f"✅ Adding {address} to sheet")

        # Append rows to sheet
        if rows:
            if has_headers:
                # Append data rows only (skip headers)
                worksheet.append_rows(rows, value_input_option='USER_ENTERED')
            else:
                # Write headers + data rows
                worksheet.update('A1', rows)
                # Format header row (now with more columns for all scenarios)
                worksheet.format('A1:AD1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
                })
                # Auto-resize columns
                worksheet.columns_auto_resize(0, len(headers))

        rows_added = len(rows) - (0 if has_headers else 1)  # Subtract header row if added

        return {
            'success': True,
            'url': spreadsheet.url,
            'sheet_id': sheet_id,
            'worksheet': worksheet_name,
            'rows_added': rows_added,
            'rows_skipped': skipped_count,
            'timestamp': timestamp,
            'message': f"Added {rows_added} properties, skipped {skipped_count} duplicates (pulled within 30 days)"
        }

    except Exception as e:
        return {'error': str(e)}


@app.route('/')
def home():
    """Render the main form page"""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_properties():
    """Handle property search form submission"""
    try:
        # Get form data
        location = request.form.get('location')
        min_price = request.form.get('min_price', type=int)
        max_price = request.form.get('max_price', type=int)
        beds_min = request.form.get('beds_min', type=int)
        baths_min = request.form.get('baths_min', type=int)
        screen_count = request.form.get('screen_count', 20, type=int)
        analyze_count = request.form.get('analyze_count', 5, type=int)
        min_score = request.form.get('min_score', 6, type=int)
        save_to_sheets = request.form.get('save_to_sheets') == 'on'

        if not location:
            return jsonify({'error': 'Location is required'}), 400

        # Run deal finder
        finder = DealFinder()

        results = finder.find_deals(
            location=location,
            min_price=min_price,
            max_price=max_price,
            beds_min=beds_min,
            baths_min=baths_min,
            initial_screen=screen_count,
            deep_analyze=analyze_count,
            min_deal_score=min_score,
            check_price_history=True,
            check_rental=True
        )

        # Save to Google Sheets if requested
        sheet_info = None
        if save_to_sheets:
            sheet_info = save_to_google_sheets(results)

        # Prepare response
        response = {
            'success': True,
            'results': results,
            'sheet_info': sheet_info
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for programmatic access"""
    try:
        data = request.get_json()

        if not data or 'location' not in data:
            return jsonify({'error': 'Location is required'}), 400

        finder = DealFinder()

        results = finder.find_deals(
            location=data['location'],
            min_price=data.get('min_price'),
            max_price=data.get('max_price'),
            beds_min=data.get('beds_min'),
            baths_min=data.get('baths_min'),
            initial_screen=data.get('screen_count', 20),
            deep_analyze=data.get('analyze_count', 5),
            min_deal_score=data.get('min_score', 6)
        )

        # Auto-save to Google Sheets if configured
        if data.get('save_to_sheets', False):
            sheet_info = save_to_google_sheets(results, data.get('spreadsheet_id'))
            results['sheet_info'] = sheet_info

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'zillow_api_configured': bool(os.getenv('ZILLOW_API_KEY')),
        'google_sheets_configured': os.path.exists('google_credentials.json')
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
