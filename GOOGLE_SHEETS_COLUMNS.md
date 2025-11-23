# Google Sheets Column Structure

## Overview
The application writes 33 columns to the "All Properties" worksheet in your Google Sheet.

## Column Layout

### Basic Information (Columns 1-7)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| A | Date Pulled | Timestamp when property was analyzed | 2025-01-15 14:30 |
| B | Search Location | Location searched | Mableton, GA |
| C | Rank | Property ranking in search results | 1, 2, 3... |
| D | Address | Street address | 123 Main St |
| E | City | City name | Mableton |
| F | State | State abbreviation | GA |
| G | ZIP | ZIP code | 30126 |

### Zillow Link (Column 8)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| H | Zillow URL | Clickable link to property on Zillow | https://www.zillow.com/homedetails/12345_zpid/ |

### Property Details (Columns 9-14)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| I | List Price | Current listing price | 250000 |
| J | Beds | Number of bedrooms | 3 |
| K | Baths | Number of bathrooms | 2 |
| L | Sqft | Square footage | 1500 |
| M | Price/Sqft | Price per square foot | 167 |
| N | Zestimate (ARV) | Zillow's estimated value (After Repair Value) | 280000 |

### Fix & Flip Analysis - All Scenarios (Columns 15-22)
| Column | Header | Description | Formula |
|--------|--------|-------------|---------|
| O | MAO Light ($25/sqft) | Max Allowable Offer with light rehab | (ARV × 0.70) - (Sqft × $25) |
| P | MAO Medium ($40/sqft) | Max Allowable Offer with medium rehab | (ARV × 0.70) - (Sqft × $40) |
| Q | MAO Heavy ($60/sqft) | Max Allowable Offer with heavy rehab | (ARV × 0.70) - (Sqft × $60) |
| R | Profit Light | Potential profit with light rehab | MAO Light - List Price |
| S | Profit Medium | Potential profit with medium rehab | MAO Medium - List Price |
| T | Profit Heavy | Potential profit with heavy rehab | MAO Heavy - List Price |
| U | Best Scenario | Which scenario gives best profit | "Works with Light Rehab" |
| V | Best Profit | Highest profit amount from all scenarios | 45000 |

### Fixer-Upper Detection (Columns 23-24)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| W | Is Fixer? | Property matches fixer keywords | YES / NO |
| X | Keywords Found | List of detected keywords | fixer, TLC, as-is |

### Deal Quality (Columns 25-27)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| Y | Deal Score | Numerical score 1-10 | 8 |
| Z | Deal Grade | Letter grade | Excellent Deal |
| AA | Recommendation | Action recommendation | Strong Buy - Analyze Further |

### Rental Analysis (Columns 28-31)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| AB | Monthly Rent | Estimated monthly rent | 1800 |
| AC | Cash Flow | Monthly cash flow after expenses | 350 |
| AD | Cash-on-Cash % | Cash on cash return percentage | 12.5 |
| AE | Cap Rate % | Capitalization rate | 8.2 |

### Price Trends (Columns 32-33)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| AF | Price Trend | Overall price trend | increasing |
| AG | 1-Year Change % | Price change over last year | 5.3 |

## How Headers are Managed

### Automatic Header Addition
When you run a search:
1. **If sheet is empty** → Headers are automatically added and formatted
2. **If headers exist** → New properties are appended below existing data

### Duplicate Prevention
- Properties are tracked by address
- If a property was pulled within the last **30 days**, it will be skipped
- Older than 30 days → Property will be re-analyzed with fresh data

### Manual Reset
If you delete all data and want to start fresh:
1. Delete all rows in the sheet (including headers)
2. Run a new search
3. Headers will be automatically added

Alternatively, you can run the `init_sheet_headers.py` script on Render:
```bash
python init_sheet_headers.py
```

## Data Alignment Verification

The code ensures perfect alignment between headers and data:
- **Headers defined**: `app.py` lines 106-118
- **Data rows built**: `app.py` lines 166-210
- **All 33 columns match** in exact order

## Key Features

✅ **Clickable Zillow Links** - Direct links to properties (Column H)
✅ **All Rehab Scenarios** - See Light/Medium/Heavy analysis for every property
✅ **Keyword Detection** - Automatically identifies fixer-uppers
✅ **Duplicate Prevention** - Skip properties pulled within 30 days
✅ **Timestamp Tracking** - Know when each property was analyzed
✅ **Best Scenario Highlighting** - See which rehab level gives best profit

## Fixer Keyword Detection

The system scans property descriptions for 20+ keywords. If **ANY** keyword is found:
- **"Is Fixer?"** column shows **YES**
- **"Keywords Found"** column lists all matching keywords (e.g., "fixer, TLC, as-is")

Keywords detected:
- **Direct:** fixer, fixer-upper, handyman special, handyman's special
- **Condition:** TLC, needs work, as-is, as is, rehab, renovation
- **Sales type:** cash only, foreclosure, short sale, estate sale
- **Marketing:** investor special, investor opportunity, motivated seller, must sell
- **Distress:** bring all offers, priced to sell, reduced, price reduction
