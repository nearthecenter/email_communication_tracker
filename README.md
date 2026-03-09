# UP OAR Alumni Email Tracker

Automated email management system for the **University of the Philippines Office of Alumni Relations (OAR)**. Reads unread Gmail messages, matches them against a FAQ document on Google Drive, sends auto-replies when a match is found, and logs everything to Google Sheets.

## Features

- Auto-replies to alumni email inquiries using a FAQ `.docx` file on Google Drive
- Logs all processed emails to Google Sheets
- Web dashboard with UP maroon branding at `http://localhost:8001`
- Checks for new emails every minute (configurable)

## Requirements

- Python 3.13 (system install)
- Google account with Gmail, Google Drive, and Google Sheets access
- `credentials.json` from Google Cloud Console (OAuth 2.0 Desktop App)

## Setup

### 1. Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable: **Gmail API**, **Google Drive API**, **Google Sheets API**
3. Create **OAuth 2.0 credentials** (Desktop App) and download as `credentials.json`
4. Place `credentials.json` in the project root directory

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

Edit `run_clean.py` and set your values:

```python
SPREADSHEET_ID = "your-google-sheets-id"   # ID from your Google Sheets URL
DOC_FILE_NAME  = "FAQs for UP Alumni Email.docx"  # File name on Google Drive
DASHBOARD_PORT = 8001
EMAIL_CHECK_INTERVAL_MINUTES = 1
```

### 4. FAQ Document

Create a `.docx` file on Google Drive named `FAQs for UP Alumni Email.docx` with Q&A pairs in this format:

```
Q: Who can avail the UP alumni email?
A: Any UP graduate can apply for an alumni email account.

Q: How do I register for an alumni email?
A: Visit the Alumni Email Registration page and fill out the form.
```

### 5. Run

```bash
python run_clean.py
```

On first run, a browser window will open for Google OAuth authentication. After that, tokens are saved locally and reused automatically.

## Usage

- **Dashboard:** `http://localhost:8001` — view email statistics and manually trigger processing
- **Auto-reply:** Emails matching a FAQ entry (≥35% confidence) receive an automatic reply and are marked as read
- **Manual reply:** Emails with no FAQ match are left unread for manual handling and logged as "Needs Manual Reply"

## Project Structure

```
email_communication_tracker/
├── credentials.json          # Google OAuth credentials (not committed)
├── run_clean.py              # Main entry point
├── requirements.txt          # Python dependencies
└── src/
    └── email_tracker/
        ├── app.py            # Application setup
        ├── gmail_service.py  # Gmail API (read, send, mark read/unread)
        ├── doc_reader.py     # Google Drive .docx reader
        ├── response_matcher.py  # FAQ keyword matching
        ├── categorizer.py    # Email categorization
        ├── scheduler.py      # APScheduler-based email processing loop
        ├── sheets_logger.py  # Google Sheets logging
        ├── models.py         # Pydantic data models
        └── web/
            └── __init__.py   # FastAPI dashboard
```

## Notes

- `credentials.json` and all `*.pickle` token files are excluded from git
- Do **not** activate the `venv` folder — it does not have the required packages. Use the system Python directly
- The dashboard auto-refreshes every 10 seconds via WebSocket
