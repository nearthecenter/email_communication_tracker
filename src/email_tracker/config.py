# Email Tracker Configuration
# Update these values for your setup

# Google Sheets Configuration
SPREADSHEET_ID = "YOUR_GOOGLE_SHEETS_ID_HERE"

# Document Configuration
DOC_FILE_NAME = "Email Responses.docx"  # Name of Google Drive .docx file

# Dashboard Configuration
DASHBOARD_PORT = 8000
DASHBOARD_HOST = "0.0.0.0"

# Email Scheduler Configuration
EMAIL_CHECK_INTERVAL_MINUTES = 60  # Check emails every hour

# Response Matching Configuration
SIMILARITY_THRESHOLD = 0.4  # 0.0 to 1.0 (40% similarity for auto-reply)

# Credentials Files
GMAIL_CREDENTIALS = "credentials.json"
DRIVE_CREDENTIALS = "credentials.json"
SHEETS_CREDENTIALS = "credentials.json"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
