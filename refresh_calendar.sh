#!/bin/bash
# Quick script to refresh calendar from Outlook
# Downloads latest ICS, imports meetings, and regenerates dashboard

echo "📅 Refreshing calendar from Outlook..."
echo ""

# Navigate to Task-Manager directory
cd "$(dirname "$0")"

# Read calendar URL from .calendar_sync_url file
if [ -f ".calendar_sync_url" ]; then
    ICS_URL=$(cat .calendar_sync_url)
else
    echo "❌ Error: .calendar_sync_url file not found"
    echo "Please create this file with your Outlook calendar URL"
    exit 1
fi

# Download latest ICS file
echo "⬇️  Downloading latest calendar from Outlook..."
curl -s "$ICS_URL" -o calendar.ics

if [ $? -eq 0 ]; then
    echo "✅ Calendar downloaded successfully"
    echo ""
else
    echo "❌ Failed to download calendar"
    exit 1
fi

# Import meetings
echo "📥 Importing meetings to data/calendar.json..."
python3 src/import_ics_calendar.py
echo ""

# Regenerate dashboard
echo "🎨 Regenerating dashboard..."
python3 src/visualize_deadlines.py
echo ""

echo "🎉 Calendar refresh complete!"
echo ""
echo "💡 Next steps:"
echo "   - Open deadline_dashboard.html to see updated calendar"
echo "   - Review data/calendar.json for any manual annotations needed"
