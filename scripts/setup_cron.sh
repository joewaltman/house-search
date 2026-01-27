#!/bin/bash
# Setup cron jobs for local deployment (alternative to Railway)

set -e

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SCRIPT_PATH="$PROJECT_DIR/scripts/run_check.sh"

echo "🏡 Setting up cron jobs for House Search Monitor"
echo "================================================"
echo "Project directory: $PROJECT_DIR"

# Create run script
cat > "$SCRIPT_PATH" << 'EOF'
#!/bin/bash
# Run a single MLS check

cd "$(dirname "$0")/.."
source venv/bin/activate

# Trigger manual check via API
curl -X POST http://localhost:8000/check-now

# Or run directly without API server:
# python -c "from app.scheduler import MLSScheduler; scheduler = MLSScheduler(); scheduler.run_check()"
EOF

chmod +x "$SCRIPT_PATH"
echo "✓ Created run script: $SCRIPT_PATH"

# Cron schedule: 8:00 AM and 6:00 PM
CRON_SCHEDULE_1="0 8 * * * $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1"
CRON_SCHEDULE_2="0 18 * * * $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1"

echo ""
echo "Add these lines to your crontab (run 'crontab -e'):"
echo ""
echo "$CRON_SCHEDULE_1"
echo "$CRON_SCHEDULE_2"
echo ""
echo "This will run checks at 8:00 AM and 6:00 PM daily."
echo ""
echo "To view current crontab: crontab -l"
echo "To edit crontab: crontab -e"
