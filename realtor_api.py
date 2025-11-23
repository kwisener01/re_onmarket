"""
Realtor.com API Integration
Fetches property descriptions and additional data from Realtor.com
"""

import http.client
import json
import os
import urllib.parse
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()


class RealtorAPI:
    """Realtor.com API client for property data"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('REALTOR_API_KEY') or os.getenv('ZILLOW_API_KEY')
        self.api_host = "realtor-com4.p.rapidapi.com"

    def search_properties(self, location: str, limit: int = 20) -> Optional[List[Dict]]:
        """
        Search for properties on Realtor.com by location
        Returns list of properties
        """
        if not self.api_key:
            print("⚠️  Realtor API key not configured")
            return None

        try:
            conn = http.client.HTTPSConnection(self.api_host)

            # Format location for URL
            encoded_location = urllib.parse.quote(location)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            # Use list endpoint
            endpoint = f"/properties/list_v2?location={encoded_location}&limit={limit}"

            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 200:
                response = json.loads(data.decode("utf-8"))
                return response.get('data', {}).get('results', [])
            else:
                print(f"⚠️  Realtor API error: {res.status}")
                return None

        except Exception as e:
            print(f"⚠️  Realtor API exception: {str(e)}")
            return None
        finally:
            conn.close()

    def search_property(self, address: str, city: str, state: str, zipcode: str) -> Optional[Dict]:
        """
        Search for a specific property on Realtor.com
        Returns property data including description
        """
        # Search by full address
        full_address = f"{address}, {city}, {state} {zipcode}"
        properties = self.search_properties(full_address, limit=5)

        if not properties:
            return None

        # Try to find exact match
        address_lower = address.lower()
        for prop in properties:
            prop_address = prop.get('location', {}).get('address', {}).get('line', '')
            if prop_address and address_lower in prop_address.lower():
                return prop

        # Return first result as fallback
        return properties[0] if properties else None

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
            'listing_remarks',
            'property_description'
        ]

        # Check top level
        for field in description_fields:
            if field in property_data and property_data[field]:
                return str(property_data[field])

        # Check nested in description object
        if 'description' in property_data and isinstance(property_data['description'], dict):
            desc = property_data['description']
            for field in ['text', 'value', 'remarks']:
                if field in desc and desc[field]:
                    return str(desc[field])

        # Check nested in listing
        if 'listing' in property_data and isinstance(property_data['listing'], dict):
            listing = property_data['listing']
            for field in description_fields:
                if field in listing and listing[field]:
                    return str(listing[field])

        return None
