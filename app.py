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

        # Create new worksheet for this search
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        location = results['search_criteria']['location']
        worksheet_name = f"{location} - {timestamp}"

        try:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
        except:
            # If worksheet name exists, add a number
            worksheet = spreadsheet.add_worksheet(title=f"{worksheet_name} (2)", rows=100, cols=20)

        # Header row
        headers = [
            'Rank', 'Address', 'City', 'State', 'ZIP',
            'List Price', 'Beds', 'Baths', 'Sqft', 'Price/Sqft',
            'Zestimate (ARV)', 'MAO (70%)', 'Profit Potential', 'ROI %',
            'Deal Score', 'Deal Grade', 'Recommendation',
            'Monthly Rent', 'Cash Flow', 'Cash-on-Cash %', 'Cap Rate %',
            'Price Trend', '1-Year Change %'
        ]

        rows = [headers]

        # Add property data
        for i, prop in enumerate(results.get('all_results', []), 1):
            analysis = prop.get('detailed_analysis', {})

            if not analysis.get('success'):
                continue

            property_data = analysis.get('property', {})
            valuation = analysis.get('valuation', {})
            investor = analysis.get('investor_analysis', {})
            deal = analysis.get('deal_quality', {})
            rental = prop.get('rental_analysis', {})
            price_hist = prop.get('price_history', {})

            row = [
                i,  # Rank
                prop.get('address', ''),
                prop.get('city', ''),
                prop.get('state', ''),
                prop.get('zipcode', ''),
                prop.get('price', 0),
                property_data.get('beds', 0),
                property_data.get('baths', 0),
                property_data.get('sqft', 0),
                prop.get('price_per_sqft', 0),
                valuation.get('zestimate', 0),
                investor.get('mao_70_percent', 0),
                investor.get('profit_potential', 0),
                investor.get('roi_percentage', 0),
                deal.get('score', 0),
                deal.get('label', ''),
                deal.get('recommendation', ''),
                rental.get('income', {}).get('monthly_rent', 0) if rental else 0,
                rental.get('cash_flow', {}).get('monthly_cash_flow', 0) if rental else 0,
                rental.get('roi_metrics', {}).get('cash_on_cash_return', 0) if rental else 0,
                rental.get('roi_metrics', {}).get('cap_rate', 0) if rental else 0,
                price_hist.get('trend', '') if price_hist else '',
                price_hist.get('one_year_change_pct', 0) if price_hist else 0
            ]

            rows.append(row)

        # Write to sheet
        worksheet.update('A1', rows)

        # Format header row
        worksheet.format('A1:W1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
        })

        # Auto-resize columns
        worksheet.columns_auto_resize(0, len(headers))

        return {
            'success': True,
            'url': spreadsheet.url,
            'sheet_id': sheet_id,
            'worksheet': worksheet_name
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
