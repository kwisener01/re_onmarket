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
    
    def calculate_rehab_estimate(self, year_built: int, sqft: int) -> Dict:
        """Estimate rehab costs based on property age"""
        current_year = datetime.now().year
        property_age = current_year - year_built
        
        light = sqft * 25
        medium = sqft * 40
        heavy = sqft * 60
        
        if property_age <= 20:
            recommended = light
            scope = "Light"
            description = "Cosmetic: paint, flooring, fixtures"
        elif property_age <= 50:
            recommended = medium
            scope = "Medium"
            description = "Kitchen, baths, HVAC, roof"
        else:
            recommended = heavy
            scope = "Heavy"
            description = "Full renovation"
        
        return {
            "light": light,
            "medium": medium,
            "heavy": heavy,
            "recommended": recommended,
            "scope": scope,
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
    
    def analyze_property(self, address: str, city: str, state: str, zipcode: str) -> Dict:
        """
        Complete property analysis
        
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
            
            # Extract fields (adjust based on actual response)
            beds = prop.get('bedrooms', prop.get('beds', 0))
            baths = prop.get('bathrooms', prop.get('baths', 0))
            sqft = prop.get('livingArea', prop.get('sqft', prop.get('squareFeet', 0)))
            year_built = prop.get('yearBuilt', prop.get('year_built', 2000))
            list_price = prop.get('price', prop.get('listPrice', 0))
            zestimate = prop.get('zestimate', prop.get('estimate', list_price))
            
            # Conservative ARV (95% of Zestimate)
            arv_conservative = zestimate * 0.95
            
            # Calculate rehab
            rehab = self.calculate_rehab_estimate(year_built, sqft)
            
            # Calculate MAO
            mao_70 = (arv_conservative * 0.70) - rehab['recommended']
            mao_65 = (arv_conservative * 0.65) - rehab['recommended']
            mao_75 = (arv_conservative * 0.75) - rehab['recommended']
            
            # Calculate profit
            profit_at_mao = (arv_conservative * 0.70) - list_price
            roi = (profit_at_mao / list_price * 100) if list_price > 0 else 0
            
            # Score deal
            deal_score = self.calculate_deal_score(list_price, arv_conservative, rehab['property_age'])
            
            # Build response
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
                "rehab": {
                    "recommended": round(rehab['recommended'], 0),
                    "scope": rehab['scope'],
                    "description": rehab['description'],
                    "per_sqft": round(rehab['recommended'] / sqft, 2) if sqft > 0 else 0
                },
                "investor_analysis": {
                    "mao_70_percent": round(mao_70, 0),
                    "mao_65_percent": round(mao_65, 0),
                    "mao_75_percent": round(mao_75, 0),
                    "recommended_max_offer": round(mao_70, 0),
                    "profit_potential": round(profit_at_mao, 0),
                    "roi_percentage": round(roi, 1)
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