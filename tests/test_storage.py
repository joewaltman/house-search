import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from app.services.storage import StorageManager
from app.models.listing import Listing


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    storage = StorageManager(data_dir=temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_listing():
    """Create a sample listing for testing"""
    return Listing(
        listing_id="test123",
        address="123 Main St",
        city="San Diego",
        zipcode="92037",
        price=1500000,
        bedrooms=3,
        bathrooms=2.5,
        sqft=2000,
        lot_size_sqft=8500,
        property_type="single_family",
        source_api="rentcast"
    )


def test_storage_initialization(temp_storage):
    """Test storage manager initialization creates directories"""
    assert temp_storage.data_dir.exists()
    assert temp_storage.backups_dir.exists()


def test_save_and_load_listings(temp_storage, sample_listing):
    """Test saving and loading listings"""
    listings = {"test123": sample_listing}

    # Save listings
    success = temp_storage.save_listings(listings)
    assert success
    assert temp_storage.listings_file.exists()

    # Load listings
    loaded = temp_storage.load_listings()
    assert len(loaded) == 1
    assert "test123" in loaded
    assert loaded["test123"].address == "123 Main St"
    assert loaded["test123"].price == 1500000


def test_load_empty_storage(temp_storage):
    """Test loading from non-existent file returns empty dict"""
    listings = temp_storage.load_listings()
    assert isinstance(listings, dict)
    assert len(listings) == 0


def test_create_backup(temp_storage, sample_listing):
    """Test backup creation"""
    listings = {"test123": sample_listing}
    temp_storage.save_listings(listings)

    # Create backup
    backup_file = temp_storage.create_backup()
    assert backup_file is not None
    assert backup_file.exists()
    assert backup_file.parent == temp_storage.backups_dir


def test_api_quotas(temp_storage):
    """Test API quota tracking"""
    # Load initial quotas
    quotas = temp_storage.load_api_quotas()
    assert 'rentcast' in quotas
    assert quotas['rentcast']['used'] == 0
    assert quotas['rentcast']['limit'] == 50

    # Increment quota
    temp_storage.increment_quota('rentcast', 5)

    # Verify increment
    quotas = temp_storage.load_api_quotas()
    assert quotas['rentcast']['used'] == 5


def test_listing_equality(sample_listing):
    """Test listing equality for deduplication"""
    listing2 = Listing(
        listing_id="different_id",
        address="123 Main St",  # Same address
        zipcode="92037",  # Same zipcode
        price=1500500,  # Similar price (within $1000)
        source_api="rapidapi"
    )

    # Should be equal for deduplication purposes
    assert sample_listing == listing2


def test_listing_hash(sample_listing):
    """Test listing hashing for deduplication"""
    listing2 = Listing(
        listing_id="different_id",
        address="123 MAIN ST",  # Case insensitive
        zipcode="92037",
        price=1500000,
        source_api="rapidapi"
    )

    # Should have same hash
    assert hash(sample_listing) == hash(listing2)
