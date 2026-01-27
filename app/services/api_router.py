from typing import List, Optional, Dict
from datetime import datetime
from app.services.rentcast_client import RentCastClient
from app.services.rapidapi_client import RapidAPIClient
from app.services.homesage_client import HomesageClient
from app.services.storage import StorageManager
from app.models.listing import Listing
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class APIRouter:
    """Routes API requests across multiple providers based on quota availability"""

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager

        # Initialize API clients
        self.clients = {}

        if settings.rentcast_api_key:
            self.clients['rentcast'] = RentCastClient(
                api_key=settings.rentcast_api_key
            )

        if settings.rapidapi_key:
            self.clients['rapidapi'] = RapidAPIClient(
                api_key=settings.rapidapi_key
            )

        if settings.homesage_api_key:
            self.clients['homesage'] = HomesageClient(
                api_key=settings.homesage_api_key
            )

        logger.info(f"Initialized API router with {len(self.clients)} clients")

    def fetch_listings_for_zipcode(
        self,
        zipcode: str,
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Listing]:
        """
        Fetch listings for a zipcode using the best available API.
        Returns listings from the first successful API call.
        """
        # Reset quotas if new month
        self.storage.reset_quotas_if_needed()

        # Get quota status
        quotas = self.storage.load_api_quotas()

        # Sort APIs by available quota (descending)
        available_apis = self._get_available_apis(quotas)

        if not available_apis:
            logger.warning("No APIs with available quota!")
            return []

        # Try each API in order until we get results
        for api_name in available_apis:
            client = self.clients.get(api_name)
            if not client:
                continue

            try:
                logger.info(f"Using {api_name} for zipcode {zipcode}")

                listings = client.fetch_listings(
                    zipcode=zipcode,
                    property_types=property_types,
                    min_price=min_price,
                    max_price=max_price
                )

                # Increment quota usage
                self.storage.increment_quota(api_name, count=1)

                if listings:
                    logger.info(
                        f"Successfully fetched {len(listings)} listings from {api_name}"
                    )
                    return listings
                else:
                    logger.info(f"No listings returned from {api_name} for {zipcode}")

            except Exception as e:
                logger.error(f"Error fetching from {api_name}: {e}")
                continue

        logger.warning(f"No listings found for zipcode {zipcode} from any API")
        return []

    def fetch_all_zipcodes(
        self,
        zipcodes: List[str],
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> Dict[str, List[Listing]]:
        """
        Fetch listings for multiple zipcodes, distributing across APIs.
        Returns a dict mapping zipcode -> listings.
        """
        results = {}

        for zipcode in zipcodes:
            listings = self.fetch_listings_for_zipcode(
                zipcode=zipcode,
                property_types=property_types,
                min_price=min_price,
                max_price=max_price
            )
            results[zipcode] = listings

        total_listings = sum(len(listings) for listings in results.values())
        logger.info(
            f"Fetched {total_listings} total listings across {len(zipcodes)} zipcodes"
        )

        return results

    def _get_available_apis(self, quotas: Dict[str, dict]) -> List[str]:
        """
        Get list of APIs with available quota, sorted by remaining quota.
        Returns list of API names in priority order.
        """
        available = []

        for api_name, quota_info in quotas.items():
            if api_name not in self.clients:
                continue

            used = quota_info['used']
            limit = quota_info['limit']

            if used < limit:
                remaining = limit - used
                available.append((api_name, remaining))

        # Sort by remaining quota (descending)
        available.sort(key=lambda x: x[1], reverse=True)

        return [api_name for api_name, _ in available]

    def get_quota_status(self) -> Dict[str, dict]:
        """Get current quota status for all APIs"""
        quotas = self.storage.load_api_quotas()
        status = {}

        for api_name, quota_info in quotas.items():
            if api_name in self.clients:
                used = quota_info['used']
                limit = quota_info['limit']
                remaining = limit - used
                percentage = (used / limit * 100) if limit > 0 else 0

                status[api_name] = {
                    'used': used,
                    'limit': limit,
                    'remaining': remaining,
                    'percentage': round(percentage, 1),
                    'reset_date': quota_info['reset_date']
                }

        return status

    def check_quota_health(self) -> bool:
        """
        Check if we have sufficient quota remaining.
        Returns True if at least one API has >10% quota remaining.
        """
        status = self.get_quota_status()

        for api_name, info in status.items():
            if info['remaining'] > (info['limit'] * 0.1):
                return True

        logger.warning("Low quota across all APIs!")
        return False
