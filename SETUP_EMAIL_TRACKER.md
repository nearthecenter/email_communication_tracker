# Email Communication Tracker Setup Guide

This guide will help you set up the email communication tracker system for the Onit Workspace.

## Features

- **Automatic Email Reading**: Reads unread emails from your Gmail account
- **AI-based Categorization**: Automatically categorizes emails (Sales, Support, HR, etc.)
- **Intelligent Auto-Reply**: Matches emails to answers in a Google Drive .docx file
- **Google Sheets Logging**: Logs all email activities to a Google Sheet
- **Web Dashboard**: Beautiful dashboard showing email statistics and status
- **Hourly Automation**: Checks and processes emails every hour

## Prerequisites

1. **Python 3.10+** installed
2. **Google Cloud Project** with the following APIs enabled:
   - Gmail API
   - Google Drive API
   - Google Sheets API
3. **Google Workspace** account (for Gmail, Drive, and Sheets access)

## Step 1: Set Up Google Cloud Project

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Enter project name (e.g., "Email Tracker")
4. Click "Create"

### 1.2 Enable Required APIs

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable these APIs:
   - **Gmail API**: Click "Enable"
   - **Google Drive API**: Click "Enable"
   - **Google Sheets API**: Click "Enable"

### 1.3 Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop application"
4. Name it (e.g., "Email Tracker")
5. Click "Create"
6. Download the JSON file and save it as `credentials.json` in your project root

## Step 2: Prepare Your Documents

### 2.1 Create Answers Document

1. Open Google Drive
2. Create a new Google Doc (or upload a .docx file)
3. Add question-answer pairs or FAQs
4. Name it exactly: **"Email Responses.docx"** (or modify the config)
5. Share it so that your Gmail account has access

Example content structure:
```
FREQUENTLY ASKED QUESTIONS

Q: What is your return policy?
A: We accept returns within 30 days of purchase. Items must be in original condition.

Q: How do I track my order?
A: You can track your order using the tracking number sent to your email.
```

### 2.2 Create Google Sheet for Logging

1. Open Google Sheets
2. Create a new spreadsheet
3. Name it (e.g., "Email Tracker Logs")
4. Copy the Spreadsheet ID from the URL: `docs.google.com/spreadsheets/d/{SPREADSHEET_ID}`
5. Update `SPREADSHEET_ID` in `config.py`

## Step 3: Install Dependencies

```bash
# Using pip
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-docx fastapi uvicorn apscheduler

# Or using the onit project's requirements
pip install -e ".[email-tracker]" --upgrade
```

## Step 4: Configure Email Tracker

### 4.1 Update Configuration File

Edit `src/email_tracker/config.py`:

```python
# Add your Google Sheets ID
SPREADSHEET_ID = "1234567890abcdefghijklmnop"

# Name of your answers document
DOC_FILE_NAME = "Email Responses.docx"

# Dashboard port
DASHBOARD_PORT = 8000

# Email check interval (in minutes)
EMAIL_CHECK_INTERVAL_MINUTES = 60
```

### 4.2 Place Credentials File

1. Make sure `credentials.json` is in your project root directory
2. First run will prompt you to authenticate with Google

## Step 5: Run the System

### Option A: Run Scheduler Only

```bash
python -m email_tracker.app
```

This will start the email scheduler that checks every hour.

### Option B: Run Dashboard Only

```python
from email_tracker import EmailTrackerApp

app = EmailTrackerApp(
    spreadsheet_id="YOUR_SPREADSHEET_ID",
    doc_file_name="Email Responses.docx"
)

app.start_dashboard()  # Visits http://localhost:8000
```

### Option C: Run Both (Recommended)

Create a script `run_email_tracker.py`:

```python
import asyncio
import threading
import logging
from email_tracker import EmailTrackerApp

logging.basicConfig(level=logging.INFO)

async def run_scheduler(app):
    await app.start_scheduler(interval_minutes=60)

def main():
    app = EmailTrackerApp(
        spreadsheet_id="YOUR_SPREADSHEET_ID",
        doc_file_name="Email Responses.docx",
        dashboard_port=8000
    )
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(
        target=lambda: asyncio.run(run_scheduler(app)),
        daemon=True
    )
    scheduler_thread.start()
    
    # Start dashboard (blocks)
    app.start_dashboard()

if __name__ == "__main__":
    main()
```

Then run:
```bash
python run_email_tracker.py
```

## Step 6: Access the Dashboard

Open your browser and visit:
```
http://localhost:8000
```

You'll see a beautiful dashboard showing:
- **Incoming**: New emails received
- **Pending**: Emails being processed
- **Auto Answered**: Emails with auto-replies sent
- **Manual Reply**: Emails needing manual response
- **Done**: Completed emails

## How It Works

### Email Processing Flow

1. **Check**: Scheduler checks Gmail for unread emails every hour
2. **Categorize**: AI categorizes each email (Sales, Support, etc.)
3. **Match**: System searches for matching answers in the .docx file
4. **Reply**: If match found (≥40% confidence), auto-reply is sent
5. **Log**: All activity is logged to Google Sheets
6. **Dashboard**: Statistics are displayed in real-time

### Email Status Lifecycle

```
Incoming → Pending → (Auto Answered/Manual Reply) → Done
                              ↓
                         Logged to Sheets
                         Shown in Dashboard
```

## Configuration Options

Edit `src/email_tracker/config.py` to customize:

| Option | Default | Description |
|--------|---------|-------------|
| `SPREADSHEET_ID` | Required | Google Sheets ID for logging |
| `DOC_FILE_NAME` | Email Responses.docx | Google Drive .docx filename |
| `DASHBOARD_PORT` | 8000 | Web dashboard port |
| `EMAIL_CHECK_INTERVAL_MINUTES` | 60 | Check emails every N minutes |
| `SIMILARITY_THRESHOLD` | 0.4 | Min similarity for auto-reply (0-1) |

## Troubleshooting

### "Authorization required" error
- Solution: Delete `token.pickle` files and run again to re-authenticate

### "File not found" in Google Drive
- Solution: Verify the .docx filename matches exactly in Google Drive and config
- Check that the file is shared/accessible to your account

### No emails being processed
- Solution: Check that emails in Gmail are actually unread
- Verify Gmail API is enabled in Google Cloud Console
- Check logs for authentication errors

### Dashboard not loading
- Solution: Verify port 8000 is not in use (or change DASHBOARD_PORT)
- Check that FastAPI is installed: `pip install fastapi uvicorn`

### Auto-replies too aggressive or not frequent enough
- Adjust `SIMILARITY_THRESHOLD` in config (lower = more matches)
- Adjust `EMAIL_CHECK_INTERVAL_MINUTES` (lower = more frequent checks)

## Advanced Usage

### Custom Email Categories

Edit the categorizer to add custom categories:

```python
from email_tracker import EmailCategorizer

categorizer = EmailCategorizer()

# Add custom category
categorizer.add_custom_category(
    "VIP Customers",
    ["vip", "premium", "enterprise", "gold"]
)

# Get all categories
categories = categorizer.get_categories()
```

### Adjust Response Matching Sensitivity

```python
from email_tracker import ResponseMatcher

# Lower threshold = more matches (more false positives)
# Higher threshold = fewer matches (fewer false positives)
matcher = ResponseMatcher(similarity_threshold=0.3)  # More sensitive
matcher = ResponseMatcher(similarity_threshold=0.6)  # Less sensitive
```

### Process Emails Immediately

Instead of waiting for the hourly scheduler:

```python
import asyncio
from email_tracker import EmailTrackerApp

app = EmailTrackerApp(
    spreadsheet_id="YOUR_SPREADSHEET_ID"
)

# Process immediately
asyncio.run(app.process_emails_immediately())
```

## Integration with Onit

The email tracker can be integrated into the Onit workspace as a tool:

```python
from src.email_tracker import EmailTrackerApp

# Define as a tool in Onit
email_tracker_tool = {
    "name": "email_tracker",
    "description": "Process and track emails with auto-reply",
    "action": lambda: EmailTrackerApp(...).process_emails_immediately()
}
```

## Security Considerations

1. **Keep credentials.json private** - Never commit to version control
2. **Use environment variables** for sensitive data:
   ```python
   import os
   SPREADSHEET_ID = os.getenv("EMAIL_TRACKER_SPREADSHEET_ID")
   ```

3. **Limit auto-reply scope** - Only reply to certain categories
4. **Review responses** - Moderate the .docx answers regularly
5. **Monitor logs** - Check Google Sheets for unexpected patterns

## Support & Debugging

For detailed logs:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## Next Steps

1. ✅ Set up Google Cloud Project
2. ✅ Enable APIs
3. ✅ Create credentials
4. ✅ Prepare documents
5. ✅ Install dependencies
6. ✅ Configure settings
7. ✅ Run the system
8. ✅ Access dashboard
9. ⚙️ Fine-tune settings based on results
10. 📊 Monitor performance in dashboard

Happy automating! 🚀
