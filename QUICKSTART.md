# Quick Start Guide

Get the House Search MLS Monitor running in 5 minutes.

## 1. Install Dependencies

```bash
# Run the setup script
./scripts/setup_local.sh

# Activate virtual environment
source venv/bin/activate
```

## 2. Configure API Keys

Edit `.env` file with your API keys:

```bash
RENTCAST_API_KEY=your_key
RAPIDAPI_KEY=your_key
HOMESAGE_API_KEY=your_key
RESEND_API_KEY=your_key
NOTIFICATION_EMAIL=your-email@example.com
```

Get free API keys from:
- RentCast: https://app.rentcast.io/app/signup
- RapidAPI: https://rapidapi.com/auth/sign-up
- Homesage: https://homesage.ai/signup
- Resend: https://resend.com/signup

## 3. Test API Connections

```bash
python scripts/test_apis.py
```

This will verify all APIs are working correctly.

## 4. Run the Service

```bash
python -m app.main
```

The service starts on http://localhost:8000

## 5. Trigger a Test Check

In a new terminal:

```bash
curl -X POST http://localhost:8000/check-now
```

Watch the logs to see it in action!

## 6. Check Results

```bash
# View status
curl http://localhost:8000/status

# View listings
curl http://localhost:8000/listings

# View API quota usage
curl http://localhost:8000/quotas

# Check stored data
cat data/listings.json | python -m json.tool
```

## Deployment Options

### Local with Cron (Free)

```bash
./scripts/setup_cron.sh
# Follow instructions to add cron jobs
```

### Railway ($5/month)

1. Push to GitHub
2. Connect to Railway
3. Add environment variables
4. Deploy

### Docker

```bash
docker build -t house-search .
docker run -d -p 8000:8000 --env-file .env house-search
```

## What Happens Next?

- Service checks for new listings at 8 AM and 6 PM daily
- New listings matching your criteria are emailed to you
- All listings are stored in `data/listings.json`
- Daily backups are created in `data/backups/`

## Customization

Edit `config.yaml` to change:
- Monitored zipcodes
- Price range ($400k - $5M default)
- Minimum lot size (8000 sqft default)
- Property types

## Need Help?

- Full docs: See `README.md`
- Detailed setup: See `SETUP.md`
- Run tests: `pytest -v`
- View logs: Check terminal output

## Common Commands

```bash
# Start service
python -m app.main

# Run tests
pytest

# Trigger manual check
curl -X POST http://localhost:8000/check-now

# View status
curl http://localhost:8000/status

# View quota usage
curl http://localhost:8000/quotas
```

That's it! 🎉 Your MLS monitor is now running.
