import pytest
from app.services.aggregator import Aggregator
from app.models.listing import Listing


@pytest.fixture
def aggregator():
    """Create aggregator instance"""
    return Aggregator()


@pytest.fixture
def duplicate_listings():
    """Create listings with duplicates from different sources"""
    return {
        'rentcast': [
            Listing(
                listing_id="rc1",
                address="123 Main Street",
                zipcode="92037",
                price=1500000,
                lot_size_sqft=10000,
                mls_number="MLS123",
                source_api="rentcast"
            ),
            Listing(
                listing_id="rc2",
                address="456 Beach Ave",
                zipcode="92109",
                price=2000000,
                lot_size_sqft=8500,
                source_api="rentcast"
            )
        ],
        'rapidapi': [
            Listing(
                listing_id="ra1",
                address="123 Main St",  # Duplicate of rc1
                zipcode="92037",
                price=1500500,  # Similar price
                lot_size_sqft=None,  # Less complete
                source_api="rapidapi"
            ),
            Listing(
                listing_id="ra2",
                address="789 Ocean Blvd",
                zipcode="92107",
                price=3000000,
                lot_size_sqft=12000,
                source_api="rapidapi"
            )
        ]
    }


def test_aggregate_and_deduplicate(aggregator, duplicate_listings):
    """Test aggregation and deduplication"""
    result = aggregator.aggregate_and_deduplicate(duplicate_listings)

    # Should have 3 unique listings (rc1/ra1 are duplicates)
    assert len(result) == 3

    # Check that the better version was kept (has lot_size and MLS)
    main_street = [l for l in result if "main" in l.address.lower()][0]
    assert main_street.lot_size_sqft == 10000
    assert main_street.mls_number == "MLS123"


def test_normalize_address_key(aggregator):
    """Test address normalization"""
    listing1 = Listing(
        listing_id="1",
        address="123 Main Street",
        zipcode="92037",
        price=1000000,
        source_api="test"
    )

    listing2 = Listing(
        listing_id="2",
        address="123 Main St",  # Abbreviated
        zipcode="92037",
        price=1000000,
        source_api="test"
    )

    key1 = aggregator._normalize_address_key(listing1)
    key2 = aggregator._normalize_address_key(listing2)

    # Should be the same key
    assert key1 == key2


def test_completeness_score(aggregator):
    """Test data completeness scoring"""
    complete_listing = Listing(
        listing_id="1",
        address="123 Main St",
        zipcode="92037",
        price=1000000,
        lot_size_sqft=10000,
        mls_number="MLS123",
        listing_url="https://example.com",
        photo_url="https://example.com/photo.jpg",
        bedrooms=3,
        bathrooms=2.5,
        sqft=2000,
        year_built=2020,
        description="Nice house",
        city="San Diego",
        source_api="test"
    )

    incomplete_listing = Listing(
        listing_id="2",
        address="456 Beach Ave",
        zipcode="92109",
        price=1500000,
        source_api="test"
    )

    score_complete = aggregator._calculate_completeness_score(complete_listing)
    score_incomplete = aggregator._calculate_completeness_score(incomplete_listing)

    # Complete listing should have much higher score
    assert score_complete > score_incomplete
    assert score_complete > 20  # Has many fields


def test_merge_with_existing(aggregator):
    """Test merging new listings with existing ones"""
    existing = {
        "1": Listing(
            listing_id="1",
            address="123 Main St",
            zipcode="92037",
            price=1000000,
            lot_size_sqft=10000,
            source_api="test"
        )
    }

    new = [
        Listing(
            listing_id="1",  # Update existing
            address="123 Main St",
            zipcode="92037",
            price=1050000,  # Price changed
            lot_size_sqft=10000,
            bedrooms=3,  # New data
            source_api="test"
        ),
        Listing(
            listing_id="2",  # New listing
            address="456 Beach Ave",
            zipcode="92109",
            price=2000000,
            source_api="test"
        )
    ]

    merged = aggregator.merge_with_existing(new, existing)

    # Should have 2 listings
    assert len(merged) == 2

    # Existing should be updated
    assert merged["1"].price == 1050000
    assert merged["1"].bedrooms == 3

    # New listing should be added
    assert "2" in merged
