#!/usr/bin/env python3
"""
Test script to verify API connections and credentials.
Run this after setting up .env to ensure all APIs are accessible.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.rentcast_client import RentCastClient
from app.services.rapidapi_client import RapidAPIClient
from app.services.homesage_client import HomesageClient
from app.utils.logging_config import setup_logging

logger = setup_logging()


def test_api(name, client, test_zipcode='92037'):
    """Test an API client"""
    print(f"\n{'='*60}")
    print(f"Testing {name} API")
    print(f"{'='*60}")

    try:
        print(f"Fetching listings for zipcode {test_zipcode}...")
        listings = client.fetch_listings(
            zipcode=test_zipcode,
            property_types=['single_family', 'multi_family']
        )

        print(f"✓ Success! Found {len(listings)} listings")

        if listings:
            sample = listings[0]
            print(f"\nSample listing:")
            print(f"  Address: {sample.address}")
            print(f"  Price: ${sample.price:,}")
            print(f"  Lot Size: {sample.lot_size_sqft or 'N/A'} sqft")
            print(f"  Source: {sample.source_api}")

        return True

    except Exception as e:
        print(f"✗ Failed: {str(e)}")
        return False


def main():
    """Test all API connections"""
    print("🏡 House Search API Connection Test")
    print("="*60)

    results = {}

    # Test RentCast
    if settings.rentcast_api_key:
        client = RentCastClient(settings.rentcast_api_key)
        results['RentCast'] = test_api('RentCast', client)
    else:
        print("\n⚠️  RentCast API key not configured")
        results['RentCast'] = False

    # Test RapidAPI
    if settings.rapidapi_key:
        client = RapidAPIClient(settings.rapidapi_key)
        results['RapidAPI'] = test_api('RapidAPI', client)
    else:
        print("\n⚠️  RapidAPI key not configured")
        results['RapidAPI'] = False

    # Test Homesage
    if settings.homesage_api_key:
        client = HomesageClient(settings.homesage_api_key)
        results['Homesage'] = test_api('Homesage', client)
    else:
        print("\n⚠️  Homesage API key not configured")
        results['Homesage'] = False

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")

    for api_name, success in results.items():
        status = "✓ Working" if success else "✗ Failed"
        print(f"{api_name}: {status}")

    working_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    print(f"\n{working_count}/{total_count} APIs working")

    if working_count == 0:
        print("\n⚠️  Warning: No APIs are working!")
        print("Please check your API keys in .env file")
        sys.exit(1)
    elif working_count < total_count:
        print("\n⚠️  Some APIs failed. Service will work with reduced capacity.")
    else:
        print("\n✓ All APIs working! Ready to monitor listings.")


if __name__ == "__main__":
    main()
