from typing import List
from app.models.listing import Listing
from app.models.config_model import FiltersConfig
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class ListingFilter:
    """Filters listings based on criteria"""

    def __init__(self, filter_config: FiltersConfig):
        self.config = filter_config

    def filter_listings(
        self,
        listings: List[Listing],
        property_types: List[str]
    ) -> List[Listing]:
        """
        Apply all filters to listings.

        Filters:
        1. Price range (min/max)
        2. Lot size (>= min_lot_size_sqft)
        3. Ocean proximity (longitude threshold)
        4. Property type (single_family, multi_family)

        Returns:
            Filtered list of listings
        """
        logger.info(f"Filtering {len(listings)} listings")

        filtered = listings

        # Apply each filter
        filtered = self._filter_by_price(filtered)
        filtered = self._filter_by_lot_size(filtered)
        filtered = self._filter_by_ocean_proximity(filtered)
        filtered = self._filter_by_property_type(filtered, property_types)

        logger.info(
            f"Filtered {len(listings)} listings -> {len(filtered)} "
            f"({len(listings) - len(filtered)} excluded)"
        )

        return filtered

    def _filter_by_price(self, listings: List[Listing]) -> List[Listing]:
        """Filter by price range"""
        filtered = []

        for listing in listings:
            if listing.price < self.config.min_price:
                logger.debug(
                    f"Excluded {listing.address}: price ${listing.price} "
                    f"< min ${self.config.min_price}"
                )
                continue

            if listing.price > self.config.max_price:
                logger.debug(
                    f"Excluded {listing.address}: price ${listing.price} "
                    f"> max ${self.config.max_price}"
                )
                continue

            filtered.append(listing)

        logger.info(f"Price filter: {len(listings)} -> {len(filtered)}")
        return filtered

    def _filter_by_lot_size(self, listings: List[Listing]) -> List[Listing]:
        """
        Filter by minimum lot size.

        Strategy: Exclude properties without lot size data OR with lot size < minimum.
        This ensures we only get properties with sufficient land.
        """
        filtered = []
        no_data_count = 0

        for listing in listings:
            if listing.lot_size_sqft is None:
                # No lot size data - exclude
                logger.debug(
                    f"Excluded {listing.address}: no lot size data"
                )
                no_data_count += 1
                continue

            if listing.lot_size_sqft < self.config.min_lot_size_sqft:
                logger.debug(
                    f"Excluded {listing.address}: lot size {listing.lot_size_sqft} sqft "
                    f"< min {self.config.min_lot_size_sqft} sqft"
                )
                continue

            filtered.append(listing)

        logger.info(
            f"Lot size filter (>= {self.config.min_lot_size_sqft} sqft): "
            f"{len(listings)} -> {len(filtered)} "
            f"({no_data_count} excluded for missing data)"
        )

        return filtered

    def _filter_by_ocean_proximity(self, listings: List[Listing]) -> List[Listing]:
        """
        Filter by ocean proximity using longitude threshold.

        Properties WEST of max_longitude (more negative) are closer to ocean.
        Strategy: Exclude properties without coordinate data OR east of threshold.
        """
        # Skip filtering if max_longitude not configured
        if self.config.max_longitude is None:
            logger.info("Ocean proximity filter: SKIPPED (max_longitude not configured)")
            return listings

        filtered = []
        no_data_count = 0

        for listing in listings:
            if listing.longitude is None:
                # No coordinate data - exclude
                logger.debug(
                    f"Excluded {listing.address}: no longitude data"
                )
                no_data_count += 1
                continue

            # Keep properties WEST of threshold (longitude <= max_longitude)
            # More negative = further west = closer to ocean
            if listing.longitude <= self.config.max_longitude:
                filtered.append(listing)
            else:
                logger.debug(
                    f"Excluded {listing.address}: longitude {listing.longitude} "
                    f"too far east (threshold: {self.config.max_longitude})"
                )

        logger.info(
            f"Ocean proximity filter (<= {self.config.max_longitude} lon): "
            f"{len(listings)} -> {len(filtered)} "
            f"({no_data_count} excluded for missing coordinates)"
        )

        return filtered

    def _filter_by_property_type(
        self,
        listings: List[Listing],
        property_types: List[str]
    ) -> List[Listing]:
        """Filter by property type"""
        if not property_types:
            return listings

        filtered = []

        for listing in listings:
            if listing.property_type in property_types:
                filtered.append(listing)
            else:
                logger.debug(
                    f"Excluded {listing.address}: property type '{listing.property_type}' "
                    f"not in {property_types}"
                )

        logger.info(f"Property type filter: {len(listings)} -> {len(filtered)}")
        return filtered

    def get_filter_summary(self) -> str:
        """Get human-readable summary of filter criteria"""
        summary = (
            f"Price: ${self.config.min_price:,} - ${self.config.max_price:,}, "
            f"Lot Size: >= {self.config.min_lot_size_sqft:,} sqft"
        )
        if self.config.max_longitude is not None:
            summary += f", Ocean Proximity: lon <= {self.config.max_longitude}"
        return summary
