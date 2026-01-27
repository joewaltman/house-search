from typing import List, Dict
from collections import defaultdict
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class Aggregator:
    """Aggregates and deduplicates listings from multiple API sources"""

    def aggregate_and_deduplicate(
        self,
        listings_by_source: Dict[str, List[Listing]]
    ) -> List[Listing]:
        """
        Combine listings from multiple sources and remove duplicates.

        Deduplication strategy:
        1. Group by address + zipcode (normalized)
        2. If multiple listings match, keep the one with most complete data
        3. Prefer listings with lot_size_sqft data when available

        Args:
            listings_by_source: Dict mapping source/zipcode -> list of listings

        Returns:
            Deduplicated list of listings
        """
        all_listings = []
        for listings in listings_by_source.values():
            all_listings.extend(listings)

        logger.info(f"Aggregating {len(all_listings)} listings from all sources")

        # Group listings by normalized address
        grouped = defaultdict(list)
        for listing in all_listings:
            key = self._normalize_address_key(listing)
            grouped[key].append(listing)

        # Deduplicate each group
        deduplicated = []
        duplicate_count = 0

        for key, group in grouped.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Multiple listings for same property - pick best one
                best = self._select_best_listing(group)
                deduplicated.append(best)
                duplicate_count += len(group) - 1

        logger.info(
            f"Deduplicated {len(all_listings)} listings -> "
            f"{len(deduplicated)} unique ({duplicate_count} duplicates removed)"
        )

        return deduplicated

    def _normalize_address_key(self, listing: Listing) -> str:
        """Create normalized key for address matching"""
        # Normalize address: lowercase, remove extra spaces
        address = listing.address.lower().strip()

        # Remove common variations
        address = (
            address
            .replace(' street', ' st')
            .replace(' avenue', ' ave')
            .replace(' road', ' rd')
            .replace(' drive', ' dr')
            .replace(' boulevard', ' blvd')
        )

        # Remove punctuation
        address = address.replace(',', '').replace('.', '')

        # Create key: normalized_address + zipcode
        return f"{address}_{listing.zipcode}"

    def _select_best_listing(self, listings: List[Listing]) -> Listing:
        """
        Select the best listing from duplicates.

        Priority:
        1. Most complete data (non-null fields)
        2. Has lot_size_sqft data (critical for filtering)
        3. Has MLS number (more authoritative)
        4. Most recent first_seen timestamp
        """
        scored = []

        for listing in listings:
            score = self._calculate_completeness_score(listing)
            scored.append((score, listing))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        best = scored[0][1]
        logger.debug(
            f"Selected best listing for {best.address} from {len(listings)} duplicates "
            f"(source: {best.source_api})"
        )

        return best

    def _calculate_completeness_score(self, listing: Listing) -> int:
        """Calculate data completeness score for a listing"""
        score = 0

        # Critical fields (higher weight)
        if listing.lot_size_sqft is not None:
            score += 10
        if listing.mls_number:
            score += 8
        if listing.listing_url:
            score += 5
        if listing.photo_url:
            score += 3

        # Standard fields
        if listing.bedrooms is not None:
            score += 2
        if listing.bathrooms is not None:
            score += 2
        if listing.sqft is not None:
            score += 2
        if listing.year_built is not None:
            score += 1
        if listing.description:
            score += 1
        if listing.city:
            score += 1

        return score

    def merge_with_existing(
        self,
        new_listings: List[Listing],
        existing_listings: Dict[str, Listing]
    ) -> Dict[str, Listing]:
        """
        Merge new listings with existing ones.
        Updates existing listings if data is more complete.

        Returns:
            Updated dict of all listings
        """
        merged = existing_listings.copy()

        for new_listing in new_listings:
            listing_id = new_listing.listing_id

            if listing_id in merged:
                # Update existing listing if new data is better
                existing = merged[listing_id]
                updated = self._merge_listing_data(existing, new_listing)
                merged[listing_id] = updated
            else:
                # Add new listing
                merged[listing_id] = new_listing

        return merged

    def _merge_listing_data(
        self,
        existing: Listing,
        new: Listing
    ) -> Listing:
        """
        Merge data from two listings, preferring non-null values.
        Updates last_updated timestamp.
        """
        # Start with existing data
        merged_data = existing.model_dump()

        # Update with new non-null values
        new_data = new.model_dump()
        for key, value in new_data.items():
            if key in ['first_seen', 'listing_id']:
                # Never update these fields
                continue

            if value is not None and (merged_data.get(key) is None or key == 'last_updated'):
                merged_data[key] = value

        return Listing(**merged_data)
