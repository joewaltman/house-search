from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class Comparator:
    """Compares new listings against existing ones to find what's new"""

    def find_new_listings(
        self,
        current_listings: Dict[str, Listing],
        previous_listings: Dict[str, Listing]
    ) -> List[Listing]:
        """
        Find listings that are new (not in previous batch).

        Args:
            current_listings: Dict of current listings (listing_id -> Listing)
            previous_listings: Dict of previously seen listings

        Returns:
            List of new listings
        """
        new_listings = []

        for listing_id, listing in current_listings.items():
            if listing_id not in previous_listings:
                new_listings.append(listing)

        logger.info(
            f"Found {len(new_listings)} new listings "
            f"(current: {len(current_listings)}, previous: {len(previous_listings)})"
        )

        return new_listings

    def find_price_changes(
        self,
        current_listings: Dict[str, Listing],
        previous_listings: Dict[str, Listing],
        min_change_percent: float = 5.0
    ) -> List[Tuple[Listing, int, int]]:
        """
        Find listings with significant price changes.

        Args:
            current_listings: Current listings
            previous_listings: Previous listings
            min_change_percent: Minimum % change to report (default 5%)

        Returns:
            List of tuples: (listing, old_price, new_price)
        """
        price_changes = []

        for listing_id, current in current_listings.items():
            if listing_id in previous_listings:
                previous = previous_listings[listing_id]

                old_price = previous.price
                new_price = current.price

                if old_price != new_price:
                    change_percent = abs((new_price - old_price) / old_price * 100)

                    if change_percent >= min_change_percent:
                        price_changes.append((current, old_price, new_price))
                        logger.info(
                            f"Price change detected for {current.address}: "
                            f"${old_price:,} -> ${new_price:,} "
                            f"({change_percent:.1f}%)"
                        )

        return price_changes

    def find_status_changes(
        self,
        current_listings: Dict[str, Listing],
        previous_listings: Dict[str, Listing]
    ) -> List[Tuple[Listing, str, str]]:
        """
        Find listings with status changes (e.g., active -> pending).

        Returns:
            List of tuples: (listing, old_status, new_status)
        """
        status_changes = []

        for listing_id, current in current_listings.items():
            if listing_id in previous_listings:
                previous = previous_listings[listing_id]

                if current.status != previous.status:
                    status_changes.append(
                        (current, previous.status, current.status)
                    )
                    logger.info(
                        f"Status change for {current.address}: "
                        f"{previous.status} -> {current.status}"
                    )

        return status_changes

    def find_removed_listings(
        self,
        current_listings: Dict[str, Listing],
        previous_listings: Dict[str, Listing],
        days_threshold: int = 3
    ) -> List[Listing]:
        """
        Find listings that have been removed (sold or delisted).

        Args:
            current_listings: Current listings
            previous_listings: Previous listings
            days_threshold: Only report if listing was seen within this many days

        Returns:
            List of removed listings
        """
        removed = []
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        for listing_id, previous in previous_listings.items():
            if listing_id not in current_listings:
                # Check if it was recently active
                if previous.last_updated >= cutoff_date:
                    removed.append(previous)
                    logger.info(
                        f"Listing removed: {previous.address} "
                        f"(last seen {previous.last_updated.date()})"
                    )

        return removed

    def get_summary_stats(
        self,
        current_listings: Dict[str, Listing],
        previous_listings: Dict[str, Listing]
    ) -> dict:
        """
        Get summary statistics about listing changes.

        Returns dict with:
        - total_current: Number of current listings
        - total_previous: Number of previous listings
        - new_count: Number of new listings
        - removed_count: Number of removed listings
        - price_changes: Number of price changes
        - status_changes: Number of status changes
        """
        new = self.find_new_listings(current_listings, previous_listings)
        removed = self.find_removed_listings(current_listings, previous_listings)
        price_changes = self.find_price_changes(current_listings, previous_listings)
        status_changes = self.find_status_changes(current_listings, previous_listings)

        return {
            'total_current': len(current_listings),
            'total_previous': len(previous_listings),
            'new_count': len(new),
            'removed_count': len(removed),
            'price_changes_count': len(price_changes),
            'status_changes_count': len(status_changes)
        }
