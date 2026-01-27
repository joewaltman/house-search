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
        """
        Fetch property records from RentCast.
        Note: RentCast free tier provides property database records, not active MLS listings.
        Use RapidAPI or Homesage for real-time MLS data.
        """
        logger.info(f"Fetching RentCast property data for zipcode {zipcode}")

        try:
            headers = {"X-Api-Key": self.api_key}

            # RentCast properties endpoint
            params = {
                "zipCode": zipcode,
                "limit": 50  # Max per request
            }

            response = self._make_request(
                method="GET",
                url=f"{self.BASE_URL}/properties",
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

    def _parse_response(self, response, zipcode: str) -> List[Listing]:
        """
        Parse RentCast API response into Listing objects.
        Note: RentCast returns property records, not active listings.
        These don't include prices, so we skip them for our use case.
        """
        listings = []

        # Response is a list directly, not nested
        items = response if isinstance(response, list) else response.get('properties', [])

        for item in items:
            try:
                # Extract address
                address = item.get('formattedAddress', '')
                if not address:
                    continue

                # RentCast property database doesn't include listing prices
                # Skip since we need prices for our monitoring
                # This API is better suited for property details enrichment
                logger.debug(f"Skipping RentCast property {address} (no listing price)")
                continue

            except Exception as e:
                logger.error(f"Error parsing RentCast property: {e}")
                continue

        logger.info(
            f"RentCast returned {len(items)} property records for {zipcode}, "
            f"but none are active listings with prices"
        )
        return listings

    def _get_first_photo(self, item: dict) -> Optional[str]:
        """Extract first photo URL from listing"""
        photos = item.get('photos', [])
        return photos[0] if photos else None
