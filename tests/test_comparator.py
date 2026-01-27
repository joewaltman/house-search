import pytest
from datetime import datetime, timedelta
from app.services.comparator import Comparator
from app.models.listing import Listing


@pytest.fixture
def comparator():
    """Create comparator instance"""
    return Comparator()


@pytest.fixture
def current_listings():
    """Current listings"""
    return {
        "1": Listing(
            listing_id="1",
            address="123 Main St",
            zipcode="92037",
            price=1000000,
            source_api="test"
        ),
        "2": Listing(
            listing_id="2",
            address="456 Beach Ave",
            zipcode="92109",
            price=2000000,
            source_api="test"
        ),
        "3": Listing(
            listing_id="3",
            address="789 Ocean Blvd",
            zipcode="92107",
            price=3000000,
            source_api="test"
        )
    }


@pytest.fixture
def previous_listings():
    """Previous listings"""
    return {
        "1": Listing(
            listing_id="1",
            address="123 Main St",
            zipcode="92037",
            price=950000,  # Price changed
            source_api="test"
        ),
        "2": Listing(
            listing_id="2",
            address="456 Beach Ave",
            zipcode="92109",
            price=2000000,
            status="active",
            source_api="test"
        ),
        "4": Listing(  # Removed
            listing_id="4",
            address="321 Coast Dr",
            zipcode="92118",
            price=1500000,
            last_updated=datetime.utcnow(),
            source_api="test"
        )
    }


def test_find_new_listings(comparator, current_listings, previous_listings):
    """Test finding new listings"""
    new = comparator.find_new_listings(current_listings, previous_listings)

    # Listing 3 is new
    assert len(new) == 1
    assert new[0].listing_id == "3"


def test_find_price_changes(comparator, current_listings, previous_listings):
    """Test finding price changes"""
    changes = comparator.find_price_changes(
        current_listings,
        previous_listings,
        min_change_percent=5.0
    )

    # Listing 1 changed from 950k to 1000k (~5.3% increase)
    assert len(changes) == 1
    listing, old_price, new_price = changes[0]
    assert listing.listing_id == "1"
    assert old_price == 950000
    assert new_price == 1000000


def test_find_removed_listings(comparator, current_listings, previous_listings):
    """Test finding removed listings"""
    removed = comparator.find_removed_listings(
        current_listings,
        previous_listings,
        days_threshold=3
    )

    # Listing 4 was removed
    assert len(removed) == 1
    assert removed[0].listing_id == "4"


def test_get_summary_stats(comparator, current_listings, previous_listings):
    """Test summary statistics"""
    stats = comparator.get_summary_stats(current_listings, previous_listings)

    assert stats['total_current'] == 3
    assert stats['total_previous'] == 3
    assert stats['new_count'] == 1
    assert stats['removed_count'] == 1
    assert stats['price_changes_count'] == 1
