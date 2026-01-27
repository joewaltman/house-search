import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from app.models.listing import Listing
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class StorageManager:
    """Manages persistent storage of listings in JSON format"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.backups_dir = self.data_dir / "backups"
        self.listings_file = self.data_dir / "listings.json"
        self.quota_file = self.data_dir / "api_quotas.json"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def load_listings(self) -> Dict[str, Listing]:
        """Load listings from JSON file"""
        if not self.listings_file.exists():
            logger.info("No existing listings file found, starting fresh")
            return {}

        try:
            with open(self.listings_file, 'r') as f:
                data = json.load(f)

            listings = {}
            for listing_id, listing_data in data.get('listings', {}).items():
                try:
                    # Parse datetime strings
                    if 'first_seen' in listing_data:
                        listing_data['first_seen'] = datetime.fromisoformat(
                            listing_data['first_seen']
                        )
                    if 'last_updated' in listing_data:
                        listing_data['last_updated'] = datetime.fromisoformat(
                            listing_data['last_updated']
                        )

                    listings[listing_id] = Listing(**listing_data)
                except Exception as e:
                    logger.error(f"Error parsing listing {listing_id}: {e}")
                    continue

            logger.info(f"Loaded {len(listings)} listings from storage")
            return listings

        except Exception as e:
            logger.error(f"Error loading listings: {e}")
            return {}

    def save_listings(self, listings: Dict[str, Listing]) -> bool:
        """Save listings to JSON file with atomic write"""
        try:
            # Prepare data structure
            data = {
                'last_check': datetime.utcnow().isoformat(),
                'total_listings': len(listings),
                'listings': {}
            }

            # Convert listings to dict
            for listing_id, listing in listings.items():
                data['listings'][listing_id] = listing.model_dump(mode='json')

            # Atomic write: write to temp file, then rename
            temp_file = self.listings_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Rename temp file to actual file (atomic on POSIX systems)
            temp_file.replace(self.listings_file)

            logger.info(f"Saved {len(listings)} listings to storage")
            return True

        except Exception as e:
            logger.error(f"Error saving listings: {e}")
            return False

    def create_backup(self) -> Optional[Path]:
        """Create a daily backup of listings file"""
        if not self.listings_file.exists():
            logger.warning("No listings file to backup")
            return None

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backups_dir / f"listings_{timestamp}.json"

            shutil.copy2(self.listings_file, backup_file)
            logger.info(f"Created backup: {backup_file.name}")

            # Prune old backups
            self._prune_old_backups(keep_days=7)

            return backup_file

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None

    def _prune_old_backups(self, keep_days: int = 7):
        """Remove backups older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            for backup_file in self.backups_dir.glob("listings_*.json"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file.name}")

        except Exception as e:
            logger.error(f"Error pruning backups: {e}")

    def load_api_quotas(self) -> Dict[str, dict]:
        """Load API quota tracking data"""
        if not self.quota_file.exists():
            return self._init_quotas()

        try:
            with open(self.quota_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading quotas: {e}")
            return self._init_quotas()

    def save_api_quotas(self, quotas: Dict[str, dict]) -> bool:
        """Save API quota tracking data"""
        try:
            with open(self.quota_file, 'w') as f:
                json.dump(quotas, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving quotas: {e}")
            return False

    def _init_quotas(self) -> Dict[str, dict]:
        """Initialize quota tracking structure"""
        now = datetime.utcnow()
        return {
            'rentcast': {
                'used': 0,
                'limit': 50,
                'reset_date': now.replace(day=1).isoformat()
            },
            'rapidapi': {
                'used': 0,
                'limit': 100,
                'reset_date': now.replace(day=1).isoformat()
            },
            'homesage': {
                'used': 0,
                'limit': 500,
                'reset_date': now.replace(day=1).isoformat()
            }
        }

    def increment_quota(self, api_name: str, count: int = 1):
        """Increment API usage quota"""
        quotas = self.load_api_quotas()

        if api_name in quotas:
            quotas[api_name]['used'] += count
            self.save_api_quotas(quotas)
            logger.info(
                f"{api_name} quota: {quotas[api_name]['used']}/{quotas[api_name]['limit']}"
            )

    def reset_quotas_if_needed(self):
        """Reset quotas if we're in a new month"""
        quotas = self.load_api_quotas()
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for api_name, quota_data in quotas.items():
            reset_date = datetime.fromisoformat(quota_data['reset_date'])
            if reset_date < month_start:
                quotas[api_name]['used'] = 0
                quotas[api_name]['reset_date'] = month_start.isoformat()
                logger.info(f"Reset {api_name} quota for new month")

        self.save_api_quotas(quotas)
