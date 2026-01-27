from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Listing(BaseModel):
    """Represents a real estate listing from MLS"""

    # Unique identifier (can be MLS number, property ID, or generated hash)
    listing_id: str

    # Basic property info
    address: str
    city: Optional[str] = None
    state: Optional[str] = "CA"
    zipcode: str

    # Pricing
    price: int

    # Property details
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size_sqft: Optional[int] = None  # Critical for filtering
    year_built: Optional[int] = None

    # Property type
    property_type: Optional[str] = None  # single_family, multi_family, condo, etc.

    # Listing details
    status: str = "active"  # active, pending, sold
    listing_url: Optional[str] = None
    photo_url: Optional[str] = None

    # MLS/Source info
    mls_number: Optional[str] = None
    source_api: str  # rentcast, rapidapi, homesage

    # Tracking
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Additional features
    description: Optional[str] = None
    hoa_fee: Optional[int] = None
    parking_spaces: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def __hash__(self):
        """Hash based on address and price for deduplication"""
        return hash((self.address.lower(), self.zipcode, self.price))

    def __eq__(self, other):
        """Equality based on address and price for deduplication"""
        if not isinstance(other, Listing):
            return False
        return (
            self.address.lower() == other.address.lower() and
            self.zipcode == other.zipcode and
            abs(self.price - other.price) < 1000  # Allow small price differences
        )
