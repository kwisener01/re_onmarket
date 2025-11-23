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
        self.api_host_open = "realtor-com-open.p.rapidapi.com"  # Alternative API endpoint

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

    def get_property_detail_open(self, property_id: str) -> Optional[Dict]:
        """
        Get detailed property information from Realtor.com (Open API)
        Alternative endpoint with potentially better data coverage
        Returns full property details including description
        """
        if not self.api_key:
            print("⚠️  Realtor API key not configured")
            return None

        try:
            conn = http.client.HTTPSConnection(self.api_host_open)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host_open
            }

            # Use details endpoint (note: "details" not "detail")
            endpoint = f"/property/details?property_id={property_id}"

            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                print(f"⚠️  Realtor Open API error: {res.status}")
                return None

        except Exception as e:
            print(f"⚠️  Realtor Open API exception: {str(e)}")
            return None
        finally:
            conn.close()

    def get_property_detail(self, property_id: str) -> Optional[Dict]:
        """
        Get detailed property information from Realtor.com
        Tries both API endpoints for maximum coverage
        Returns full property details including description
        """
        if not self.api_key:
            print("⚠️  Realtor API key not configured")
            return None

        # Try the Open API first (seems to have better data)
        result = self.get_property_detail_open(property_id)
        if result:
            return result

        # Fallback to the v4 API
        try:
            conn = http.client.HTTPSConnection(self.api_host)

            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host
            }

            # Use detail endpoint
            endpoint = f"/properties/detail?property_id={property_id}"

            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                print(f"⚠️  Realtor detail API error: {res.status}")
                return None

        except Exception as e:
            print(f"⚠️  Realtor detail API exception: {str(e)}")
            return None
        finally:
            conn.close()

    def search_property(self, address: str, city: str, state: str, zipcode: str) -> Optional[Dict]:
        """
        Search for a specific property on Realtor.com
        First searches by address, then gets full details
        Returns property data including description
        """
        # Search by full address
        full_address = f"{address}, {city}, {state} {zipcode}"
        properties = self.search_properties(full_address, limit=5)

        if not properties:
            return None

        # Try to find exact match
        address_lower = address.lower()
        matched_prop = None

        for prop in properties:
            prop_address = prop.get('location', {}).get('address', {}).get('line', '')
            if prop_address and address_lower in prop_address.lower():
                matched_prop = prop
                break

        # Use first result as fallback
        if not matched_prop and properties:
            matched_prop = properties[0]

        if not matched_prop:
            return None

        # Get property_id and fetch full details
        property_id = matched_prop.get('property_id')
        if property_id:
            # Fetch full details which should include description
            detail = self.get_property_detail(property_id)
            if detail:
                return detail

        # Fallback to search result if detail fetch failed
        return matched_prop

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
            'property_description',
            'publicRemarks',
            'agentRemarks',
            'mlsDescription'
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

        # Check nested in data object (Open API format)
        if 'data' in property_data and isinstance(property_data['data'], dict):
            data_obj = property_data['data']
            for field in description_fields:
                if field in data_obj and data_obj[field]:
                    return str(data_obj[field])

            # Check data.listing
            if 'listing' in data_obj and isinstance(data_obj['listing'], dict):
                listing = data_obj['listing']
                for field in description_fields:
                    if field in listing and listing[field]:
                        return str(listing[field])

        return None
