# Deployment Guide - FYNIX Deal Finder

This guide will help you deploy the FYNIX Deal Finder web application with Google Sheets integration.

## 📋 Prerequisites

1. **Zillow API Key** from RapidAPI
2. **Google Cloud Project** with Sheets API enabled
3. **Deployment Platform** account (Render, Railway, or Heroku)

---

## 🔧 Setup Steps

### Step 1: Google Sheets API Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com

2. **Create a New Project** (or use existing)
   - Click "Select a project" → "New Project"
   - Name it "FYNIX Deal Finder"
   - Click "Create"

3. **Enable Google Sheets API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
   - Also enable "Google Drive API"

4. **Create Service Account**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Name: `fynix-deal-finder`
   - Click "Create and Continue"
   - Skip optional steps, click "Done"

5. **Create Service Account Key**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON" format
   - Click "Create"
   - Save the downloaded file as `google_credentials.json`

6. **Share Your Google Sheet**
   - Create a new Google Sheet or use existing
   - Click "Share" button
   - Paste the service account email (from the JSON file: `client_email`)
   - Give "Editor" access
   - Copy the spreadsheet ID from the URL:
     ```
     https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
     ```

### Step 2: Local Testing

1. **Clone and Setup**
   ```bash
   cd re_onmarket
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**

   Create/update `.env` file:
   ```env
   ZILLOW_API_KEY=your_zillow_api_key_here
   GOOGLE_SHEET_ID=your_google_sheet_id_here
   ```

3. **Add Google Credentials**
   - Place `google_credentials.json` in the project root
   - Make sure it's in `.gitignore` (already configured)

4. **Test Locally**
   ```bash
   python app.py
   ```
   - Visit: http://localhost:5000
   - Try a search (e.g., "Mableton, GA")
   - Check if results appear and save to Google Sheets

---

## 🚀 Deployment Options

### Option A: Deploy to Render (Recommended - Free Tier Available)

1. **Create Render Account**: https://render.com

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Or use "Deploy from GitHub" and select your repo

3. **Configure Service**
   ```
   Name: fynix-deal-finder
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

4. **Add Environment Variables**
   - Go to "Environment" tab
   - Add:
     ```
     ZILLOW_API_KEY = your_zillow_api_key
     GOOGLE_SHEET_ID = your_google_sheet_id
     ```

5. **Add Google Credentials**
   - In Render dashboard, go to "Environment" → "Secret Files"
   - Add file: `google_credentials.json`
   - Paste the entire contents of your credentials file

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your app will be live at: `https://your-app-name.onrender.com`

---

### Option B: Deploy to Railway

1. **Create Railway Account**: https://railway.app

2. **New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure**
   - Railway auto-detects Python
   - Go to "Variables" tab

4. **Add Environment Variables**
   ```
   ZILLOW_API_KEY = your_zillow_api_key
   GOOGLE_SHEET_ID = your_google_sheet_id
   ```

5. **Add Google Credentials**
   - Upload `google_credentials.json` to the project root via GitHub
   - Or add as environment variable:
     ```
     GOOGLE_CREDENTIALS = {paste entire JSON contents}
     ```
   - Update `app.py` to read from env var if file doesn't exist

6. **Deploy**
   - Railway automatically deploys
   - Get your URL from the dashboard

---

### Option C: Deploy to Heroku

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Login and Create App**
   ```bash
   heroku login
   heroku create fynix-deal-finder
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set ZILLOW_API_KEY=your_key
   heroku config:set GOOGLE_SHEET_ID=your_sheet_id
   ```

4. **Add Credentials as Config Var**
   ```bash
   # Option 1: Upload file
   heroku buildpacks:add heroku/python
   git add google_credentials.json

   # Option 2: As environment variable
   heroku config:set GOOGLE_CREDENTIALS="$(cat google_credentials.json)"
   ```

5. **Create Procfile**
   Already created in your project:
   ```
   web: gunicorn app:app
   ```

6. **Deploy**
   ```bash
   git push heroku main
   heroku open
   ```

---

## 🔒 Security Best Practices

### Never Commit Sensitive Files
The `.gitignore` already includes:
```
.env
google_credentials.json
*.json (except package.json)
```

### Use Environment Variables
For production, always use environment variables instead of files when possible.

### Update app.py for Env Var Credentials (Optional)
If you want to use credentials from environment variable instead of file:

```python
import json
import os

def get_google_sheets_client():
    try:
        # Try to load from file first
        if os.path.exists('google_credentials.json'):
            creds = Credentials.from_service_account_file(
                'google_credentials.json',
                scopes=SCOPES
            )
        # Fallback to environment variable
        elif os.getenv('GOOGLE_CREDENTIALS'):
            creds_json = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
            creds = Credentials.from_service_account_info(
                creds_json,
                scopes=SCOPES
            )
        else:
            raise ValueError("No Google credentials found")

        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error: {e}")
        return None
```

---

## 📊 Using the Application

### Web Interface
1. Visit your deployed URL
2. Fill out the form:
   - **Location**: City, state, or ZIP (e.g., "Mableton, GA")
   - **Price Range**: Optional min/max filters
   - **Bedrooms/Bathrooms**: Optional filters
   - **Screen Count**: How many properties to initially review (default: 20)
   - **Analyze Count**: How many to deeply analyze (default: 10)
   - **Min Score**: Only deep dive on deals scoring this or higher (default: 6)
   - **Save to Google Sheets**: Check to auto-save results

3. Click "Find Investment Deals"
4. Wait 1-2 minutes for results
5. View results on the page
6. Click "View Results in Google Sheets" to see full spreadsheet

### API Endpoint
You can also call the API programmatically:

```bash
curl -X POST https://your-app.onrender.com/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Mableton, GA",
    "max_price": 200000,
    "beds_min": 3,
    "screen_count": 10,
    "analyze_count": 5,
    "save_to_sheets": true
  }'
```

### Google Sheets Integration
Results are automatically saved to your configured Google Sheet with:
- Property address, price, beds/baths, sqft
- Zestimate (ARV), MAO (70% Rule), profit potential, ROI
- Deal score and recommendation
- Rental analysis (cash flow, ROI, cap rate)
- Price trend analysis

Each search creates a new worksheet with timestamp.

---

## 🔍 Monitoring

### Health Check Endpoint
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T12:00:00",
  "zillow_api_configured": true,
  "google_sheets_configured": true
}
```

### Logs
- **Render**: View logs in dashboard
- **Railway**: Click on deployment → "View Logs"
- **Heroku**: `heroku logs --tail`

---

## 🐛 Troubleshooting

### "API connection failed"
- Check `ZILLOW_API_KEY` environment variable
- Verify API key is active on RapidAPI
- Check API quota/limits

### "Could not connect to Google Sheets"
- Verify `google_credentials.json` is present
- Check if `GOOGLE_SHEET_ID` is set correctly
- Ensure service account has access to the sheet
- Verify Google Sheets API is enabled in Cloud Console

### "Module not found" errors
- Ensure `requirements.txt` is complete
- Check build logs for installation errors
- Try rebuilding the deployment

### Slow performance
- Reduce `screen_count` and `analyze_count` parameters
- Check Zillow API rate limits
- Consider upgrading to paid hosting tier

---

## 💰 Cost Estimates

### Free Tier Limits
- **Render**: 750 hours/month free
- **Railway**: $5 free credit/month
- **Heroku**: Dynos sleep after 30 min inactivity (free tier deprecated)

### API Costs
- **Zillow API**: Check RapidAPI pricing (typically free tier: 100-500 calls/month)
- **Google Sheets API**: Free (unlimited for service accounts)

### Recommended Setup
- Start with Render free tier
- Monitor API usage
- Upgrade as needed

---

## 📝 Next Steps

1. ✅ Set up Google Cloud credentials
2. ✅ Configure environment variables
3. ✅ Test locally
4. ✅ Deploy to hosting platform
5. ✅ Share the URL with your team
6. 📊 Start finding deals!

---

## 🆘 Support

For issues:
1. Check deployment logs
2. Verify all environment variables are set
3. Test API connection via `/health` endpoint
4. Review this guide's troubleshooting section

Happy deal hunting! 🏠💰
