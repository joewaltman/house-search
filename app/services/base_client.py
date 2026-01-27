from abc import ABC, abstractmethod
from typing import List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseAPIClient(ABC):
    """Base class for all MLS API clients"""

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def __del__(self):
        """Cleanup HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()

    @abstractmethod
    def get_api_name(self) -> str:
        """Return the name of this API"""
        pass

    @abstractmethod
    def fetch_listings(
        self,
        zipcode: str,
        property_types: List[str],
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Listing]:
        """
        Fetch listings for a zipcode.
        Must be implemented by each API client.
        """
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> dict:
        """Make HTTP request with retry logic"""
        try:
            response = self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"{self.get_api_name()} HTTP error {e.response.status_code}: {e}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"{self.get_api_name()} request error: {e}")
            raise
        except Exception as e:
            logger.error(f"{self.get_api_name()} unexpected error: {e}")
            raise

    def _normalize_property_type(self, raw_type: str) -> str:
        """Normalize property type strings across different APIs"""
        raw_lower = raw_type.lower()

        if any(x in raw_lower for x in ['single', 'detached', 'sfr']):
            return 'single_family'
        elif any(x in raw_lower for x in ['multi', 'duplex', 'triplex', 'fourplex']):
            return 'multi_family'
        elif 'condo' in raw_lower or 'townhouse' in raw_lower:
            return 'condo'
        elif 'apartment' in raw_lower:
            return 'apartment'
        else:
            return raw_type

    def _generate_listing_id(self, address: str, zipcode: str) -> str:
        """Generate a consistent listing ID from address and zipcode"""
        import hashlib
        key = f"{address.lower().strip()}_{zipcode}".encode()
        return hashlib.md5(key).hexdigest()[:12]
