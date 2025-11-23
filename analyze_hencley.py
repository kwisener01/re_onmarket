"""
Analyze property at 2598 Hencley Cir SW, Marietta, GA 30008
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from zillow_analyzer import ZillowPropertyAnalyzer, print_analysis
import json

# Analyze the Marietta property
analyzer = ZillowPropertyAnalyzer()

result = analyzer.analyze_property(
    address="2598 Hencley Cir SW",
    city="Marietta",
    state="GA",
    zipcode="30008"
)

print_analysis(result)

# Save to file
with open('hencley_analysis.json', 'w') as f:
    json.dump(result, f, indent=2)

print("\n💾 Full result saved to: hencley_analysis.json\n")
