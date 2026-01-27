from typing import List, Optional
import resend
from app.models.listing import Listing
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class EmailNotifier:
    """Sends email notifications for new listings using Resend API"""

    def __init__(self):
        self.api_key = settings.resend_api_key
        self.from_email = settings.from_email
        self.to_email = settings.notification_email

        if self.api_key:
            resend.api_key = self.api_key

    def send_new_listings_email(self, listings: List[Listing]) -> bool:
        """
        Send email notification with new listings.

        Args:
            listings: List of new listings to include in email

        Returns:
            True if email sent successfully, False otherwise
        """
        if not listings:
            logger.info("No new listings to send")
            return True

        if not self.api_key:
            logger.warning("Resend API key not configured, skipping email")
            return False

        try:
            subject = self._generate_subject(listings)
            html_body = self._generate_html_body(listings)

            params = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_body
            }

            response = resend.Emails.send(params)
            logger.info(f"Email sent successfully to {self.to_email}: {response}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def _generate_subject(self, listings: List[Listing]) -> str:
        """Generate email subject line"""
        count = len(listings)

        if count == 1:
            listing = listings[0]
            return f"New Listing Alert: {listing.address} - ${listing.price:,}"
        else:
            total_value = sum(l.price for l in listings)
            avg_price = total_value // count
            return f"{count} New Listings in San Diego Coastal Areas (avg ${avg_price:,})"

    def _generate_html_body(self, listings: List[Listing]) -> str:
        """Generate HTML email body"""
        # Sort by price (ascending)
        sorted_listings = sorted(listings, key=lambda x: x.price)

        # Generate listing cards
        listing_cards = []
        for listing in sorted_listings:
            card = self._generate_listing_card(listing)
            listing_cards.append(card)

        listings_html = "\n".join(listing_cards)

        # Full HTML email
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .container {{
            background: white;
            padding: 20px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .listing-card {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 20px 0;
            overflow: hidden;
            transition: box-shadow 0.3s;
        }}
        .listing-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .listing-image {{
            width: 100%;
            height: 300px;
            object-fit: cover;
            background-color: #f0f0f0;
        }}
        .listing-content {{
            padding: 20px;
        }}
        .listing-price {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0 0 10px 0;
        }}
        .listing-address {{
            font-size: 18px;
            color: #555;
            margin: 0 0 15px 0;
        }}
        .listing-details {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
        }}
        .detail-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .detail-label {{
            font-weight: 600;
            color: #666;
        }}
        .detail-value {{
            color: #333;
        }}
        .lot-size {{
            background-color: #e3f2fd;
            padding: 8px 12px;
            border-radius: 4px;
            font-weight: 600;
            color: #1976d2;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin-top: 15px;
        }}
        .cta-button:hover {{
            opacity: 0.9;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }}
        .badge-api {{
            background-color: #e8f5e9;
            color: #2e7d32;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏡 New Property Listings Alert</h1>
        <p>San Diego Coastal Areas | Lot Size ≥ 8,000 sq ft</p>
    </div>

    <div class="container">
        <p>Great news! We found <strong>{len(listings)} new listing{'s' if len(listings) != 1 else ''}</strong> matching your criteria:</p>

        {listings_html}

        <div class="footer">
            <p>This is an automated notification from your House Search monitor.</p>
            <p>Checking daily at 8:00 AM and 6:00 PM Pacific Time.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_listing_card(self, listing: Listing) -> str:
        """Generate HTML for a single listing card"""
        # Format details
        beds = f"{listing.bedrooms} beds" if listing.bedrooms else "N/A"
        baths = f"{listing.bathrooms} baths" if listing.bathrooms else "N/A"
        sqft = f"{listing.sqft:,} sq ft" if listing.sqft else "N/A"
        lot_size = f"{listing.lot_size_sqft:,} sq ft" if listing.lot_size_sqft else "N/A"
        year = str(listing.year_built) if listing.year_built else "N/A"

        # Image section
        image_html = ""
        if listing.photo_url:
            image_html = f'<img src="{listing.photo_url}" alt="{listing.address}" class="listing-image">'
        else:
            image_html = '<div class="listing-image" style="display: flex; align-items: center; justify-content: center; color: #999;">No image available</div>'

        # Link
        view_link = listing.listing_url or "#"

        # Description snippet
        description = ""
        if listing.description:
            snippet = listing.description[:200] + "..." if len(listing.description) > 200 else listing.description
            description = f'<p style="color: #666; margin: 10px 0;">{snippet}</p>'

        card = f"""
        <div class="listing-card">
            {image_html}
            <div class="listing-content">
                <div class="listing-price">
                    ${listing.price:,}
                    <span class="badge badge-api">{listing.source_api}</span>
                </div>
                <div class="listing-address">{listing.address}, {listing.city or ''} {listing.zipcode}</div>

                <div class="listing-details">
                    <div class="detail-item">
                        <span class="detail-label">🛏️ Beds:</span>
                        <span class="detail-value">{beds}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">🚿 Baths:</span>
                        <span class="detail-value">{baths}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">📐 Size:</span>
                        <span class="detail-value">{sqft}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">📅 Built:</span>
                        <span class="detail-value">{year}</span>
                    </div>
                </div>

                <div class="lot-size">
                    📏 Lot Size: {lot_size}
                </div>

                {description}

                <a href="{view_link}" class="cta-button">View Full Details →</a>
            </div>
        </div>
        """

        return card

    def send_error_notification(self, error_message: str) -> bool:
        """Send email notification about errors"""
        if not self.api_key:
            logger.warning("Cannot send error notification: API key not configured")
            return False

        try:
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .error-box {{
            background-color: #fee;
            border-left: 4px solid #c33;
            padding: 20px;
            border-radius: 4px;
        }}
        .error-title {{
            color: #c33;
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <div class="error-title">⚠️ House Search Monitor Error</div>
        <p>{error_message}</p>
        <p style="color: #666; font-size: 14px; margin-top: 15px;">
            This is an automated error notification. Please check the application logs for more details.
        </p>
    </div>
</body>
</html>
"""

            params = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": "🚨 House Search Monitor Error",
                "html": html
            }

            resend.Emails.send(params)
            logger.info("Error notification email sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
