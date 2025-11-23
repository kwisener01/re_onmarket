"""
FYNIX Property Analyzer - Zillow API Integration
Analyzes investment properties and calculates MAO using 70% rule
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import http.client
import json
from datetime import datetime
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ZillowPropertyAnalyzer:
    """Analyzes investment properties using Zillow API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ZILLOW_API_KEY')
        self.api_host = "zillow-working-api.p.rapidapi.com"
        
        if not self.api_key:
            raise ValueError("API key not found. Set ZILLOW_API_KEY in .env file")
    
    def get_property_data(self, address: str, city: str, state: str, zipcode: str) -> Optional[Dict]:
        """
        Fetch property data from Zillow API
        
        Returns raw Zillow API response
        """
        # Format address for URL
        full_address = f"{address}, {city}, {state} {zipcode}"
        encoded_address = full_address.replace(" ", "%20").replace(",", "%2C")
        
        print(f"\n🔍 Fetching data for: {full_address}")
        print(f"📡 API Endpoint: /pro/byaddress?propertyaddress={encoded_address}\n")
        
        try:
            conn = http.client.HTTPSConnection(self.api_host)
            
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }
            
            endpoint = f"/pro/byaddress?propertyaddress={encoded_address}"
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
    
    def detect_fixer_keywords(self, text: str) -> Dict:
        """
        Detect keywords that indicate a fixer-upper property
        Returns matches and a flag
        """
        if not text:
            return {"is_fixer": False, "keywords_found": [], "keyword_count": 0}

        text_lower = text.lower()

        fixer_keywords = [
            # Primary fixer terms
            "fixer", "fixer-upper", "fixer upper", "fixerupper",
            "fix and flip", "flip", "fix",

            # Handyman terms
            "handyman special", "handyman's special", "handy man",

            # TLC and work needed
            "tlc", "needs tlc", "needs work", "needs updating",
            "needs repair", "needs renovation", "needs renovations",
            "major renovation", "major renovations",

            # As-is condition
            "as-is", "as is", "sold as-is", "selling as-is",

            # Investor language
            "investor special", "investor opportunity", "investor dream",
            "investor's dream", "investors dream",

            # Cash terms
            "cash only", "cash buyer",

            # Renovation terms
            "rehab", "renovation", "renovations", "renovation opportunity",
            "gut renovation", "gut",

            # Opportunity language
            "flip opportunity", "bring your hammer",
            "cosmetic updates needed", "cosmetic updates",
            "high potential", "so much potential",

            # Price signals
            "below market", "motivated seller", "must sell",
            "bring all offers", "priced to sell",

            # Distressed sales
            "estate sale", "foreclosure", "bank owned", "short sale"
        ]

        found = []
        for keyword in fixer_keywords:
            if keyword in text_lower:
                found.append(keyword)

        return {
            "is_fixer": len(found) > 0,
            "keywords_found": found,
            "keyword_count": len(found)
        }

    def calculate_rehab_estimate(self, year_built: int, sqft: int) -> Dict:
        """
        Calculate rehab costs for ALL scenarios (Light, Medium, Heavy)
        Don't pick one - show all possibilities for scanning
        """
        current_year = datetime.now().year
        property_age = current_year - year_built

        # Calculate all three scenarios
        light = sqft * 25
        medium = sqft * 40
        heavy = sqft * 60

        # Suggest which is most likely based on age, but return all
        if property_age <= 20:
            suggested = "Light"
            description = "Likely cosmetic: paint, flooring, fixtures"
        elif property_age <= 50:
            suggested = "Medium"
            description = "Likely needs: Kitchen, baths, HVAC, roof"
        else:
            suggested = "Heavy"
            description = "Likely needs: Full renovation"

        return {
            "light": light,
            "light_per_sqft": 25,
            "medium": medium,
            "medium_per_sqft": 40,
            "heavy": heavy,
            "heavy_per_sqft": 60,
            "suggested_scope": suggested,
            "description": description,
            "property_age": property_age
        }
    
    def calculate_deal_score(self, list_price: float, arv: float, property_age: int) -> Dict:
        """Score deal from 1-10"""
        score = 5
        reasons = []
        
        price_to_arv = list_price / arv if arv > 0 else 1.0
        
        if price_to_arv <= 0.55:
            score += 2
            reasons.append("Deep discount (45%+ below ARV)")
        elif price_to_arv <= 0.65:
            score += 1
            reasons.append("Good discount (35%+ below ARV)")
        
        if property_age <= 20:
            score += 1
            reasons.append("Newer property (light rehab)")
        elif property_age > 50:
            score -= 1
            reasons.append("Older property (heavy rehab)")
        
        if price_to_arv > 0.75:
            score -= 2
            reasons.append("Overpriced (>75% of ARV)")
        
        score = max(1, min(10, score))
        
        if score >= 9:
            label = "🔥 HOT DEAL"
            recommendation = "BUY IMMEDIATELY"
        elif score >= 8:
            label = "🔥 EXCELLENT"
            recommendation = "BUY - Strong opportunity"
        elif score >= 7:
            label = "✅ GOOD"
            recommendation = "BUY - Solid deal"
        elif score >= 6:
            label = "⚠️ FAIR"
            recommendation = "CONDITIONAL - Verify carefully"
        else:
            label = "❌ POOR"
            recommendation = "PASS - No profit"
        
        return {
            "score": score,
            "label": label,
            "recommendation": recommendation,
            "reasons": reasons,
            "price_to_arv_ratio": round(price_to_arv, 3)
        }
    
    def analyze_property(self, address: str, city: str, state: str, zipcode: str, search_data: Dict = None) -> Dict:
        """
        Complete property analysis

        Args:
            address, city, state, zipcode: Property location
            search_data: Optional data from search results to use as fallback

        Returns comprehensive investor brief
        """
        # Get raw Zillow data
        zillow_data = self.get_property_data(address, city, state, zipcode)
        
        if not zillow_data:
            return {
                "success": False,
                "error": "Unable to fetch property data"
            }
        
        # Save raw response for inspection
        print("📄 Raw Zillow Response:")
        print(json.dumps(zillow_data, indent=2))
        print("\n" + "="*80 + "\n")
        
        # Extract property details
        # NOTE: Adjust these field names based on actual API response
        try:
            # Try different possible response structures
            if 'data' in zillow_data:
                prop = zillow_data['data']
            elif 'property' in zillow_data:
                prop = zillow_data['property']
            else:
                prop = zillow_data

            # Helper function to try multiple field names
            def extract_field(prop_dict, *field_names, default=0):
                """Try multiple field names and return first non-zero value"""
                for field in field_names:
                    if '.' in field:
                        # Handle nested fields like 'price.value'
                        parts = field.split('.')
                        val = prop_dict
                        for part in parts:
                            if isinstance(val, dict):
                                val = val.get(part)
                            else:
                                val = None
                                break
                        if val is not None and val != 0:
                            return val
                    else:
                        val = prop_dict.get(field)
                        if val is not None and val != 0:
                            return val
                return default

            # Extract fields with multiple fallbacks
            beds = extract_field(prop, 'bedrooms', 'beds', 'bedroomsCount', 'numBedrooms', default=3)
            baths = extract_field(prop, 'bathrooms', 'baths', 'bathroomsCount', 'numBathrooms', default=2)
            sqft = extract_field(prop, 'livingArea', 'sqft', 'squareFeet', 'floorArea', 'livingAreaSqFt', 'resoFacts.livingArea', default=1500)
            year_built = extract_field(prop, 'yearBuilt', 'year_built', 'yearBuilt', 'resoFacts.yearBuilt', default=2000)

            # Price extraction (can be nested)
            list_price = extract_field(prop, 'price.value', 'price', 'listPrice', 'askingPrice', 'currentPrice', default=0)

            # Zestimate extraction
            zestimate = extract_field(prop, 'zestimate', 'homeValue', 'estimate', 'estimatedValue', 'valuation', default=list_price)

            # Use search data as fallback if API didn't return values
            if search_data:
                if beds in [0, 3]:  # 3 is default, use search data if available
                    beds = search_data.get('beds', beds)
                if baths in [0, 2]:
                    baths = search_data.get('baths', baths)
                if sqft in [0, 1500]:
                    sqft = search_data.get('sqft', sqft)
                if list_price == 0:
                    list_price = search_data.get('price', 0)
                if zestimate in [0, list_price]:
                    # Estimate zestimate as 110% of list price if not available
                    zestimate = search_data.get('zestimate', list_price * 1.1 if list_price > 0 else 0)

            # Debug logging
            print(f"🔍 Extracted values:")
            print(f"   Beds: {beds}, Baths: {baths}, Sqft: {sqft}")
            print(f"   Year: {year_built}, Price: ${list_price:,}, Zestimate: ${zestimate:,}")
            print()
            
            # Conservative ARV (95% of Zestimate)
            arv_conservative = zestimate * 0.95

            # Calculate rehab for all scenarios
            rehab = self.calculate_rehab_estimate(year_built, sqft)

            # Calculate MAO for ALL THREE rehab scenarios (Light, Medium, Heavy)
            # This allows scanner to catch borderline deals
            mao_light = (arv_conservative * 0.70) - rehab['light']
            mao_medium = (arv_conservative * 0.70) - rehab['medium']
            mao_heavy = (arv_conservative * 0.70) - rehab['heavy']

            # Calculate profit for each scenario
            profit_light = mao_light - list_price
            profit_medium = mao_medium - list_price
            profit_heavy = mao_heavy - list_price

            # Determine best scenario
            if list_price <= mao_light:
                best_scenario = "Works with Light Rehab"
                best_profit = profit_light
            elif list_price <= mao_medium:
                best_scenario = "Works with Medium Rehab"
                best_profit = profit_medium
            elif list_price <= mao_heavy:
                best_scenario = "Works with Heavy Rehab"
                best_profit = profit_heavy
            else:
                best_scenario = "Not a Deal"
                best_profit = profit_heavy

            # Extract description for keyword detection - check multiple possible fields
            description_text = ""
            possible_fields = [
                'description', 'remarks', 'propertyDescription',
                'listingDescription', 'publicRemarks', 'agentRemarks',
                'mlsDescription', 'listing_description'
            ]

            for field in possible_fields:
                if field in prop and prop.get(field):
                    description_text = str(prop.get(field))
                    break

            # Also check nested structures
            if not description_text and 'listing' in prop and isinstance(prop['listing'], dict):
                listing = prop['listing']
                for field in possible_fields:
                    if field in listing and listing.get(field):
                        description_text = str(listing.get(field))
                        break

            print(f"   📝 Description text found: {'Yes (' + str(len(description_text)) + ' chars)' if description_text else 'No'}")

            # Detect fixer keywords
            keyword_analysis = self.detect_fixer_keywords(description_text)

            # Score deal (use medium as baseline)
            deal_score = self.calculate_deal_score(list_price, arv_conservative, rehab['property_age'])
            
            # Build response with all scenarios
            result = {
                "success": True,
                "property": {
                    "address": f"{address}, {city}, {state} {zipcode}",
                    "beds": beds,
                    "baths": baths,
                    "sqft": sqft,
                    "year_built": year_built,
                    "property_age": rehab['property_age'],
                    "list_price": list_price
                },
                "valuation": {
                    "zestimate": zestimate,
                    "arv_conservative": round(arv_conservative, 0),
                    "arv_source": "Zillow Zestimate × 0.95"
                },
                "rehab_scenarios": {
                    "light": {
                        "cost": round(rehab['light'], 0),
                        "per_sqft": rehab['light_per_sqft'],
                        "description": "Cosmetic: paint, flooring, fixtures"
                    },
                    "medium": {
                        "cost": round(rehab['medium'], 0),
                        "per_sqft": rehab['medium_per_sqft'],
                        "description": "Kitchen, baths, HVAC, roof"
                    },
                    "heavy": {
                        "cost": round(rehab['heavy'], 0),
                        "per_sqft": rehab['heavy_per_sqft'],
                        "description": "Full renovation, foundation, systems"
                    },
                    "suggested": rehab['suggested_scope']
                },
                "investor_analysis": {
                    # MAO for each rehab scenario
                    "mao_light_rehab": round(mao_light, 0),
                    "mao_medium_rehab": round(mao_medium, 0),
                    "mao_heavy_rehab": round(mao_heavy, 0),
                    # Profit for each scenario
                    "profit_light": round(profit_light, 0),
                    "profit_medium": round(profit_medium, 0),
                    "profit_heavy": round(profit_heavy, 0),
                    # Best scenario
                    "best_scenario": best_scenario,
                    "best_profit": round(best_profit, 0),
                    # Legacy fields (using medium as default)
                    "mao_70_percent": round(mao_medium, 0),
                    "profit_potential": round(profit_medium, 0),
                    "roi_percentage": round((profit_medium / list_price * 100), 1) if list_price > 0 else 0
                },
                "keywords": {
                    "is_fixer": keyword_analysis['is_fixer'],
                    "keywords_found": keyword_analysis['keywords_found'],
                    "keyword_count": keyword_analysis['keyword_count']
                },
                "deal_quality": deal_score,
                "analysis_date": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing Zillow data: {str(e)}",
                "raw_data": zillow_data
            }


def format_currency(amount):
    """Format number as currency"""
    return f"${amount:,.0f}"


def print_analysis(result: Dict):
    """Pretty print analysis results"""
    if not result.get('success'):
        print(f"❌ ERROR: {result.get('error')}")
        return
    
    print("\n" + "="*80)
    print("🏠 FYNIX PROPERTY ANALYSIS REPORT")
    print("="*80 + "\n")
    
    # Property Details
    prop = result['property']
    print(f"📍 ADDRESS: {prop['address']}")
    print(f"🏡 SPECS: {prop['beds']} bed | {prop['baths']} bath | {prop['sqft']:,} sqft")
    print(f"📅 BUILT: {prop['year_built']} ({prop['property_age']} years old)")
    print(f"💵 LIST PRICE: {format_currency(prop['list_price'])}")
    
    # Valuation
    print("\n" + "-"*80)
    print("💰 VALUATION")
    print("-"*80)
    val = result['valuation']
    print(f"Zillow Zestimate: {format_currency(val['zestimate'])}")
    print(f"ARV (Conservative): {format_currency(val['arv_conservative'])}")
    
    # Rehab
    print("\n" + "-"*80)
    print("🔨 REHAB ESTIMATE")
    print("-"*80)
    rehab = result['rehab']
    print(f"Scope: {rehab['scope']} - {rehab['description']}")
    print(f"Estimated Cost: {format_currency(rehab['recommended'])} (${rehab['per_sqft']}/sqft)")
    
    # Investor Analysis
    print("\n" + "-"*80)
    print("📊 INVESTOR ANALYSIS (70% RULE)")
    print("-"*80)
    inv = result['investor_analysis']
    print(f"Maximum Allowable Offer (70%): {format_currency(inv['mao_70_percent'])}")
    print(f"Conservative MAO (65%):        {format_currency(inv['mao_65_percent'])}")
    print(f"Aggressive MAO (75%):          {format_currency(inv['mao_75_percent'])}")
    print(f"\nProfit Potential: {format_currency(inv['profit_potential'])}")
    print(f"ROI: {inv['roi_percentage']}%")
    
    # Deal Quality
    print("\n" + "-"*80)
    print("⭐ DEAL QUALITY SCORE")
    print("-"*80)
    deal = result['deal_quality']
    print(f"Score: {deal['score']}/10 - {deal['label']}")
    print(f"Recommendation: {deal['recommendation']}")
    print(f"Price/ARV Ratio: {deal['price_to_arv_ratio']}")
    if deal['reasons']:
        print("\nFactors:")
        for reason in deal['reasons']:
            print(f"  • {reason}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='FYNIX Property Analyzer - Analyze investment properties using Zillow API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python zillow_analyzer.py "1875 AVONDALE Circle" "Jacksonville" "FL" "32205"
  python zillow_analyzer.py "2598 Hencley Cir SW" "Marietta" "GA" "30008"
        """
    )

    parser.add_argument('address', help='Street address (e.g., "1875 AVONDALE Circle")')
    parser.add_argument('city', help='City name (e.g., "Jacksonville")')
    parser.add_argument('state', help='State code (e.g., "FL")')
    parser.add_argument('zipcode', help='ZIP code (e.g., "32205")')
    parser.add_argument('--save', '-s', help='Save results to JSON file', metavar='FILENAME')

    args = parser.parse_args()

    # Run analysis
    analyzer = ZillowPropertyAnalyzer()

    result = analyzer.analyze_property(
        address=args.address,
        city=args.city,
        state=args.state,
        zipcode=args.zipcode
    )

    # Print analysis
    print_analysis(result)

    # Save to file if requested
    if args.save:
        import json
        with open(args.save, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Results saved to: {args.save}\n")