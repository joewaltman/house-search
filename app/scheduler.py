from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List
import pytz

from app.config import settings, app_config, get_all_zipcodes
from app.services.storage import StorageManager
from app.services.api_router import APIRouter
from app.services.aggregator import Aggregator
from app.services.filters import ListingFilter
from app.services.comparator import Comparator
from app.services.notifier import EmailNotifier
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class MLSScheduler:
    """Schedules and orchestrates MLS listing checks"""

    def __init__(self):
        self.storage = StorageManager()
        self.api_router = APIRouter(self.storage)
        self.aggregator = Aggregator()
        self.filter = ListingFilter(app_config.filters)
        self.comparator = Comparator()
        self.notifier = EmailNotifier()
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Parse check times from config
        check_times = settings.check_times.split(',')
        timezone = pytz.timezone(settings.timezone)

        for check_time in check_times:
            hour, minute = map(int, check_time.strip().split(':'))

            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=timezone
            )

            self.scheduler.add_job(
                self.run_check,
                trigger=trigger,
                id=f'check_{hour:02d}_{minute:02d}',
                name=f'MLS Check at {check_time}',
                replace_existing=True
            )

            logger.info(f"Scheduled check at {check_time} {settings.timezone}")

        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")

    def run_check(self):
        """
        Run a complete MLS check cycle.

        Steps:
        1. Load existing listings from storage
        2. Fetch new listings from APIs for all zipcodes
        3. Aggregate and deduplicate results
        4. Apply filters (price, lot size, property type)
        5. Compare with existing to find new listings
        6. Merge with existing listings
        7. Save to storage
        8. Send email notifications for new listings
        """
        logger.info("=" * 80)
        logger.info("Starting MLS check cycle")
        logger.info("=" * 80)

        try:
            # Step 1: Load existing listings
            logger.info("Step 1: Loading existing listings")
            existing_listings = self.storage.load_listings()
            logger.info(f"Loaded {len(existing_listings)} existing listings")

            # Step 2: Fetch new listings from APIs
            logger.info("Step 2: Fetching listings from APIs")
            zipcodes = get_all_zipcodes(app_config)
            logger.info(f"Querying {len(zipcodes)} zipcodes: {', '.join(zipcodes)}")

            results_by_zipcode = self.api_router.fetch_all_zipcodes(
                zipcodes=zipcodes,
                property_types=app_config.property_types,
                min_price=app_config.filters.min_price,
                max_price=app_config.filters.max_price
            )

            # Step 3: Aggregate and deduplicate
            logger.info("Step 3: Aggregating and deduplicating")
            all_listings = self.aggregator.aggregate_and_deduplicate(results_by_zipcode)

            # Step 4: Apply filters
            logger.info("Step 4: Applying filters")
            logger.info(f"Filter criteria: {self.filter.get_filter_summary()}")
            filtered_listings = self.filter.filter_listings(
                all_listings,
                app_config.property_types
            )

            # Convert to dict for comparison
            current_listings_dict = {
                listing.listing_id: listing
                for listing in filtered_listings
            }

            # Step 5: Find new listings
            logger.info("Step 5: Comparing with existing listings")
            new_listings = self.comparator.find_new_listings(
                current_listings_dict,
                existing_listings
            )

            # Get summary stats
            stats = self.comparator.get_summary_stats(
                current_listings_dict,
                existing_listings
            )
            logger.info(f"Summary: {stats}")

            # Step 6: Merge with existing
            logger.info("Step 6: Merging with existing listings")
            merged_listings = self.aggregator.merge_with_existing(
                filtered_listings,
                existing_listings
            )

            # Step 7: Save to storage
            logger.info("Step 7: Saving to storage")
            self.storage.save_listings(merged_listings)
            self.storage.create_backup()

            # Step 8: Send notifications
            if new_listings:
                logger.info(f"Step 8: Sending email notification for {len(new_listings)} new listings")
                self.notifier.send_new_listings_email(new_listings)
            else:
                logger.info("Step 8: No new listings to notify")

            # Log quota status
            quota_status = self.api_router.get_quota_status()
            logger.info("API Quota Status:")
            for api_name, status in quota_status.items():
                logger.info(
                    f"  {api_name}: {status['used']}/{status['limit']} "
                    f"({status['percentage']}% used, {status['remaining']} remaining)"
                )

            logger.info("=" * 80)
            logger.info("MLS check cycle completed successfully")
            logger.info("=" * 80)

        except Exception as e:
            error_msg = f"Error during MLS check: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Send error notification
            try:
                self.notifier.send_error_notification(error_msg)
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")

    def get_status(self) -> dict:
        """Get current scheduler status"""
        listings = self.storage.load_listings()
        quota_status = self.api_router.get_quota_status()

        jobs = []
        if self.scheduler.running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                })

        return {
            'scheduler_running': self.is_running,
            'total_listings': len(listings),
            'scheduled_jobs': jobs,
            'api_quotas': quota_status,
            'check_times': settings.check_times,
            'timezone': settings.timezone
        }
