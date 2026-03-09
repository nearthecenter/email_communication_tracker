# Email Communication Tracker for Onit

A complete automated email management system that reads emails from Gmail, categorizes them, auto-replies using answers from a Google Drive document, logs everything to Google Sheets, and provides a beautiful real-time dashboard.

## 🎯 Features

### 📧 Email Management
- **Automatic Email Reading**: Fetches unread emails from Gmail
- **Smart Categorization**: AI-based categorization (Sales, Support, HR, etc.)
- **Intelligent Auto-Reply**: Matches emails to answers using keyword matching
- **Status Tracking**: Tracks emails through their lifecycle

### 📊 Logging & Analytics
- **Google Sheets Integration**: All email activities logged automatically
- **Real-time Dashboard**: Beautiful web dashboard with live statistics
- **Email Statistics**: Track incoming, pending, answered, and completed emails

### 🤖 Automation
- **Hourly Processing**: Automatically checks and processes emails every hour
- **Intelligent Matching**: Keyword-based matching against answer document
- **No Manual Configuration**: Works with existing Gmail and Google Drive

## 📁 Project Structure

```
onit/
├── src/email_tracker/
│   ├── __init__.py                 # Package exports
│   ├── models.py                   # Data models (Email, EmailStatus, etc.)
│   ├── gmail_service.py            # Gmail API integration
│   ├── categorizer.py              # Email categorization
│   ├── doc_reader.py              # Google Drive .docx reader
│   ├── response_matcher.py        # Response matching engine
│   ├── sheets_logger.py           # Google Sheets logging
│   ├── scheduler.py               # Email processing scheduler
│   ├── app.py                     # Main application
│   ├── web/
│   │   └── __init__.py            # FastAPI dashboard
│   └── config.py                  # Configuration
├── run_email_tracker.py            # Main entry point
├── test_email_tracker_setup.py     # Installation verification
└── SETUP_EMAIL_TRACKER.md          # Detailed setup guide
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install email tracker dependencies
pip install -e ".[email-tracker]"

# Or install all (including other onit features)
pip install -e ".[all]"
```

### 2. Set Up Google Cloud

See [SETUP_EMAIL_TRACKER.md](SETUP_EMAIL_TRACKER.md) for detailed instructions:
1. Create Google Cloud Project
2. Enable Gmail, Drive, Sheets APIs
3. Create OAuth 2.0 credentials
4. Download credentials.json

### 3. Prepare Documents

- Create **Email Responses.docx** in Google Drive with Q&A pairs
- Create Google Sheet for logging (note the spreadsheet ID)

### 4. Configure

Edit `run_email_tracker.py`:
```python
SPREADSHEET_ID = "YOUR_GOOGLE_SHEETS_ID"  # Update this
```

### 5. Run

```bash
python run_email_tracker.py
```

Open dashboard: http://localhost:8000

## 📖 How It Works

### Email Processing Pipeline

```
Gmail (unread emails)
    ↓
Categorizer (detect category)
    ↓
Doc Reader (load answers from Drive)
    ↓
Response Matcher (keyword matching)
    ↓
If match found → Send auto-reply
If no match → Mark for manual reply
    ↓
Sheets Logger (log all activity)
    ↓
Dashboard (display statistics)
```

### Email Statuses

| Status | Description |
|--------|-------------|
| **Incoming** | New emails received |
| **Pending** | Being processed/reviewed |
| **Answered** | Auto-reply sent |
| **Manual Reply** | Needs manual response |
| **Done** | Processing complete |

## 🎨 Dashboard Features

The web dashboard shows:

- **Real-time Statistics**: Number of emails in each status
- **Status Breakdown**: Percentage distribution using charts
- **Live Updates**: WebSocket-based real-time updates
- **Responsive Design**: Works on desktop and mobile

Access at: http://localhost:8000

## ⚙️ Configuration

### Main Settings (config.py)

```python
SPREADSHEET_ID = "..."              # Google Sheets ID
DOC_FILE_NAME = "Email Responses.docx"  # Google Drive document
DASHBOARD_PORT = 8000               # Dashboard port
EMAIL_CHECK_INTERVAL_MINUTES = 60   # Check frequency
SIMILARITY_THRESHOLD = 0.4          # 40% minimum match confidence
```

### Matching Sensitivity

Adjust `SIMILARITY_THRESHOLD`:
- **Lower (0.2-0.3)**: More auto-replies, some false positives
- **Default (0.4)**: Balanced approach
- **Higher (0.6-0.7)**: Fewer auto-replies, higher accuracy

## 🔌 Integration Examples

### Run as a Standalone Service

```bash
python run_email_tracker.py
```

### Run Just the Scheduler

```python
import asyncio
from email_tracker import EmailTrackerApp

async def main():
    app = EmailTrackerApp(
        spreadsheet_id="YOUR_ID",
        doc_file_name="Email Responses.docx"
    )
    await app.start_scheduler(interval_minutes=60)
    # Keep running indefinitely
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

### Run Just the Dashboard

```python
from email_tracker import EmailTrackerApp

app = EmailTrackerApp(
    spreadsheet_id="YOUR_ID",
    doc_file_name="Email Responses.docx"
)
app.start_dashboard()  # Runs on port 8000
```

### Integrate with Onit as a Tool

```python
from src.email_tracker import EmailTrackerApp

async def process_emails_tool():
    """Onit tool for processing emails."""
    app = EmailTrackerApp(
        spreadsheet_id="YOUR_ID"
    )
    await app.process_emails_immediately()

# Register with Onit
onit.register_tool("process_emails", process_emails_tool)
```

## 🧪 Testing

Verify installation:

```bash
python test_email_tracker_setup.py
```

This checks:
- ✅ All required packages installed
- ✅ All modules available
- ✅ All files present
- ✅ Credentials configured

## 📝 Google Sheets Format

The logging sheet automatically has these columns:

| Timestamp | Email ID | From Email | Subject | Category | Status | Matched Response | Reply Sent | Reply Sent At | Notes |
|-----------|----------|-----------|---------|----------|--------|------------------|-----------|---------------|-------|
| 2024-01-15T10:30:00 | msg_123 | user@example.com | Question | Support | answered | Yes | 2024-01-15T10:31:00 | Auto-replied |

## 🔐 Security

- **Credentials**: Stored locally in `credentials.json` (add to .gitignore)
- **Tokens**: Cached in `*.pickle` files (add to .gitignore)
- **Google Drive**: Uses read-only access for documents
- **Gmail**: Uses Gmail API with appropriate scopes

### Recommended .gitignore additions

```
credentials.json
*_token.pickle
.env
.env.local
```

## 📚 Advanced Usage

### Custom Categories

```python
from email_tracker import EmailCategorizer

categorizer = EmailCategorizer()
categorizer.add_custom_category("VIP", ["vip", "premium", "gold"])
```

### Process Emails Immediately

```python
import asyncio
from email_tracker import EmailTrackerApp

app = EmailTrackerApp(spreadsheet_id="YOUR_ID")
asyncio.run(app.process_emails_immediately())
```

### Get Statistics

```python
from email_tracker import SheetsLogger

logger = SheetsLogger(spreadsheet_id="YOUR_ID")
stats = logger.get_statistics()
print(f"Incoming: {stats['incoming']}")
print(f"Done: {stats['done']}")
```

## 🐛 Troubleshooting

### Common Issues

**"Authorization required" error**
- Delete `*.pickle` files
- Re-run to re-authenticate

**"File not found" error**
- Check document name matches exactly
- Verify document is shared with your account

**No emails processed**
- Verify emails are unread in Gmail
- Check Gmail API is enabled
- Review logs for errors

**More help?**
See [SETUP_EMAIL_TRACKER.md](SETUP_EMAIL_TRACKER.md#troubleshooting)

## 📊 Performance

- **Email Check**: ~5-10 seconds per batch
- **Dashboard Load**: <100ms per request
- **Processing**: Real-time with WebSocket updates
- **Sheets Update**: ~2-3 seconds per batch

## 🔄 Email Processing Frequency

| Interval | Use Case |
|----------|----------|
| Every 5 min | High-volume support |
| Every 15 min | Regular support |
| Every 1 hour | Standard (default) |
| Every 4 hours | Low-volume |
| Manual only | Critical/sensitive |

## 📈 Scaling Considerations

- **Multiple Gmail accounts**: Create separate instances
- **High volume**: Reduce check interval
- **Many rules**: Add more categories/keywords
- **Large sheets**: Archive old logs regularly

## 🤝 Contributing

To improve the email tracker:
1. Fork the project
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is part of Onit and uses the Apache 2.0 License.

## 🆘 Support

- **Setup Issues**: See [SETUP_EMAIL_TRACKER.md](SETUP_EMAIL_TRACKER.md)
- **Google APIs**: Check Google Cloud documentation
- **Errors**: Run `test_email_tracker_setup.py`
- **Logs**: Check terminal output for detailed logs

## 🎉 Getting Started

1. **Install**: `pip install -e ".[email-tracker]"`
2. **Setup**: Follow [SETUP_EMAIL_TRACKER.md](SETUP_EMAIL_TRACKER.md)
3. **Configure**: Update `run_email_tracker.py`
4. **Run**: `python run_email_tracker.py`
5. **Access**: http://localhost:8000

That's it! Your automated email system is ready! 🚀
