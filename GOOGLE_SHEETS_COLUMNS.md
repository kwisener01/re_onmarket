# Google Sheets Column Structure

## Overview
The application writes 32 columns to the "All Properties" worksheet in your Google Sheet.

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

### Property Details (Columns 8-13)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| H | List Price | Current listing price | 250000 |
| I | Beds | Number of bedrooms | 3 |
| J | Baths | Number of bathrooms | 2 |
| K | Sqft | Square footage | 1500 |
| L | Price/Sqft | Price per square foot | 167 |
| M | Zestimate (ARV) | Zillow's estimated value (After Repair Value) | 280000 |

### Fix & Flip Analysis - All Scenarios (Columns 14-21)
| Column | Header | Description | Formula |
|--------|--------|-------------|---------|
| N | MAO Light ($25/sqft) | Max Allowable Offer with light rehab | (ARV × 0.70) - (Sqft × $25) |
| O | MAO Medium ($40/sqft) | Max Allowable Offer with medium rehab | (ARV × 0.70) - (Sqft × $40) |
| P | MAO Heavy ($60/sqft) | Max Allowable Offer with heavy rehab | (ARV × 0.70) - (Sqft × $60) |
| Q | Profit Light | Potential profit with light rehab | MAO Light - List Price |
| R | Profit Medium | Potential profit with medium rehab | MAO Medium - List Price |
| S | Profit Heavy | Potential profit with heavy rehab | MAO Heavy - List Price |
| T | Best Scenario | Which scenario gives best profit | "Works with Light Rehab" |
| U | Best Profit | Highest profit amount from all scenarios | 45000 |

### Fixer-Upper Detection (Columns 22-23)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| V | Is Fixer? | Property matches fixer keywords | YES / NO |
| W | Keywords Found | List of detected keywords | fixer, TLC, as-is |

### Deal Quality (Columns 24-26)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| X | Deal Score | Numerical score 1-10 | 8 |
| Y | Deal Grade | Letter grade | Excellent Deal |
| Z | Recommendation | Action recommendation | Strong Buy - Analyze Further |

### Rental Analysis (Columns 27-30)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| AA | Monthly Rent | Estimated monthly rent | 1800 |
| AB | Cash Flow | Monthly cash flow after expenses | 350 |
| AC | Cash-on-Cash % | Cash on cash return percentage | 12.5 |
| AD | Cap Rate % | Capitalization rate | 8.2 |

### Price Trends (Columns 31-32)
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| AE | Price Trend | Overall price trend | increasing |
| AF | 1-Year Change % | Price change over last year | 5.3 |

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
- **Headers defined**: `app.py` lines 106-117
- **Data rows built**: `app.py` lines 165-205
- **All 32 columns match** in exact order

## Key Features

✅ **All Rehab Scenarios** - See Light/Medium/Heavy analysis for every property
✅ **Keyword Detection** - Automatically identifies fixer-uppers
✅ **Duplicate Prevention** - Skip properties pulled within 30 days
✅ **Timestamp Tracking** - Know when each property was analyzed
✅ **Best Scenario Highlighting** - See which rehab level gives best profit
