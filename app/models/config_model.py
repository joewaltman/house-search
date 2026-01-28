from typing import List, Optional
from pydantic import BaseModel


class ZipcodesConfig(BaseModel):
    """Zipcode configuration"""
    priority: List[str]
    additional: List[str] = []


class FiltersConfig(BaseModel):
    """Property filtering criteria"""
    min_price: int = 400000
    max_price: int = 5000000
    min_lot_size_sqft: int = 8000
    max_longitude: Optional[float] = None  # Filter for ocean proximity


class AppConfig(BaseModel):
    """Application configuration from YAML"""
    zipcodes: ZipcodesConfig
    property_types: List[str]
    filters: FiltersConfig
