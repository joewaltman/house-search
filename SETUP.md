# Setup Guide

This guide will walk you through setting up the House Search MLS Monitor from scratch.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- A terminal/command line

## Step-by-Step Setup

### 1. Clone or Download the Project

If you have the project files, navigate to the directory:

```bash
cd house-search
```

### 2. Run the Setup Script

```bash
chmod +x scripts/setup_local.sh
./scripts/setup_local.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Copy `.env.example` to `.env`

### 3. Get API Keys

You need to sign up for these free services:

#### A. RentCast API (50 calls/month free)

1. Go to https://app.rentcast.io/app/signup
2. Create a free account
3. Navigate to API Keys section
4. Copy your API key

#### B. RapidAPI US Real Estate (100 calls/month free)

1. Go to https://rapidapi.com/auth/sign-up
2. Create a free account
3. Search for "US Real Estate" API
4. Subscribe to the free tier
5. Copy your API key from the "Code Snippets" section

#### C. Homesage.ai (500 credits/month free)

1. Go to https://homesage.ai/signup
2. Create a free account
3. Navigate to API section in dashboard
4. Copy your API key

#### D. Resend Email (100 emails/day free)

1. Go to https://resend.com/signup
2. Create a free account
3. Add and verify your email domain (or use test mode)
4. Create an API key
5. Copy the API key

### 4. Configure Environment Variables

Edit the `.env` file:

```bash
nano .env
# or
code .env
```

Fill in your API keys:

```bash
RENTCAST_API_KEY=your_actual_key_here
RAPIDAPI_KEY=your_actual_key_here
HOMESAGE_API_KEY=your_actual_key_here
RESEND_API_KEY=re_your_actual_key_here
NOTIFICATION_EMAIL=youremail@example.com
FROM_EMAIL=noreply@yourdomain.com
```

### 5. Customize Search Criteria (Optional)

Edit `config.yaml` to customize:
- Which zipcodes to monitor
- Price range
- Minimum lot size
- Property types

```bash
nano config.yaml
```

### 6. Test the Setup

Activate the virtual environment:

```bash
source venv/bin/activate
```

Run a test check:

```bash
python -m app.main &
sleep 5
curl -X POST http://localhost:8000/check-now
```

Check the logs to verify it's working:

```bash
tail -f logs/app.log
```

### 7. Choose Deployment Method

#### Option A: Run as a Service (Railway - $5/month)

1. Push code to GitHub
2. Sign up at https://railway.app
3. Create new project from GitHub repo
4. Add environment variables in Railway dashboard
5. Deploy

#### Option B: Run Locally with Cron (Free)

Set up cron jobs to run checks automatically:

```bash
./scripts/setup_cron.sh
```

Follow the instructions to add the cron jobs.

#### Option C: Run Manually

Just start the service when you want:

```bash
source venv/bin/activate
python -m app.main
```

## Verification

### Check Service Status

```bash
curl http://localhost:8000/status
```

### View Current Listings

```bash
curl http://localhost:8000/listings
```

### Check API Quotas

```bash
curl http://localhost:8000/quotas
```

### Trigger Manual Check

```bash
curl -X POST http://localhost:8000/check-now
```

## Next Steps

1. **Monitor for a Day**: Let it run for 24 hours to verify everything works
2. **Check Email**: Verify you receive notifications (may take time for new listings)
3. **Adjust Filters**: Modify `config.yaml` if needed based on results
4. **Set Up Monitoring**: Consider setting up uptime monitoring if using Railway

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Import Errors

Make sure you're in the project directory and virtual environment is activated:

```bash
pwd  # Should show house-search directory
which python  # Should show venv/bin/python
```

### API Connection Issues

Test each API individually:

```python
from app.services.rentcast_client import RentCastClient
from app.config import settings

client = RentCastClient(settings.rentcast_api_key)
listings = client.fetch_listings('92037', ['single_family'])
print(f"Found {len(listings)} listings")
```

### Email Not Sending

1. Verify Resend API key is correct
2. Check if domain is verified (or use test mode)
3. Check spam folder
4. View detailed logs: `tail -f logs/app.log`

## Getting Help

- Check README.md for general documentation
- Review logs in `logs/app.log`
- Check data files in `data/` directory
- Review test output: `pytest -v`

## Maintenance

### Update Dependencies

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Clear Old Backups

```bash
# Backups older than 7 days are auto-deleted
# To manually clean:
find data/backups -name "*.json" -mtime +7 -delete
```

### Reset Listings

To start fresh:

```bash
rm data/listings.json
rm data/api_quotas.json
# Next check will be treated as first run
```
