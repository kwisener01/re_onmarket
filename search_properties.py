"""
FYNIX Property Search - Search properties using AI prompts
Search for investment properties using natural language queries
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import http.client
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from zillow_analyzer import ZillowPropertyAnalyzer, format_currency

# Load environment variables
load_dotenv()


class PropertySearcher:
    """Search for properties using AI prompts"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ZILLOW_API_KEY')
        self.api_host = "zillow-working-api.p.rapidapi.com"

        if not self.api_key:
            raise ValueError("API key not found. Set ZILLOW_API_KEY in .env file")

    def search_by_location(
        self,
        location: str,
        min_price: int = None,
        max_price: int = None,
        beds_min: int = None,
        beds_max: int = None,
        baths_min: int = None,
        home_type: str = None,
        page: int = 1,
        sort_order: str = "Price_Low_High"
    ) -> Optional[Dict]:
        """
        Search properties by location with price and criteria filters

        Args:
            location: City, State or ZIP code (e.g., "Atlanta, GA" or "30008")
            min_price: Minimum price
            max_price: Maximum price
            beds_min: Minimum bedrooms
            beds_max: Maximum bedrooms
            baths_min: Minimum bathrooms
            home_type: Property type (Houses, Apartments, Condos, Townhomes, etc.)
            page: Page number for pagination
            sort_order: Sort order (Price_Low_High, Price_High_Low, Newest, etc.)

        Returns:
            Search results from Zillow API
        """
        print(f"\n🔍 Searching Properties")
        print(f"📍 Location: {location}")
        if min_price or max_price:
            price_range = f"${min_price:,}" if min_price else "Any"
            price_range += f" - ${max_price:,}" if max_price else "+"
            print(f"💰 Price Range: {price_range}")
        if beds_min:
            print(f"🛏️  Bedrooms: {beds_min}+ beds")
        if baths_min:
            print(f"🚿 Bathrooms: {baths_min}+ baths")
        print(f"📄 Page: {page} | Sort: {sort_order}\n")

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            # Build AI prompt from parameters
            prompt_parts = []

            if beds_min:
                prompt_parts.append(f"{beds_min}+ bedroom")

            prompt_parts.append("homes for sale in")
            prompt_parts.append(location)

            if min_price and max_price:
                prompt_parts.append(f"between ${min_price:,} and ${max_price:,}")
            elif max_price:
                prompt_parts.append(f"under ${max_price:,}")
            elif min_price:
                prompt_parts.append(f"over ${min_price:,}")

            if baths_min:
                prompt_parts.append(f"with {baths_min}+ bathrooms")

            prompt = " ".join(prompt_parts)
            encoded_prompt = prompt.replace(" ", "%20").replace(",", "%2C").replace("$", "%24").replace("+", "%2B")

            endpoint = f"/search/byaiprompt?ai_search_prompt={encoded_prompt}&page={page}&sortOrder={sort_order}"
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

    def search_by_prompt(self, prompt: str, page: int = 1, sort_order: str = "Homes_for_you") -> Optional[Dict]:
        """
        Search properties using AI prompt

        Args:
            prompt: Natural language search query (e.g., "2 bedroom homes for sale in Atlanta under 100k")
            page: Page number for pagination
            sort_order: Sort order (Homes_for_you, Price_High_Low, Price_Low_High, etc.)

        Returns:
            Search results from Zillow API
        """
        # URL encode the prompt
        encoded_prompt = prompt.replace(" ", "%20").replace(",", "%2C")

        print(f"\n🔍 Searching: {prompt}")
        print(f"📄 Page: {page} | Sort: {sort_order}\n")

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            endpoint = f"/search/byaiprompt?ai_search_prompt={encoded_prompt}&page={page}&sortOrder={sort_order}"
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

    def analyze_search_results(self, results: Dict, max_analyze: int = 10) -> List[Dict]:
        """
        Analyze properties from search results for investment potential

        Args:
            results: Search results from Zillow API
            max_analyze: Maximum number of properties to analyze in detail

        Returns:
            List of analyzed properties sorted by deal quality
        """
        if not results or 'searchResults' not in results:
            print("❌ No properties found in results")
            return []

        properties = results['searchResults']
        total_results = results.get('resultsCount', {}).get('totalMatchingCount', len(properties))

        print(f"\n📊 Found {total_results} properties")
        print(f"📋 Analyzing top {min(max_analyze, len(properties))} properties...\n")

        analyzer = ZillowPropertyAnalyzer()
        analyzed_properties = []

        for i, item in enumerate(properties[:max_analyze], 1):
            try:
                # Extract property from search result
                if 'property' not in item:
                    print(f"⏭️  Skipping result {i} - no property data")
                    continue

                prop = item['property']

                # Extract address details
                addr = prop.get('address', {})
                address = addr.get('streetAddress', '')
                city = addr.get('city', '')
                state = addr.get('state', '')
                zipcode = addr.get('zipcode', '')

                if not all([address, city, state, zipcode]):
                    print(f"⏭️  Skipping property {i} - incomplete address")
                    continue

                print(f"\n{i}. Analyzing: {address}, {city}, {state} {zipcode}")

                # Analyze the property
                result = analyzer.analyze_property(
                    address=address,
                    city=city,
                    state=state,
                    zipcode=zipcode
                )

                if result.get('success'):
                    score = result['deal_quality']['score']
                    label = result['deal_quality']['label']
                    print(f"   Score: {score}/10 - {label}")
                    analyzed_properties.append(result)
                else:
                    print(f"   ❌ Failed: {result.get('error')}")

            except Exception as e:
                print(f"   ❌ Error analyzing property {i}: {str(e)}")
                continue

        # Sort by deal quality score
        analyzed_properties.sort(key=lambda x: x['deal_quality']['score'], reverse=True)

        return analyzed_properties


def print_search_summary(properties: List[Dict]):
    """Print a summary of analyzed properties ranked by deal quality"""
    if not properties:
        print("\n❌ No properties were successfully analyzed")
        return

    print("\n" + "="*80)
    print("📊 INVESTMENT ANALYSIS SUMMARY - RANKED BY DEAL QUALITY")
    print("="*80 + "\n")

    for i, result in enumerate(properties, 1):
        prop = result['property']
        deal = result['deal_quality']
        inv = result['investor_analysis']

        print(f"{i}. {prop['address']}")
        print(f"   Score: {deal['score']}/10 - {deal['label']}")
        print(f"   Recommendation: {deal['recommendation']}")
        print(f"   List: {format_currency(prop['list_price'])} | MAO: {format_currency(inv['mao_70_percent'])}")
        print(f"   Profit: {format_currency(inv['profit_potential'])} ({inv['roi_percentage']}% ROI)")
        print(f"   {prop['beds']} bed | {prop['baths']} bath | {prop['sqft']:,} sqft | Built {prop['year_built']}\n")


def save_results(properties: List[Dict], filename: str):
    """Save analyzed properties to JSON file"""
    with open(filename, 'w') as f:
        json.dump(properties, f, indent=2)
    print(f"\n💾 Full results saved to: {filename}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='FYNIX Property Search - Find investment properties',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # AI Prompt Search
  python search_properties.py --prompt "2 bedroom homes for sale in Atlanta under 100k"
  python search_properties.py --prompt "fixer uppers in Jacksonville FL" --max 5

  # Location-Based Search with Price Range
  python search_properties.py --location "Atlanta, GA" --min 50000 --max 100000
  python search_properties.py --location "30008" --min 60000 --max 150000 --beds 3
  python search_properties.py --location "Marietta, GA" --max 200000 --beds 3 --baths 2

  # Advanced Options
  python search_properties.py --location "Cobb County, GA" --max 100000 --save deals.json
  python search_properties.py --location "Atlanta, GA" --min 50000 --max 80000 --sort Price_Low_High

Sort Options:
  Price_Low_High, Price_High_Low, Newest, Bedrooms, Bathrooms, Homes_for_you
        """
    )

    # Search method selection
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--prompt', help='AI search prompt (e.g., "2 bedroom homes for sale in Atlanta under 100k")')
    search_group.add_argument('--location', help='City, State or ZIP code (e.g., "Atlanta, GA" or "30008")')

    # Location-based search parameters
    parser.add_argument('--min', type=int, help='Minimum price', metavar='PRICE')
    parser.add_argument('--max', type=int, help='Maximum price', metavar='PRICE')
    parser.add_argument('--beds', type=int, help='Minimum bedrooms')
    parser.add_argument('--beds-max', type=int, help='Maximum bedrooms')
    parser.add_argument('--baths', type=int, help='Minimum bathrooms')
    parser.add_argument('--type', help='Home type (Houses, Apartments, Condos, Townhomes)')

    # Common parameters
    parser.add_argument('--page', '-p', type=int, default=1, help='Page number for results (default: 1)')
    parser.add_argument('--sort', '-s', default=None,
                       choices=['Homes_for_you', 'Price_Low_High', 'Price_High_Low', 'Newest', 'Bedrooms', 'Bathrooms'],
                       help='Sort order for results')
    parser.add_argument('--analyze', '-a', type=int, default=10, help='Number of properties to analyze (default: 10)', metavar='NUM')
    parser.add_argument('--save', help='Save results to JSON file', metavar='FILENAME')
    parser.add_argument('--raw', action='store_true', help='Show raw search results without analysis')

    args = parser.parse_args()

    # Initialize searcher
    searcher = PropertySearcher()

    # Determine sort order
    if args.sort:
        sort_order = args.sort
    elif args.location:
        sort_order = "Price_Low_High"  # Default for location search
    else:
        sort_order = "Homes_for_you"  # Default for AI prompt search

    # Search for properties
    if args.prompt:
        results = searcher.search_by_prompt(
            prompt=args.prompt,
            page=args.page,
            sort_order=sort_order
        )
    else:  # args.location
        results = searcher.search_by_location(
            location=args.location,
            min_price=args.min,
            max_price=args.max,
            beds_min=args.beds,
            beds_max=args.beds_max,
            baths_min=args.baths,
            home_type=args.type,
            page=args.page,
            sort_order=sort_order
        )

    if not results:
        print("❌ Search failed or returned no results")
        sys.exit(1)

    # Show raw results if requested
    if args.raw:
        print("\n" + "="*80)
        print("RAW SEARCH RESULTS")
        print("="*80 + "\n")
        print(json.dumps(results, indent=2))
        sys.exit(0)

    # Analyze the results
    analyzed = searcher.analyze_search_results(results, max_analyze=args.analyze)

    # Print summary
    print_search_summary(analyzed)

    # Save if requested
    if args.save:
        save_results(analyzed, args.save)
