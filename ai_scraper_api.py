"""
AI Web Scraper API Integration
Uses AI to extract content from property listing URLs
Can scrape Zillow, Realtor.com, or Redfin pages directly
"""

import http.client
import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class AIScraperAPI:
    """AI Web Scraper API client for extracting property data from listing pages"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY') or os.getenv('ZILLOW_API_KEY')
        self.api_host = "ai-web-scraper1.p.rapidapi.com"

    def scrape_url(self, url: str, summary: bool = False) -> Optional[Dict]:
        """
        Scrape a URL and extract content using AI

        Args:
            url: The URL to scrape
            summary: Whether to return a summary (True) or full content (False)

        Returns:
            Scraped content as dictionary or None
        """
        if not self.api_key:
            print("⚠️  AI Scraper API key not configured")
            return None

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            payload = json.dumps({
                "url": url,
                "summary": summary
            })

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host,
                'Content-Type': 'application/json'
            }

            conn.request("POST", "/", payload, headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                print(f"⚠️  AI Scraper API error: {res.status}")
                return None

        except Exception as e:
            print(f"⚠️  AI Scraper API exception: {str(e)}")
            return None
        finally:
            conn.close()

    def scrape_property_page(self, property_url: str) -> Optional[str]:
        """
        Scrape a property listing page and extract the description

        Args:
            property_url: URL to Zillow, Realtor.com, or Redfin property page

        Returns:
            Property description text or None
        """
        print(f"   🔄 Scraping property page with AI: {property_url}")

        scraped_data = self.scrape_url(property_url, summary=False)

        if not scraped_data:
            return None

        # Extract text content from scraped data
        # The AI scraper returns various fields depending on the response format
        content_fields = [
            'content',
            'text',
            'data',
            'extracted_content',
            'body',
            'description'
        ]

        for field in content_fields:
            if field in scraped_data and scraped_data[field]:
                content = str(scraped_data[field])
                print(f"   ✅ Successfully scraped {len(content)} characters from page")
                return content

        # If we got a response but no recognized field, return the whole thing as string
        if scraped_data:
            content = str(scraped_data)
            print(f"   ✅ Scraped data (unknown format): {len(content)} characters")
            return content

        return None

    def get_property_description(self, zillow_url: str = None, realtor_url: str = None,
                                redfin_url: str = None) -> Optional[str]:
        """
        Try to scrape property description from any available URL
        Tries in order: Realtor.com, Zillow, Redfin

        Args:
            zillow_url: Zillow property URL
            realtor_url: Realtor.com property URL
            redfin_url: Redfin property URL

        Returns:
            Property description or None
        """
        # Try Realtor.com first (usually has best descriptions)
        if realtor_url:
            description = self.scrape_property_page(realtor_url)
            if description:
                return description

        # Try Zillow second
        if zillow_url:
            description = self.scrape_property_page(zillow_url)
            if description:
                return description

        # Try Redfin last
        if redfin_url:
            description = self.scrape_property_page(redfin_url)
            if description:
                return description

        return None
