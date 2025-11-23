"""
FYNIX Property Price History - Track property value changes over time
Analyze price trends to identify distressed properties and appreciation patterns
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import http.client
import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PropertyHistoryAnalyzer:
    """Analyze property price history and trends"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ZILLOW_API_KEY')
        self.api_host = "zillow-working-api.p.rapidapi.com"

        if not self.api_key:
            raise ValueError("API key not found. Set ZILLOW_API_KEY in .env file")

    def get_price_history(self, zpid: str = None, url: str = None, address: str = None) -> Optional[Dict]:
        """
        Get price history for a property

        Args:
            zpid: Zillow Property ID (e.g., "30907787")
            url: Zillow property URL
            address: Property address (e.g., "3 W Forest Dr, Rochester, NY 14624")

        Returns:
            Price history data from Zillow API
        """
        if not any([zpid, url, address]):
            raise ValueError("Must provide zpid, url, or address")

        # Build query parameters
        params = ["recent_first=True", "which=zestimate_history"]

        if zpid:
            params.append(f"byzpid={zpid}")
        if url:
            encoded_url = url.replace(":", "%3A").replace("/", "%2F")
            params.append(f"byurl={encoded_url}")
        if address:
            encoded_addr = address.replace(" ", "%20").replace(",", "%2C")
            params.append(f"byaddress={encoded_addr}")

        endpoint = f"/graph_charts?{'&'.join(params)}"

        print(f"\n📊 Fetching price history...")
        if zpid:
            print(f"🆔 ZPID: {zpid}")
        if address:
            print(f"📍 Address: {address}")
        print()

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            conn.request("GET", endpoint, headers=headers)

            res = conn.getresponse()
            data = res.read()

            print(f"✅ API Response Status: {res.status}\n")

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                print(f"❌ API Error: {res.status}")
                print(f"Response: {data.decode('utf-8')}\n")
                return None

        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return None
        finally:
            conn.close()

    def analyze_trends(self, history_data: Dict) -> Dict:
        """
        Analyze price trends from history data

        Returns:
            Analysis including trend direction, volatility, and investment signals
        """
        if not history_data or 'DataPoints' not in history_data:
            return {"error": "No history data available"}

        # Extract home value chart data
        data_points_obj = history_data['DataPoints']
        if 'homeValueChartData' not in data_points_obj or not data_points_obj['homeValueChartData']:
            return {"error": "No price history available"}

        # Get "This home" data series
        home_series = None
        for series in data_points_obj['homeValueChartData']:
            if series.get('name') == 'This home':
                home_series = series
                break

        if not home_series or 'points' not in home_series:
            return {"error": "No price data found"}

        # Convert points to simplified format
        points = home_series['points']
        data_points = [{'date': p['x'], 'value': p['y']} for p in points]

        if not data_points or len(data_points) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Sort by date (most recent first)
        sorted_data = sorted(data_points, key=lambda x: x.get('date', 0), reverse=True)

        # Get current and historical values
        current_value = sorted_data[0].get('value', 0)
        oldest_value = sorted_data[-1].get('value', 0)

        # Calculate time periods
        one_year_ago = None
        six_months_ago = None

        current_date = sorted_data[0].get('date', 0)

        for point in sorted_data:
            point_date = point.get('date', 0)
            days_diff = (current_date - point_date) / (1000 * 60 * 60 * 24)

            if days_diff >= 365 and one_year_ago is None:
                one_year_ago = point.get('value', 0)
            if days_diff >= 180 and six_months_ago is None:
                six_months_ago = point.get('value', 0)

        # Calculate changes
        total_change = current_value - oldest_value
        total_change_pct = (total_change / oldest_value * 100) if oldest_value > 0 else 0

        one_year_change = (current_value - one_year_ago) if one_year_ago else 0
        one_year_change_pct = (one_year_change / one_year_ago * 100) if one_year_ago and one_year_ago > 0 else 0

        six_month_change = (current_value - six_months_ago) if six_months_ago else 0
        six_month_change_pct = (six_month_change / six_months_ago * 100) if six_months_ago and six_months_ago > 0 else 0

        # Determine trend
        if one_year_change_pct < -5:
            trend = "📉 DECLINING"
            signal = "🔥 POTENTIAL DISTRESSED DEAL"
        elif one_year_change_pct < 0:
            trend = "📉 Slightly Down"
            signal = "⚠️ Watch for opportunity"
        elif one_year_change_pct < 5:
            trend = "➡️ Stable"
            signal = "✅ Normal market"
        elif one_year_change_pct < 10:
            trend = "📈 Rising"
            signal = "💰 Appreciating market"
        else:
            trend = "📈 STRONG GROWTH"
            signal = "🚀 Hot market - may be overvalued"

        # Calculate volatility
        values = [p.get('value', 0) for p in sorted_data if p.get('value', 0) > 0]
        avg_value = sum(values) / len(values) if values else 0
        variance = sum((v - avg_value) ** 2 for v in values) / len(values) if values else 0
        volatility = (variance ** 0.5) / avg_value * 100 if avg_value > 0 else 0

        # Peak and trough
        peak_value = max(values) if values else 0
        trough_value = min(values) if values else 0
        from_peak_pct = ((current_value - peak_value) / peak_value * 100) if peak_value > 0 else 0

        return {
            "current_value": current_value,
            "oldest_value": oldest_value,
            "peak_value": peak_value,
            "trough_value": trough_value,
            "total_change": total_change,
            "total_change_pct": round(total_change_pct, 2),
            "one_year_change": one_year_change,
            "one_year_change_pct": round(one_year_change_pct, 2),
            "six_month_change": six_month_change,
            "six_month_change_pct": round(six_month_change_pct, 2),
            "from_peak_pct": round(from_peak_pct, 2),
            "trend": trend,
            "signal": signal,
            "volatility": round(volatility, 2),
            "data_points_count": len(sorted_data),
            "data_range_days": int((current_date - sorted_data[-1].get('date', current_date)) / (1000 * 60 * 60 * 24))
        }


def format_currency(amount):
    """Format number as currency"""
    return f"${amount:,.0f}"


def format_date(timestamp_ms):
    """Format timestamp to date"""
    if not timestamp_ms:
        return "Unknown"
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%b %d, %Y")


def print_price_history(history_data: Dict, analysis: Dict):
    """Pretty print price history and analysis"""

    print("\n" + "="*80)
    print("📊 FYNIX PRICE HISTORY ANALYSIS")
    print("="*80 + "\n")

    if 'error' in analysis:
        print(f"❌ {analysis['error']}")
        return

    # Current Status
    print("💰 CURRENT STATUS")
    print("-"*80)
    print(f"Current Value: {format_currency(analysis['current_value'])}")
    print(f"Peak Value: {format_currency(analysis['peak_value'])}")
    print(f"From Peak: {analysis['from_peak_pct']:+.1f}%")

    # Trends
    print("\n" + "-"*80)
    print("📈 PRICE TRENDS")
    print("-"*80)
    print(f"Trend: {analysis['trend']}")
    print(f"Signal: {analysis['signal']}")
    print(f"\n6 Month Change: {format_currency(analysis['six_month_change'])} ({analysis['six_month_change_pct']:+.1f}%)")
    print(f"1 Year Change: {format_currency(analysis['one_year_change'])} ({analysis['one_year_change_pct']:+.1f}%)")
    print(f"All Time Change: {format_currency(analysis['total_change'])} ({analysis['total_change_pct']:+.1f}%)")

    # Market Analysis
    print("\n" + "-"*80)
    print("🎯 MARKET ANALYSIS")
    print("-"*80)
    print(f"Volatility: {analysis['volatility']:.1f}%")
    print(f"Data Points: {analysis['data_points_count']} over {analysis['data_range_days']} days")

    # Investment Insight
    print("\n" + "-"*80)
    print("💡 INVESTMENT INSIGHT")
    print("-"*80)

    if analysis['one_year_change_pct'] < -10:
        print("🔥 STRONG BUY SIGNAL - Property value has declined significantly")
        print("   This could indicate a distressed seller or market correction")
        print("   Great opportunity for below-market purchase")
    elif analysis['one_year_change_pct'] < -5:
        print("✅ BUY SIGNAL - Property value trending down")
        print("   Possible opportunity to negotiate below Zestimate")
    elif analysis['from_peak_pct'] < -15:
        print("⚠️ POTENTIAL OPPORTUNITY - Property well below peak value")
        print("   Investigate reason for decline before proceeding")
    elif analysis['one_year_change_pct'] > 15:
        print("⚠️ CAUTION - Rapid appreciation may indicate overvaluation")
        print("   Market may be overheated, ensure deal makes sense")
    else:
        print("➡️ NORMAL MARKET - Stable appreciation within normal range")
        print("   Standard market conditions, proceed with normal analysis")

    # Recent History
    if 'DataPoints' in history_data and 'homeValueChartData' in history_data['DataPoints']:
        print("\n" + "-"*80)
        print("📅 RECENT PRICE HISTORY (Last 12 Months)")
        print("-"*80)

        # Get "This home" series
        home_series = None
        for series in history_data['DataPoints']['homeValueChartData']:
            if series.get('name') == 'This home':
                home_series = series
                break

        if home_series and 'points' in home_series:
            points = home_series['points']
            data_points = sorted([{'date': p['x'], 'value': p['y']} for p in points],
                               key=lambda x: x.get('date', 0), reverse=True)

            for i, point in enumerate(data_points[:12]):
                value = point.get('value', 0)
                date = format_date(point.get('date'))
                change = ((value - analysis['current_value']) / analysis['current_value'] * 100) if i > 0 else 0

                if i == 0:
                    print(f"{date}: {format_currency(value)} (Current)")
                else:
                    print(f"{date}: {format_currency(value)} ({change:+.1f}% from current)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='FYNIX Price History Analyzer - Track property value trends',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python price_history.py --zpid 30907787
  python price_history.py --address "3 W Forest Dr, Rochester, NY 14624"
  python price_history.py --zpid 14341709 --save history.json

  # Get ZPID from Zillow URL (the number at the end):
  # https://www.zillow.com/homedetails/123-Main-St/14341709_zpid/
        """
    )

    parser.add_argument('--zpid', help='Zillow Property ID')
    parser.add_argument('--url', help='Zillow property URL')
    parser.add_argument('--address', help='Property address')
    parser.add_argument('--save', help='Save results to JSON file', metavar='FILENAME')
    parser.add_argument('--raw', action='store_true', help='Show raw API response')

    args = parser.parse_args()

    if not any([args.zpid, args.url, args.address]):
        parser.error("Must provide at least one of: --zpid, --url, or --address")

    # Initialize analyzer
    analyzer = PropertyHistoryAnalyzer()

    # Get price history
    history = analyzer.get_price_history(
        zpid=args.zpid,
        url=args.url,
        address=args.address
    )

    if not history:
        print("❌ Failed to retrieve price history")
        sys.exit(1)

    # Show raw results if requested
    if args.raw:
        print("\n" + "="*80)
        print("RAW API RESPONSE")
        print("="*80 + "\n")
        print(json.dumps(history, indent=2))
        print()

    # Analyze trends
    analysis = analyzer.analyze_trends(history)

    # Print analysis
    print_price_history(history, analysis)

    # Save if requested
    if args.save:
        result = {
            "history": history,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }
        with open(args.save, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Results saved to: {args.save}\n")
