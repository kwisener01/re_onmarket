"""
Realtor.com API Integration
Fetches property descriptions and additional data from Realtor.com
"""

import http.client
import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class RealtorAPI:
    """Realtor.com API client for property data"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('REALTOR_API_KEY')
        self.api_host = "realtor.p.rapidapi.com"

    def search_property(self, address: str, city: str, state: str, zipcode: str) -> Optional[Dict]:
        """
        Search for property on Realtor.com
        Returns property data including description
        """
        if not self.api_key:
            print("⚠️  Realtor API key not configured")
            return None

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            # Format search query
            query = f"{address}, {city}, {state} {zipcode}"

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            # Use property detail endpoint
            endpoint = f"/properties/v3/detail?property_id={query}"

            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                print(f"⚠️  Realtor API error: {res.status}")
                return None

        except Exception as e:
            print(f"⚠️  Realtor API exception: {str(e)}")
            return None
        finally:
            conn.close()

    def get_property_description(self, address: str, city: str, state: str, zipcode: str) -> Optional[str]:
        """
        Get property description from Realtor.com
        Returns description text or None
        """
        property_data = self.search_property(address, city, state, zipcode)

        if not property_data:
            return None

        # Try to extract description from various possible fields
        description_fields = [
            'description',
            'public_remarks',
            'remarks',
            'listing_description',
            'property_description'
        ]

        # Check top level
        for field in description_fields:
            if field in property_data and property_data[field]:
                return str(property_data[field])

        # Check nested in listing
        if 'listing' in property_data and isinstance(property_data['listing'], dict):
            for field in description_fields:
                if field in property_data['listing'] and property_data['listing'][field]:
                    return str(property_data['listing'][field])

        # Check nested in data
        if 'data' in property_data and isinstance(property_data['data'], dict):
            for field in description_fields:
                if field in property_data['data'] and property_data['data'][field]:
                    return str(property_data['data'][field])

        return None
