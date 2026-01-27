import pytest
from app.services.filters import ListingFilter
from app.models.listing import Listing
from app.models.config_model import FiltersConfig


@pytest.fixture
def filter_config():
    """Create filter configuration"""
    return FiltersConfig(
        min_price=400000,
        max_price=5000000,
        min_lot_size_sqft=8000
    )


@pytest.fixture
def listing_filter(filter_config):
    """Create listing filter instance"""
    return ListingFilter(filter_config)


@pytest.fixture
def sample_listings():
    """Create sample listings for testing"""
    return [
        Listing(
            listing_id="1",
            address="123 Main St",
            zipcode="92037",
            price=1500000,
            lot_size_sqft=10000,
            property_type="single_family",
            source_api="rentcast"
        ),
        Listing(
            listing_id="2",
            address="456 Beach Ave",
            zipcode="92109",
            price=2000000,
            lot_size_sqft=5000,  # Too small
            property_type="single_family",
            source_api="rapidapi"
        ),
        Listing(
            listing_id="3",
            address="789 Ocean Blvd",
            zipcode="92107",
            price=3000000,
            lot_size_sqft=None,  # No lot size data
            property_type="single_family",
            source_api="homesage"
        ),
        Listing(
            listing_id="4",
            address="321 Coastal Dr",
            zipcode="92118",
            price=300000,  # Too cheap
            lot_size_sqft=9000,
            property_type="single_family",
            source_api="rentcast"
        ),
        Listing(
            listing_id="5",
            address="654 Sunset Way",
            zipcode="92075",
            price=4500000,
            lot_size_sqft=12000,
            property_type="condo",  # Wrong type
            source_api="rapidapi"
        )
    ]


def test_filter_by_price(listing_filter, sample_listings):
    """Test price filtering"""
    filtered = listing_filter._filter_by_price(sample_listings)

    # Should exclude listing with price < 400000
    assert len(filtered) == 4
    assert all(l.price >= 400000 for l in filtered)
    assert all(l.price <= 5000000 for l in filtered)


def test_filter_by_lot_size(listing_filter, sample_listings):
    """Test lot size filtering"""
    filtered = listing_filter._filter_by_lot_size(sample_listings)

    # Should only include listings with lot_size >= 8000
    # Excludes: listing 2 (5000), listing 3 (None)
    assert len(filtered) == 3
    assert all(l.lot_size_sqft >= 8000 for l in filtered)


def test_filter_by_property_type(listing_filter, sample_listings):
    """Test property type filtering"""
    property_types = ['single_family', 'multi_family']

    filtered = listing_filter._filter_by_property_type(
        sample_listings,
        property_types
    )

    # Should exclude condo (listing 5)
    assert len(filtered) == 4
    assert all(l.property_type in property_types for l in filtered)


def test_complete_filtering(listing_filter, sample_listings):
    """Test complete filtering pipeline"""
    property_types = ['single_family', 'multi_family']

    filtered = listing_filter.filter_listings(
        sample_listings,
        property_types
    )

    # Only listing 1 should pass all filters:
    # - Price in range
    # - Lot size >= 8000
    # - Property type = single_family
    assert len(filtered) == 1
    assert filtered[0].listing_id == "1"


def test_filter_summary(listing_filter):
    """Test filter summary generation"""
    summary = listing_filter.get_filter_summary()

    assert "400,000" in summary
    assert "5,000,000" in summary
    assert "8,000" in summary
