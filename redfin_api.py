"""
Redfin API Integration
Fetches property descriptions from Redfin's unofficial API
No API key required - uses public endpoints
"""

import http.client
import json
import urllib.parse
from typing import Dict, Optional


class RedfinAPI:
    """Redfin API client for property data"""

    def __init__(self):
        self.api_host = "redfin.com"

    def search_property(self, address: str, city: str, state: str, zipcode: str) -> Optional[Dict]:
        """
        Search for property on Redfin
        Returns property data including description
        """
        try:
            conn = http.client.HTTPSConnection(self.api_host)

            # Format search query
            query = f"{address}, {city}, {state} {zipcode}"
            encoded_query = urllib.parse.quote(query)

            # First, search for the property to get the URL
            search_endpoint = f"/stingray/do/location-autocomplete?location={encoded_query}&v=2"

            # Complete browser-like headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.redfin.com/',
                'Origin': 'https://www.redfin.com',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }

            conn.request("GET", search_endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()

            if res.status != 200:
                if res.status == 403:
                    print(f"⚠️  Redfin blocked request (403). They may be rate-limiting or detecting automation. Using Realtor.com instead is recommended.")
                else:
                    print(f"⚠️  Redfin search error: {res.status}")
                return None

            # Parse response (Redfin returns JSON with a prefix to strip)
            text = data.decode("utf-8")
            if text.startswith("{}&&"):
                text = text[4:]

            search_results = json.loads(text)

            # Get first result
            if not search_results or 'payload' not in search_results:
                return None

            payload = search_results['payload']
            if not payload or 'sections' not in payload:
                return None

            # Find property in results
            property_id = None
            for section in payload['sections']:
                if 'rows' in section:
                    for row in section['rows']:
                        if row.get('type') == 'address':
                            property_id = row.get('id')
                            break
                if property_id:
                    break

            if not property_id:
                return None

            # Now get property details
            # Property ID format: typically a number
            detail_endpoint = f"/stingray/api/home/details/aboveTheFold?propertyId={property_id}&accessLevel=1"

            conn2 = http.client.HTTPSConnection(self.api_host)
            conn2.request("GET", detail_endpoint, headers=headers)
            res2 = conn2.getresponse()
            data2 = res2.read()

            if res2.status == 200:
                text2 = data2.decode("utf-8")
                if text2.startswith("{}&&"):
                    text2 = text2[4:]
                return json.loads(text2)

            return None

        except Exception as e:
            print(f"⚠️  Redfin API exception: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
            if 'conn2' in locals():
                conn2.close()

    def get_property_description(self, address: str, city: str, state: str, zipcode: str) -> Optional[str]:
        """
        Get property description from Redfin
        Returns description text or None
        """
        property_data = self.search_property(address, city, state, zipcode)

        if not property_data:
            return None

        # Try to extract description from Redfin response structure
        description_fields = [
            'description',
            'remarks',
            'publicRemarks',
            'listingRemarks'
        ]

        # Check payload
        if 'payload' in property_data and isinstance(property_data['payload'], dict):
            payload = property_data['payload']

            # Check top level of payload
            for field in description_fields:
                if field in payload and payload[field]:
                    return str(payload[field])

            # Check propertyDetails
            if 'propertyDetails' in payload and isinstance(payload['propertyDetails'], dict):
                details = payload['propertyDetails']
                for field in description_fields:
                    if field in details and details[field]:
                        return str(details[field])

            # Check listingInfo
            if 'listingInfo' in payload and isinstance(payload['listingInfo'], dict):
                listing = payload['listingInfo']
                for field in description_fields:
                    if field in listing and listing[field]:
                        return str(listing[field])

        return None
