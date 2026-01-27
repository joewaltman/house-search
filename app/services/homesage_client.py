from typing import List, Optional
from datetime import datetime
from app.services.base_client import BaseAPIClient
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class HomesageClient(BaseAPIClient):
    """Client for Homesage.ai API - 500 credits/month free tier"""

    BASE_URL = "https://api.homesage.ai/v1"

    def get_api_name(self) -> str:
        return "homesage"

    def fetch_listings(
        self,
        zipcode: str,
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Listing]:
        """Fetch for-sale listings from Homesage"""
        logger.info(f"Fetching Homesage listings for zipcode {zipcode}")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            params = {
                "zip_code": zipcode,
                "status": "for_sale",
                "limit": 50
            }

            if min_price:
                params["min_price"] = min_price
            if max_price:
                params["max_price"] = max_price

            response = self._make_request(
                method="GET",
                url=f"{self.BASE_URL}/properties/search",
                headers=headers,
                params=params
            )

            return self._parse_response(response, zipcode)

        except Exception as e:
            logger.error(f"Error fetching from Homesage for {zipcode}: {e}")
            return []

    def _parse_response(self, response: dict, zipcode: str) -> List[Listing]:
        """Parse Homesage API response into Listing objects"""
        listings = []

        properties = response.get('properties', [])

        for item in properties:
            try:
                address = item.get('address', {})
                full_address = address.get('full_address', '')

                if not full_address:
                    continue

                # Extract property details
                details = item.get('property_details', {})

                listing = Listing(
                    listing_id=item.get('property_id') or self._generate_listing_id(
                        full_address, zipcode
                    ),
                    address=full_address,
                    city=address.get('city'),
                    state=address.get('state', 'CA'),
                    zipcode=zipcode,
                    price=int(item.get('price', 0)),
                    bedrooms=details.get('bedrooms'),
                    bathrooms=details.get('bathrooms'),
                    sqft=details.get('square_feet'),
                    lot_size_sqft=details.get('lot_size_sqft'),
                    year_built=details.get('year_built'),
                    property_type=self._normalize_property_type(
                        details.get('property_type', 'Unknown')
                    ),
                    status='active',
                    listing_url=item.get('listing_url'),
                    photo_url=self._get_photo_url(item),
                    mls_number=item.get('mls_number'),
                    source_api=self.get_api_name(),
                    description=item.get('description'),
                    hoa_fee=item.get('hoa_fee')
                )

                listings.append(listing)

            except Exception as e:
                logger.error(f"Error parsing Homesage listing: {e}")
                continue

        logger.info(f"Parsed {len(listings)} listings from Homesage for {zipcode}")
        return listings

    def _get_photo_url(self, item: dict) -> Optional[str]:
        """Extract photo URL from listing"""
        images = item.get('images', [])
        if images and len(images) > 0:
            return images[0].get('url')
        return None
