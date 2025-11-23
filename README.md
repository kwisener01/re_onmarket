# Real Estate Deal Finder

A Python-based real estate investment analysis tool that uses the Zillow API to find and analyze investment properties.

## Setup

### 1. Install Dependencies

```bash
pip install python-dotenv
```

### 2. Get Your Zillow API Key

1. Go to [RapidAPI - Zillow API](https://rapidapi.com/apimaker/api/zillow-com1)
2. Sign up or log in to RapidAPI
3. Subscribe to the Zillow API (free tier available)
4. Copy your API key from the dashboard

### 3. Configure Environment Variables

1. Open the `.env` file in the project root
2. Add your API key:

```env
ZILLOW_API_KEY=your_actual_api_key_here
```

**Important:** Never commit your `.env` file to git! It's already in `.gitignore`.

## Usage

### Test API Connection

```bash
python test_analyzer.py api
```

### Analyze a Single Property

```bash
python test_analyzer.py single
```

### Find Investment Deals

```bash
python deal_finder.py
```

## Scripts Overview

- `deal_finder.py` - Main orchestrator for finding investment deals
- `search_properties.py` - Search for properties by location or AI prompt
- `zillow_analyzer.py` - Analyze property value and investment potential
- `rental_analyzer.py` - Calculate rental investment metrics
- `price_history.py` - Analyze price trends over time
- `test_analyzer.py` - Test and validate the analysis tools

## Features

- Property search by location and criteria
- Fix-and-flip deal analysis (70% Rule)
- Rental investment analysis (cash flow, ROI, cap rate)
- Price history and trend analysis
- Deal quality scoring and ranking
- Optimized API usage to minimize costs

## API Information

This project uses the **Zillow API** via RapidAPI:
- Host: `zillow-working-api.p.rapidapi.com`
- Required header: `x-rapidapi-key`

Make sure you have an active subscription to use the API.
