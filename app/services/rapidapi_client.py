from typing import List, Optional
from datetime import datetime
from app.services.base_client import BaseAPIClient
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class RapidAPIClient(BaseAPIClient):
    """Client for Realtor Search API via RapidAPI - Free tier"""

    BASE_URL = "https://realtor-search.p.rapidapi.com"

    def get_api_name(self) -> str:
        return "rapidapi"

    def fetch_listings(
        self,
        zipcode: str,
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Listing]:
        """Fetch for-sale listings from Realtor Search API"""
        logger.info(f"Fetching Realtor Search listings for zipcode {zipcode}")

        try:
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "realtor-search.p.rapidapi.com"
            }

            # Realtor Search API uses location parameter with "zip:" prefix
            params = {
                "location": f"zip:{zipcode}",
                "sortBy": "relevance"
            }

            response = self._make_request(
                method="GET",
                url=f"{self.BASE_URL}/properties/search-buy",
                headers=headers,
                params=params
            )

            return self._parse_response(response, zipcode)

        except Exception as e:
            logger.error(f"Error fetching from Realtor Search for {zipcode}: {e}")
            return []

    def _parse_response(self, response: dict, zipcode: str) -> List[Listing]:
        """Parse Realtor Search API response into Listing objects"""
        listings = []

        # Check if request was successful
        if not response.get('status'):
            logger.warning(f"API returned error: {response.get('message', 'Unknown error')}")
            return listings

        # Get results from data object
        data = response.get('data', {})
        results = data.get('results', [])

        if not results:
            logger.info(f"No results found for zipcode {zipcode}")
            return listings

        for item in results:
            try:
                # Extract location information
                location = item.get('location', {})
                address_obj = location.get('address', {})

                address_line = address_obj.get('line', '')
                if not address_line:
                    continue

                city = address_obj.get('city', '')
                state = address_obj.get('state_code', 'CA')
                postal_code = address_obj.get('postal_code', zipcode)

                # Extract coordinates for ocean proximity filtering
                coordinate = address_obj.get('coordinate', {})
                latitude = coordinate.get('lat')
                longitude = coordinate.get('lon')

                # Get price
                list_price = item.get('list_price')
                if not list_price:
                    logger.debug(f"Skipping listing without price: {address_line}")
                    continue

                # Get property description/details
                description = item.get('description', {})

                beds = description.get('beds')
                baths = description.get('baths')
                sqft = description.get('sqft')
                lot_sqft = description.get('lot_sqft')  # Critical for our 8000 sqft filter!
                prop_type = description.get('type', 'Unknown')

                # Extract year built from details if available
                year_built = None
                details = item.get('details', [])
                for detail_section in details:
                    if detail_section.get('category') == 'Building and Construction':
                        for text in detail_section.get('text', []):
                            if 'Year Built:' in text:
                                try:
                                    year_built = int(text.split('Year Built:')[1].strip())
                                except:
                                    pass

                # Get photo
                primary_photo = item.get('primary_photo', {})
                photo_url = primary_photo.get('href') if primary_photo else None

                # Get HOA fee
                hoa_fee = None
                for detail_section in details:
                    if detail_section.get('category') == 'Homeowners Association':
                        for text in detail_section.get('text', []):
                            if 'Association Fee:' in text:
                                try:
                                    fee_str = text.split('Association Fee:')[1].strip()
                                    hoa_fee = int(fee_str.replace(',', ''))
                                except:
                                    pass

                # Get MLS number from source
                source = item.get('source', {})
                mls_number = source.get('listing_id')

                listing = Listing(
                    listing_id=item.get('property_id') or self._generate_listing_id(
                        address_line, postal_code
                    ),
                    address=address_line,
                    city=city,
                    state=state,
                    zipcode=postal_code,
                    latitude=latitude,
                    longitude=longitude,
                    price=int(list_price),
                    bedrooms=beds,
                    bathrooms=baths,
                    sqft=sqft,
                    lot_size_sqft=lot_sqft,
                    year_built=year_built,
                    property_type=self._normalize_property_type(prop_type),
                    status='active',
                    listing_url=item.get('href'),
                    photo_url=photo_url,
                    mls_number=mls_number,
                    source_api=self.get_api_name(),
                    hoa_fee=hoa_fee
                )

                listings.append(listing)

            except Exception as e:
                logger.error(f"Error parsing Realtor Search listing: {e}")
                logger.debug(f"Problematic item keys: {item.keys() if isinstance(item, dict) else 'not a dict'}")
                continue

        logger.info(f"Parsed {len(listings)} listings from Realtor Search for {zipcode}")
        return listings

    def _get_primary_photo(self, item: dict) -> Optional[str]:
        """Extract primary photo URL from listing"""
        primary = item.get('primary_photo', {})
        if primary:
            return primary.get('href')
        return None
