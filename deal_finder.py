"""
FYNIX Deal Finder - Efficient Investment Property Workflow
Optimized to minimize API calls while finding the best deals
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

from search_properties import PropertySearcher
from zillow_analyzer import ZillowPropertyAnalyzer
from price_history import PropertyHistoryAnalyzer
from rental_analyzer import RentalAnalyzer

# Load environment variables
load_dotenv()


class DealFinder:
    """Efficient workflow to find and analyze investment deals"""

    def __init__(self):
        self.searcher = PropertySearcher()
        self.analyzer = ZillowPropertyAnalyzer()
        self.history_analyzer = PropertyHistoryAnalyzer()
        self.rental_analyzer = RentalAnalyzer()

    def find_deals(
        self,
        location: str,
        min_price: int = None,
        max_price: int = None,
        beds_min: int = None,
        baths_min: int = None,
        initial_screen: int = 20,
        deep_analyze: int = 5,
        min_deal_score: int = 6,
        check_price_history: bool = True,
        check_rental: bool = True,
        save_file: str = None
    ) -> Dict:
        """
        Efficient deal-finding workflow

        Args:
            location: City, State or ZIP code
            min_price: Minimum price
            max_price: Maximum price
            beds_min: Minimum bedrooms
            baths_min: Minimum bathrooms
            initial_screen: Number of properties to quick-screen (default: 20)
            deep_analyze: Number of top properties to deep-analyze (default: 5)
            min_deal_score: Minimum deal score to consider (default: 6)
            check_price_history: Check price trends for top deals (default: True)
            check_rental: Analyze rental potential for top deals (default: True)
            save_file: Save results to JSON file

        Returns:
            Complete analysis results
        """
        results = {
            'search_criteria': {
                'location': location,
                'min_price': min_price,
                'max_price': max_price,
                'beds_min': beds_min,
                'baths_min': baths_min,
                'searched_at': datetime.now().isoformat()
            },
            'api_calls': 0,
            'properties_found': 0,
            'properties_screened': 0,
            'properties_analyzed': 0,
            'hot_deals': [],
            'all_results': []
        }

        print("\n" + "="*80)
        print("🔍 FYNIX DEAL FINDER - Optimized Workflow")
        print("="*80 + "\n")

        # STEP 1: Search for properties (1 API call)
        print("📊 STEP 1: SEARCHING FOR PROPERTIES")
        print("-"*80)

        search_results = self.searcher.search_by_location(
            location=location,
            min_price=min_price,
            max_price=max_price,
            beds_min=beds_min,
            baths_min=baths_min,
            page=1,
            sort_order="Price_Low_High"
        )

        results['api_calls'] += 1

        if not search_results or 'searchResults' not in search_results:
            print("❌ No properties found")
            return results

        properties = search_results['searchResults']
        total_found = search_results.get('resultsCount', {}).get('totalMatchingCount', len(properties))
        results['properties_found'] = total_found

        print(f"✅ Found {total_found} properties matching criteria")
        print(f"📋 Screening top {min(initial_screen, len(properties))} properties...\n")

        # STEP 2: Quick screen properties (use search data, 0 additional API calls)
        print("🎯 STEP 2: QUICK SCREENING (using search data)")
        print("-"*80)

        screened = []
        for i, item in enumerate(properties[:initial_screen], 1):
            if 'property' not in item:
                continue

            prop = item['property']
            addr = prop.get('address', {})

            # Extract basic info from search results
            zpid = prop.get('zpid')
            address = addr.get('streetAddress', 'Unknown')
            city = addr.get('city', '')
            state = addr.get('state', '')
            zipcode = addr.get('zipcode', '')
            price = prop.get('price', {}).get('value', 0)
            beds = prop.get('bedrooms', 0)
            baths = prop.get('bathrooms', 0)
            sqft = prop.get('livingArea', 0)

            # Quick screening criteria
            if price > 0 and sqft > 0:
                price_per_sqft = price / sqft

                screened.append({
                    'zpid': zpid,
                    'address': address,
                    'city': city,
                    'state': state,
                    'zipcode': zipcode,
                    'full_address': f"{address}, {city}, {state} {zipcode}",
                    'price': price,
                    'beds': beds,
                    'baths': baths,
                    'sqft': sqft,
                    'price_per_sqft': price_per_sqft
                })

                print(f"{i}. {address}, {city} - ${price:,} | {beds}bed {baths}bath | ${price_per_sqft:.0f}/sqft")

        results['properties_screened'] = len(screened)
        print(f"\n✅ Screened {len(screened)} properties\n")

        # STEP 3: Detailed analysis on top properties (N API calls)
        print(f"🔬 STEP 3: DETAILED ANALYSIS (Top {deep_analyze} properties)")
        print("-"*80)

        analyzed = []
        for i, prop in enumerate(screened[:deep_analyze], 1):
            print(f"\n{i}. Analyzing: {prop['full_address']}")
            print(f"   List Price: ${prop['price']:,}")

            # Analyze property (1 API call)
            # Pass search data as fallback in case API doesn't return all fields
            analysis = self.analyzer.analyze_property(
                address=prop['address'],
                city=prop['city'],
                state=prop['state'],
                zipcode=prop['zipcode'],
                search_data=prop  # Pass search data with known values
            )
            results['api_calls'] += 1

            if not analysis.get('success'):
                print(f"   ❌ Failed to analyze")
                continue

            deal_score = analysis['deal_quality']['score']
            recommendation = analysis['deal_quality']['recommendation']

            print(f"   Deal Score: {deal_score}/10 - {analysis['deal_quality']['label']}")
            print(f"   MAO (70%): ${analysis['investor_analysis']['mao_70_percent']:,.0f}")
            print(f"   Recommendation: {recommendation}")

            prop['detailed_analysis'] = analysis
            prop['deal_score'] = deal_score

            analyzed.append(prop)

        results['properties_analyzed'] = len(analyzed)

        # Sort by deal score
        analyzed.sort(key=lambda x: x['deal_score'], reverse=True)

        # STEP 4: Deep dive on hot deals (price history + rental analysis)
        hot_deals = [p for p in analyzed if p['deal_score'] >= min_deal_score]

        if hot_deals:
            print(f"\n🔥 STEP 4: DEEP DIVE ON HOT DEALS (Score {min_deal_score}+)")
            print("-"*80)
            print(f"Found {len(hot_deals)} properties worth deeper analysis\n")

            for i, prop in enumerate(hot_deals, 1):
                print(f"\n{'='*80}")
                print(f"🔥 HOT DEAL #{i}: {prop['full_address']}")
                print(f"{'='*80}")

                analysis = prop['detailed_analysis']
                zpid = prop['zpid']

                # Price History Analysis (1 API call per hot deal)
                if check_price_history:
                    print(f"\n📈 Price Trend Analysis...")
                    history_data = self.history_analyzer.get_price_history(zpid=str(zpid))
                    results['api_calls'] += 1

                    if history_data:
                        trend_analysis = self.history_analyzer.analyze_trends(history_data)
                        prop['price_history'] = trend_analysis

                        if 'error' not in trend_analysis:
                            print(f"   Current Value: ${trend_analysis['current_value']:,}")
                            print(f"   Trend: {trend_analysis['trend']}")
                            print(f"   1-Year Change: {trend_analysis['one_year_change_pct']:+.1f}%")
                            print(f"   Signal: {trend_analysis['signal']}")

                # Rental Analysis (1 API call if fetching rent history, 0 if using estimate)
                if check_rental:
                    print(f"\n🏠 Rental Investment Analysis...")

                    # Use rent zestimate from property details (no additional API call)
                    rent_estimate = analysis['property'].get('rent_zestimate', 0)

                    if rent_estimate > 0:
                        rental_analysis = self.rental_analyzer.analyze_rental_investment(
                            purchase_price=prop['price'],
                            monthly_rent=rent_estimate
                        )
                        prop['rental_analysis'] = rental_analysis

                        print(f"   Monthly Rent: ${rent_estimate:,}")
                        print(f"   Monthly Cash Flow: ${rental_analysis['cash_flow']['monthly_cash_flow']:,.0f}")
                        print(f"   Cash-on-Cash ROI: {rental_analysis['roi_metrics']['cash_on_cash_return']:.1f}%")
                        print(f"   Cap Rate: {rental_analysis['roi_metrics']['cap_rate']:.1f}%")
                        print(f"   Grade: {rental_analysis['rating']['grade']}")

                # Summary
                print(f"\n💡 INVESTMENT SUMMARY")
                print(f"   Deal Score: {prop['deal_score']}/10")
                print(f"   List Price: ${prop['price']:,}")
                print(f"   ARV: ${analysis['valuation']['arv']:,}")
                print(f"   MAO (70%): ${analysis['investor_analysis']['mao_70_percent']:,}")
                print(f"   Est. Profit: ${analysis['investor_analysis']['profit_potential']:,}")
                print(f"   ROI: {analysis['investor_analysis']['roi_percentage']:.1f}%")

            results['hot_deals'] = hot_deals
        else:
            print(f"\n⚠️  STEP 4: No properties scored {min_deal_score}+ for deep analysis")

        results['all_results'] = analyzed

        # STEP 5: Summary Report
        print(f"\n\n{'='*80}")
        print("📊 FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total API Calls Used: {results['api_calls']}")
        print(f"Properties Found: {results['properties_found']}")
        print(f"Properties Screened: {results['properties_screened']}")
        print(f"Properties Analyzed: {results['properties_analyzed']}")
        print(f"Hot Deals Found: {len(hot_deals)}")
        print(f"\nTop Deals:")

        for i, prop in enumerate(analyzed[:5], 1):
            print(f"  {i}. {prop['full_address']}")
            print(f"     ${prop['price']:,} | Score: {prop['deal_score']}/10 | {prop['detailed_analysis']['deal_quality']['label']}")

        # Save results
        if save_file:
            with open(save_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Complete results saved to: {save_file}")

        print(f"\n{'='*80}\n")

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='FYNIX Deal Finder - Optimized workflow to find investment deals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python deal_finder.py --location "Georgia" --max 100000

  # Focused search
  python deal_finder.py --location "Atlanta, GA" --min 50000 --max 100000 --beds 3

  # Aggressive screening
  python deal_finder.py --location "30008" --max 150000 --screen 30 --analyze 10

  # Quick scan (minimal API usage)
  python deal_finder.py --location "Cobb County, GA" --max 100000 --screen 20 --analyze 3

  # Full analysis with save
  python deal_finder.py --location "Georgia" --max 100000 --beds 3 --save deals.json

Workflow:
  1. Search (1 API call) - Gets 20 properties
  2. Quick screen (0 API calls) - Uses search data
  3. Detailed analysis (N API calls) - Top N properties
  4. Deep dive (2N API calls) - Price history + rental for hot deals

  Total: 1 + N + 2M API calls (where M = hot deals)
        """
    )

    parser.add_argument('--location', required=True, help='City, State or ZIP code')
    parser.add_argument('--min', type=int, help='Minimum price')
    parser.add_argument('--max', type=int, help='Maximum price')
    parser.add_argument('--beds', type=int, help='Minimum bedrooms')
    parser.add_argument('--baths', type=int, help='Minimum bathrooms')

    parser.add_argument('--screen', type=int, default=20, help='Number of properties to quick-screen (default: 20)')
    parser.add_argument('--analyze', type=int, default=5, help='Number of properties to analyze in detail (default: 5)')
    parser.add_argument('--min-score', type=int, default=6, help='Minimum deal score for deep analysis (default: 6)')

    parser.add_argument('--no-history', action='store_true', help='Skip price history analysis')
    parser.add_argument('--no-rental', action='store_true', help='Skip rental analysis')

    parser.add_argument('--save', help='Save results to JSON file')

    args = parser.parse_args()

    # Run deal finder
    finder = DealFinder()

    results = finder.find_deals(
        location=args.location,
        min_price=args.min,
        max_price=args.max,
        beds_min=args.beds,
        baths_min=args.baths,
        initial_screen=args.screen,
        deep_analyze=args.analyze,
        min_deal_score=args.min_score,
        check_price_history=not args.no_history,
        check_rental=not args.no_rental,
        save_file=args.save
    )
