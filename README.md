# 🏡 House Search MLS Monitor

Backend service to monitor MLS listings for single and multifamily properties in coastal San Diego zipcodes, with email notifications for new listings.

## Features

- **Multi-API Integration**: Combines 3 free API tiers for zero API costs
  - RentCast API: 50 calls/month
  - RapidAPI US Real Estate: 100 calls/month
  - Homesage.ai: 500 credits/month
- **Smart Filtering**: Lot size ≥ 8,000 sqft, price range, property type
- **Automated Checks**: Daily monitoring (8 AM & 6 PM)
- **Email Alerts**: Beautiful HTML emails for new listings via Resend
- **Deduplication**: Intelligent merging of listings across APIs
- **Persistent Storage**: JSON-based with automatic backups
- **Quota Tracking**: Monitors API usage to stay within free tiers

## Architecture

```
┌───────────────────────────────────────────────┐
│    MLS Monitor Service (Multi-API Free)       │
├───────────────────────────────────────────────┤
│                                               │
│         ┌───────────────────┐                │
│         │    Scheduler      │                │
│         │ (Daily: 8am, 6pm) │                │
│         └─────────┬─────────┘                │
│                   ↓                            │
│         ┌───────────────────┐                │
│         │  API Router       │                │
│         │ (Rotate 3 APIs)   │                │
│         └─────────┬─────────┘                │
│                   ↓                            │
│    ┌──────────────┼──────────────┐           │
│    ↓              ↓               ↓           │
│ ┌────────┐  ┌──────────┐  ┌──────────┐      │
│ │RentCast│  │ RapidAPI │  │Homesage  │      │
│ │50/month│  │100/month │  │500/month │      │
│ └────┬───┘  └─────┬────┘  └─────┬────┘      │
│      │            │              │            │
│      └────────────┼──────────────┘            │
│                   ↓                            │
│         ┌───────────────────┐                │
│         │   Aggregator &    │                │
│         │  Deduplicator     │                │
│         └─────────┬─────────┘                │
│                   ↓                            │
│         ┌───────────────────┐                │
│         │   Comparator      │                │
│         │  (Find New)       │                │
│         └─────────┬─────────┘                │
│                   ↓                            │
│         ┌───────────────────┐                │
│         │ Email Notifier    │                │
│         │  (Resend API)     │                │
│         └───────────────────┘                │
└───────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Local Development

```bash
# Run setup script
./scripts/setup_local.sh

# Activate virtual environment
source venv/bin/activate

# Edit .env with your API keys
cp .env.example .env
nano .env

# Run the service
python -m app.main
```

The service will start on `http://localhost:8000`

### Option 2: Docker

```bash
# Build image
docker build -t house-search .

# Run container
docker run -d \
  --name house-search \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  house-search
```

### Option 3: Railway Deployment

1. Push code to GitHub
2. Connect Railway to your repository
3. Add environment variables in Railway dashboard
4. Deploy automatically

Cost: $5/month for always-on service

## Configuration

### Environment Variables (.env)

```bash
# API Keys (get from respective providers)
RENTCAST_API_KEY=your_rentcast_key
RAPIDAPI_KEY=your_rapidapi_key
HOMESAGE_API_KEY=your_homesage_key

# Email notifications (get from resend.com)
RESEND_API_KEY=re_your_resend_key
NOTIFICATION_EMAIL=your-email@example.com
FROM_EMAIL=notifications@yourdomain.com

# Schedule
CHECK_TIMES=08:00,18:00
TIMEZONE=America/Los_Angeles
LOG_LEVEL=INFO
```

### Search Criteria (config.yaml)

```yaml
zipcodes:
  priority:
    - '92037'  # La Jolla
    - '92109'  # Pacific Beach
    - '92107'  # Ocean Beach
    # ... more zipcodes

property_types:
  - single_family
  - multi_family

filters:
  min_price: 400000
  max_price: 5000000
  min_lot_size_sqft: 8000  # Critical: filters for lots ≥ 8000 sqft
```

## API Endpoints

### `GET /health`
Health check endpoint
```bash
curl http://localhost:8000/health
```

### `GET /status`
Get detailed service status
```json
{
  "scheduler_running": true,
  "total_listings": 45,
  "api_quotas": {
    "rentcast": {
      "used": 12,
      "limit": 50,
      "remaining": 38
    }
  }
}
```

### `POST /check-now`
Manually trigger a check
```bash
curl -X POST http://localhost:8000/check-now
```

### `GET /listings?limit=10&offset=0`
Get current listings with pagination

### `GET /quotas`
Get API quota status

## API Setup

### 1. RentCast API (50 calls/month free)

1. Sign up at [rentcast.io](https://rentcast.io)
2. Get API key from dashboard
3. Add to `.env` as `RENTCAST_API_KEY`

### 2. RapidAPI US Real Estate (100 calls/month free)

1. Sign up at [rapidapi.com](https://rapidapi.com)
2. Subscribe to "US Real Estate API"
3. Add to `.env` as `RAPIDAPI_KEY`

### 3. Homesage.ai (500 credits/month free)

1. Sign up at [homesage.ai](https://homesage.ai)
2. Get API key from dashboard
3. Add to `.env` as `HOMESAGE_API_KEY`

### 4. Resend Email (100 emails/day free)

1. Sign up at [resend.com](https://resend.com)
2. Verify your domain or use test mode
3. Add API key to `.env` as `RESEND_API_KEY`

## How It Works

### Daily Check Cycle

1. **Schedule**: Runs at 8:00 AM and 6:00 PM daily
2. **Fetch**: Queries all zipcodes using available API quota
3. **Aggregate**: Combines results from multiple APIs
4. **Deduplicate**: Removes duplicate properties
5. **Filter**: Applies lot size (≥ 8000 sqft), price, property type filters
6. **Compare**: Identifies new listings vs stored data
7. **Store**: Saves to JSON with daily backups
8. **Notify**: Sends email with new listings

### Quota Management

- Tracks usage for each API monthly
- Automatically resets on 1st of each month
- Routes requests to API with most remaining quota
- Warns if quota running low

### Deduplication Strategy

Same property may appear in multiple APIs. The system:
- Normalizes addresses (e.g., "Street" → "St")
- Groups by address + zipcode
- Selects version with most complete data
- Prioritizes listings with lot size and MLS data

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_storage.py
```

## Local Deployment (Free Alternative)

Instead of Railway, run locally using cron:

```bash
# Setup cron jobs
./scripts/setup_cron.sh

# This creates jobs for 8 AM and 6 PM checks
# Total cost: $0/month
```

## Monitoring

### View Logs

```bash
# Docker
docker logs house-search -f

# Local
tail -f logs/app.log

# Railway
Use Railway dashboard logs viewer
```

### Check Quota Status

```bash
curl http://localhost:8000/quotas
```

### Verify Storage

```bash
# Check listings file
cat data/listings.json | python -m json.tool

# Check backups
ls -lh data/backups/
```

## Cost Summary

| Service | Monthly Cost |
|---------|--------------|
| RentCast API | $0 (free tier) |
| RapidAPI | $0 (free tier) |
| Homesage API | $0 (free tier) |
| Resend Email | $0 (free tier) |
| **Local Deployment** | **$0** |
| **Railway Deployment** | **$5** |

**Total: $0-5/month** depending on deployment choice

## Upgrading

If you need more frequent checks or higher limits:

- **RentCast**: Upgrade to $15-30/month for more calls
- **Railway**: Stays at $5/month regardless of usage
- **Resend**: Stays free up to 3,000 emails/month

## Troubleshooting

### No Emails Received

1. Check Resend API key is valid
2. Verify email address in `.env`
3. Check spam folder
4. View logs for email errors

### API Quota Exceeded

1. Check quota status: `curl localhost:8000/quotas`
2. Wait for monthly reset (1st of month)
3. Consider upgrading API tier
4. Reduce number of zipcodes

### No New Listings

This is normal! The service only notifies when:
- A property is truly new (not previously seen)
- It matches all filters (lot size ≥ 8000 sqft, price range, property type)

Check `data/listings.json` to see all tracked properties.

## Project Structure

```
house-search/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration loader
│   ├── scheduler.py         # Scheduling logic
│   ├── services/
│   │   ├── api_router.py   # API request router
│   │   ├── rentcast_client.py
│   │   ├── rapidapi_client.py
│   │   ├── homesage_client.py
│   │   ├── aggregator.py   # Deduplication
│   │   ├── filters.py      # Filtering logic
│   │   ├── comparator.py   # Change detection
│   │   └── notifier.py     # Email sending
│   ├── models/
│   │   ├── listing.py      # Data models
│   │   └── config_model.py
│   └── utils/
│       └── logging_config.py
├── data/                    # Persistent storage
│   ├── listings.json
│   └── backups/
├── tests/                   # Unit tests
├── scripts/                 # Setup scripts
├── config.yaml              # Search configuration
├── .env                     # Secrets (not in git)
├── requirements.txt
├── Dockerfile
└── README.md
```

## Contributing

This is a personal project, but feel free to fork and customize for your own needs!

## License

MIT License - use freely for personal or commercial purposes.

---

Built with ❤️ for finding the perfect San Diego coastal property
# Railway Deployment Wed Jan 28 09:20:32 PST 2026
