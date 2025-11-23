"""
Quick test script for FYNIX Property Analyzer
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from zillow_analyzer import ZillowPropertyAnalyzer, print_analysis
import json


def test_single_property():
    """Test analyzing a single property"""
    print("\n" + "="*80)
    print("TEST 1: Single Property Analysis")
    print("="*80)
    
    analyzer = ZillowPropertyAnalyzer()
    
    # Test property
    result = analyzer.analyze_property(
        address="1875 AVONDALE Circle",
        city="Jacksonville",
        state="FL",
        zipcode="32205"
    )
    
    print_analysis(result)
    
    # Save to file for inspection
    with open('test_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("💾 Full result saved to: test_result.json\n")


def test_multiple_properties():
    """Test analyzing multiple properties"""
    print("\n" + "="*80)
    print("TEST 2: Batch Property Analysis")
    print("="*80 + "\n")
    
    analyzer = ZillowPropertyAnalyzer()
    
    properties = [
        {
            "address": "1875 AVONDALE Circle",
            "city": "Jacksonville",
            "state": "FL",
            "zipcode": "32205"
        },
        {
            "address": "123 Main St",
            "city": "Atlanta",
            "state": "GA",
            "zipcode": "30308"
        },
        # Add more test properties here
    ]
    
    results = []
    for prop in properties:
        print(f"\nAnalyzing: {prop['address']}, {prop['city']}, {prop['state']}")
        result = analyzer.analyze_property(**prop)
        
        if result.get('success'):
            results.append(result)
            score = result['deal_quality']['score']
            label = result['deal_quality']['label']
            print(f"✅ Score: {score}/10 - {label}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    
    # Sort by score
    results.sort(key=lambda x: x['deal_quality']['score'], reverse=True)
    
    print("\n" + "="*80)
    print("SUMMARY - RANKED BY DEAL QUALITY")
    print("="*80 + "\n")
    
    for i, result in enumerate(results, 1):
        prop = result['property']
        deal = result['deal_quality']
        inv = result['investor_analysis']
        
        print(f"{i}. {prop['address']}")
        print(f"   Score: {deal['score']}/10 - {deal['label']}")
        print(f"   List: ${prop['list_price']:,} | MAO: ${inv['mao_70_percent']:,}")
        print(f"   Profit: ${inv['profit_potential']:,} ({inv['roi_percentage']}% ROI)\n")


def test_api_connection():
    """Test basic API connectivity"""
    print("\n" + "="*80)
    print("TEST 3: API Connection Test")
    print("="*80 + "\n")
    
    try:
        analyzer = ZillowPropertyAnalyzer()
        print("✅ API Key loaded successfully")
        print(f"🔑 Key: {analyzer.api_key[:10]}...{analyzer.api_key[-10:]}")
        print(f"🌐 Host: {analyzer.api_host}\n")
        
        # Try a simple request
        result = analyzer.get_property_data(
            address="1875 AVONDALE Circle",
            city="Jacksonville",
            state="FL",
            zipcode="32205"
        )
        
        if result:
            print("✅ API connection successful!")
            print(f"📦 Received {len(json.dumps(result))} bytes of data\n")
        else:
            print("❌ API connection failed\n")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "single":
            test_single_property()
        elif test_name == "batch":
            test_multiple_properties()
        elif test_name == "api":
            test_api_connection()
        else:
            print("Usage: python test_analyzer.py [single|batch|api]")
    else:
        # Run all tests
        test_api_connection()
        test_single_property()
        # test_multiple_properties()  # Uncomment when ready