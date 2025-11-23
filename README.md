# FYNIX Real Estate Deal Finder

A Python-based real estate investment analysis tool with **web interface** and **Google Sheets integration**. Uses the Zillow API to find and analyze investment properties.

## 🚀 Two Ways to Use

1. **Web Application** - Beautiful form interface with Google Sheets export (recommended)
2. **Command Line** - Direct Python scripts for automation

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

### Option 1: Web Application (Recommended)

**Local Development:**
```bash
pip install -r requirements.txt
python app.py
```
Visit: http://localhost:5000

**Deploy to Production:**
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide to Render, Railway, or Heroku.

**Features:**
- 🎨 Beautiful web form interface
- 📊 Automatic Google Sheets export
- 📈 Real-time results display
- 🔄 API endpoint for integrations

### Option 2: Command Line

**Test API Connection:**
```bash
python test_analyzer.py api
```

**Analyze a Single Property:**
```bash
python test_analyzer.py single
```

**Find Investment Deals:**
```bash
python deal_finder.py --location "Mableton, GA" --max 200000 --beds 3
```

## Files Overview

**Web Application:**
- `app.py` - Flask web server with Google Sheets integration
- `templates/index.html` - Beautiful web form interface

**Core Scripts:**
- `deal_finder.py` - Main orchestrator for finding investment deals
- `search_properties.py` - Search for properties by location or AI prompt
- `zillow_analyzer.py` - Analyze property value and investment potential
- `rental_analyzer.py` - Calculate rental investment metrics
- `price_history.py` - Analyze price trends over time
- `test_analyzer.py` - Test and validate the analysis tools

**Configuration:**
- `requirements.txt` - Python dependencies
- `Procfile` - Deployment configuration
- `.env` - Your API keys (keep private!)
- `google_credentials.json` - Google Sheets credentials (keep private!)

## Features

**Analysis:**
- 🔍 Property search by location and criteria
- 💰 Fix-and-flip deal analysis (70% Rule)
- 🏠 Rental investment analysis (cash flow, ROI, cap rate)
- 📈 Price history and trend analysis
- ⭐ Deal quality scoring (1-10 scale)
- 🎯 Optimized API usage to minimize costs

**Web Interface:**
- 🌐 Beautiful, responsive web form
- 📊 Automatic Google Sheets export
- 📱 Mobile-friendly design
- 🚀 One-click deployment
- 🔗 API endpoint for integrations

## API Information

This project uses the **Zillow API** via RapidAPI:
- Host: `zillow-working-api.p.rapidapi.com`
- Required header: `x-rapidapi-key`

Make sure you have an active subscription to use the API.

## 📊 Google Sheets Integration

Results are automatically exported to Google Sheets with:
- Property details (address, price, beds/baths, sqft)
- Investment metrics (ARV, MAO, profit potential, ROI)
- Deal scores and recommendations
- Rental analysis (cash flow, cap rate)
- Price trends and signals

See [DEPLOYMENT.md](DEPLOYMENT.md) for setup instructions.

## 🚀 Quick Start

1. **Get API Key**: [RapidAPI - Zillow](https://rapidapi.com/apimaker/api/zillow-com1)
2. **Configure**: Add to `.env` file
3. **Run Web App**: `python app.py`
4. **Start Searching**: Visit http://localhost:5000

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)

## 📖 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Complete guide for deploying to Render, Railway, or Heroku
- Command line examples in each script file

## 🆘 Support

Check `/health` endpoint to verify configuration:
```
http://localhost:5000/health
```

Returns API and Google Sheets connection status.
