from typing import List, Optional
from datetime import datetime
from app.services.base_client import BaseAPIClient
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class RapidAPIClient(BaseAPIClient):
    """Client for RapidAPI US Real Estate - 100 calls/month free tier"""

    BASE_URL = "https://us-real-estate.p.rapidapi.com"

    def get_api_name(self) -> str:
        return "rapidapi"

    def fetch_listings(
        self,
        zipcode: str,
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Listing]:
        """Fetch for-sale listings from RapidAPI"""
        logger.info(f"Fetching RapidAPI listings for zipcode {zipcode}")

        try:
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "us-real-estate.p.rapidapi.com"
            }

            params = {
                "postal_code": zipcode,
                "status": "for_sale",
                "limit": 50,
                "offset": 0
            }

            # Add property type filters if supported
            if property_types:
                params["property_type"] = self._map_property_types(property_types)

            if min_price:
                params["price_min"] = min_price
            if max_price:
                params["price_max"] = max_price

            response = self._make_request(
                method="GET",
                url=f"{self.BASE_URL}/v2/for-sale",
                headers=headers,
                params=params
            )

            return self._parse_response(response, zipcode)

        except Exception as e:
            logger.error(f"Error fetching from RapidAPI for {zipcode}: {e}")
            return []

    def _map_property_types(self, property_types: List[str]) -> str:
        """Map our property types to RapidAPI format"""
        mapping = {
            'single_family': 'single_family',
            'multi_family': 'multi_family',
            'condo': 'condo',
            'townhouse': 'townhouse'
        }

        rapidapi_types = []
        for pt in property_types:
            if pt in mapping:
                rapidapi_types.append(mapping[pt])

        return ','.join(rapidapi_types) if rapidapi_types else 'single_family,multi_family'

    def _parse_response(self, response: dict, zipcode: str) -> List[Listing]:
        """Parse RapidAPI response into Listing objects"""
        listings = []

        # RapidAPI response structure may vary, adjust based on actual API docs
        results = response.get('data', {}).get('results', [])

        for item in results:
            try:
                # Extract address components
                address_obj = item.get('location', {}).get('address', {})
                address_line = address_obj.get('line', '')
                city = address_obj.get('city', '')

                if not address_line:
                    continue

                # Get property details
                description_obj = item.get('description', {})

                listing = Listing(
                    listing_id=item.get('property_id') or self._generate_listing_id(
                        address_line, zipcode
                    ),
                    address=address_line,
                    city=city,
                    state=address_obj.get('state', 'CA'),
                    zipcode=zipcode,
                    price=int(item.get('list_price', 0)),
                    bedrooms=description_obj.get('beds'),
                    bathrooms=description_obj.get('baths'),
                    sqft=description_obj.get('sqft'),
                    lot_size_sqft=description_obj.get('lot_sqft'),
                    year_built=description_obj.get('year_built'),
                    property_type=self._normalize_property_type(
                        description_obj.get('type', 'Unknown')
                    ),
                    status='active',
                    listing_url=item.get('href'),
                    photo_url=self._get_primary_photo(item),
                    mls_number=item.get('mls', {}).get('id'),
                    source_api=self.get_api_name(),
                    description=description_obj.get('text'),
                    hoa_fee=item.get('hoa', {}).get('fee')
                )

                listings.append(listing)

            except Exception as e:
                logger.error(f"Error parsing RapidAPI listing: {e}")
                continue

        logger.info(f"Parsed {len(listings)} listings from RapidAPI for {zipcode}")
        return listings

    def _get_primary_photo(self, item: dict) -> Optional[str]:
        """Extract primary photo URL from listing"""
        photos = item.get('photos', [])
        if photos and len(photos) > 0:
            return photos[0].get('href')
        return None
