from typing import List, Optional
from datetime import datetime
from app.services.base_client import BaseAPIClient
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class RentCastClient(BaseAPIClient):
    """Client for RentCast API - 50 calls/month free tier"""

    BASE_URL = "https://api.rentcast.io/v1"

    def get_api_name(self) -> str:
        return "rentcast"

    def fetch_listings(
        self,
        zipcode: str,
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Listing]:
        """Fetch for-sale listings from RentCast"""
        logger.info(f"Fetching RentCast listings for zipcode {zipcode}")

        try:
            headers = {"X-Api-Key": self.api_key}

            # RentCast uses different endpoint for for-sale properties
            params = {
                "zipCode": zipcode,
                "status": "Active",
                "propertyType": self._map_property_types(property_types),
                "limit": 50  # Max per request
            }

            if min_price:
                params["priceMin"] = min_price
            if max_price:
                params["priceMax"] = max_price

            response = self._make_request(
                method="GET",
                url=f"{self.BASE_URL}/listings/sale",
                headers=headers,
                params=params
            )

            return self._parse_response(response, zipcode)

        except Exception as e:
            logger.error(f"Error fetching from RentCast for {zipcode}: {e}")
            return []

    def _map_property_types(self, property_types: List[str]) -> str:
        """Map our property types to RentCast format"""
        mapping = {
            'single_family': 'Single Family',
            'multi_family': 'Multi Family',
            'condo': 'Condo',
            'townhouse': 'Townhouse'
        }

        rentcast_types = []
        for pt in property_types:
            if pt in mapping:
                rentcast_types.append(mapping[pt])

        return ','.join(rentcast_types) if rentcast_types else 'Single Family,Multi Family'

    def _parse_response(self, response: dict, zipcode: str) -> List[Listing]:
        """Parse RentCast API response into Listing objects"""
        listings = []

        for item in response.get('properties', []):
            try:
                # Extract address
                address_obj = item.get('address', {})
                address = address_obj.get('formattedAddress', '')

                if not address:
                    continue

                listing = Listing(
                    listing_id=item.get('id') or self._generate_listing_id(address, zipcode),
                    address=address,
                    city=address_obj.get('city'),
                    state=address_obj.get('state', 'CA'),
                    zipcode=zipcode,
                    price=int(item.get('price', 0)),
                    bedrooms=item.get('bedrooms'),
                    bathrooms=item.get('bathrooms'),
                    sqft=item.get('squareFootage'),
                    lot_size_sqft=item.get('lotSize'),
                    year_built=item.get('yearBuilt'),
                    property_type=self._normalize_property_type(
                        item.get('propertyType', 'Unknown')
                    ),
                    status='active',
                    listing_url=item.get('listingUrl'),
                    photo_url=self._get_first_photo(item),
                    mls_number=item.get('mlsNumber'),
                    source_api=self.get_api_name(),
                    description=item.get('description'),
                    hoa_fee=item.get('hoaFee'),
                    parking_spaces=item.get('parking', {}).get('spaces')
                )

                listings.append(listing)

            except Exception as e:
                logger.error(f"Error parsing RentCast listing: {e}")
                continue

        logger.info(f"Parsed {len(listings)} listings from RentCast for {zipcode}")
        return listings

    def _get_first_photo(self, item: dict) -> Optional[str]:
        """Extract first photo URL from listing"""
        photos = item.get('photos', [])
        return photos[0] if photos else None
