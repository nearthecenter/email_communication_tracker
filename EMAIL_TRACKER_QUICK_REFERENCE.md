"""
Email Tracker - Quick Reference Guide

This file contains common commands and use cases.
"""

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

# 1. Install dependencies
# pip install -e ".[email-tracker]"

# 2. Get credentials from Google Cloud Console
# Download credentials.json

# 3. Create documents
# - Email Responses.docx on Google Drive
# - Google Sheet for logging

# 4. Update configuration
# Edit run_email_tracker.py with your SPREADSHEET_ID


# ============================================================================
# RUNNING THE SYSTEM
# ============================================================================

# Start with dashboard and scheduler
# python run_email_tracker.py

# Test installation
# python test_email_tracker_setup.py


# ============================================================================
# PYTHON CODE EXAMPLES
# ============================================================================

# Example 1: Basic Usage
# ----------------------------------------
import asyncio
from email_tracker import EmailTrackerApp

async def example_basic():
    app = EmailTrackerApp(
        spreadsheet_id="1234567890abcdefg",
        doc_file_name="Email Responses.docx"
    )
    
    # Start scheduler (checks emails every 60 minutes)
    await app.start_scheduler(interval_minutes=60)
    
    # Keep running
    while True:
        await asyncio.sleep(1)

# asyncio.run(example_basic())


# Example 2: Process Emails Immediately
# ----------------------------------------
async def example_immediate():
    app = EmailTrackerApp(spreadsheet_id="YOUR_ID")
    
    # Process emails right now (don't wait for scheduler)
    await app.process_emails_immediately()
    
    # Get status
    status = app.get_status()
    print(status)

# asyncio.run(example_immediate())


# Example 3: Just the Dashboard
# ----------------------------------------
def example_dashboard_only():
    from email_tracker import EmailTrackerApp
    
    app = EmailTrackerApp(spreadsheet_id="YOUR_ID")
    
    # Start only the dashboard (no scheduler)
    app.start_dashboard()  # Opens http://localhost:8000

# example_dashboard_only()


# Example 4: Custom Categorization
# ----------------------------------------
from email_tracker import EmailTrackerApp, EmailCategorizer

def example_custom_categories():
    app = EmailTrackerApp(spreadsheet_id="YOUR_ID")
    
    # Add custom category
    app.categorizer.add_custom_category(
        "VIP Customers",
        ["vip", "premium", "enterprise", "gold"]
    )
    
    # Get all categories
    categories = app.categorizer.get_categories()
    print(categories)

# example_custom_categories()


# Example 5: Adjust Matching Sensitivity
# ----------------------------------------
from email_tracker import ResponseMatcher

def example_sensitivity():
    # More sensitive (more false positives)
    matcher_sensitive = ResponseMatcher(similarity_threshold=0.3)
    
    # Default
    matcher_balanced = ResponseMatcher(similarity_threshold=0.4)
    
    # More strict (fewer false positives)
    matcher_strict = ResponseMatcher(similarity_threshold=0.6)

# example_sensitivity()


# Example 6: Get Email Statistics
# ----------------------------------------
from email_tracker import SheetsLogger

def example_statistics():
    logger = SheetsLogger(spreadsheet_id="YOUR_ID")
    
    # Get all statistics
    stats = logger.get_statistics()
    
    print(f"Total emails: {stats['total']}")
    print(f"Incoming: {stats['incoming']}")
    print(f"Pending: {stats['pending']}")
    print(f"Auto answered: {stats['answered']}")
    print(f"Need manual reply: {stats['manual_reply']}")
    print(f"Done: {stats['done']}")

# example_statistics()


# Example 7: Fetch Unread Emails
# ----------------------------------------
from email_tracker import GmailService

def example_fetch_emails():
    gmail = GmailService()
    
    # Get up to 20 unread emails
    emails = gmail.get_unread_emails(max_results=20)
    
    for email in emails:
        print(f"From: {email.from_email}")
        print(f"Subject: {email.subject}")
        print(f"Body: {email.body[:100]}...")
        print()

# example_fetch_emails()


# Example 8: Send Manual Reply
# ----------------------------------------
from email_tracker import GmailService

def example_send_reply():
    gmail = GmailService()
    
    success = gmail.send_reply(
        to_email="user@example.com",
        subject="Original Subject",
        body="Thank you for your email. We will respond soon.",
        in_reply_to_id="email_id_here"
    )
    
    if success:
        print("✅ Reply sent!")
    else:
        print("❌ Failed to send reply")

# example_send_reply()


# Example 9: Read Document from Google Drive
# ----------------------------------------
from email_tracker import DocReader

def example_read_doc():
    reader = DocReader()
    
    # Get document by file name
    content = reader.get_answers_by_name("Email Responses.docx")
    
    if content:
        print("Document content:")
        print(content)
        
        # Extract sections
        sections = reader.extract_sections(content)
        for section, text in sections.items():
            print(f"\n[{section}]")
            print(text)
    else:
        print("Document not found")

# example_read_doc()


# Example 10: Match Email to Response
# ----------------------------------------
from email_tracker import Email, EmailStatus, ResponseMatcher, DocReader

async def example_match_response():
    # Create a sample email
    email = Email(
        email_id="msg_123",
        from_email="customer@example.com",
        subject="What is your return policy?",
        body="I want to know about your return policy."
    )
    
    # Load document
    reader = DocReader()
    doc_content = reader.get_answers_by_name("Email Responses.docx")
    
    # Match response
    matcher = ResponseMatcher(similarity_threshold=0.4)
    matched_response, confidence = matcher.find_response(email, doc_content)
    
    print(f"Confidence: {confidence:.1%}")
    print(f"Matched response: {matched_response}")

# asyncio.run(example_match_response())


# ============================================================================
# CONFIGURATION OPTIONS
# ============================================================================

"""
Key settings in config.py:

SPREADSHEET_ID = "YOUR_ID"
    Google Sheets ID from URL: docs.google.com/spreadsheets/d/{ID}

DOC_FILE_NAME = "Email Responses.docx"
    Name of document in Google Drive

DASHBOARD_PORT = 8000
    Port for web dashboard

EMAIL_CHECK_INTERVAL_MINUTES = 60
    How often to check emails (in minutes)

SIMILARITY_THRESHOLD = 0.4
    Minimum confidence for auto-reply (0.0 to 1.0)
    - 0.3: More aggressive (more false positives)
    - 0.4: Balanced (default)
    - 0.6: Conservative (fewer false positives)
"""


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

"""
Available API endpoints:

GET /                          - Dashboard HTML page
GET /api/stats                 - Get current statistics (JSON)
GET /api/health                - Health check
WebSocket /ws/stats            - Real-time statistics stream

Dashboard runs on: http://localhost:8000
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Common issues and solutions:

1. "Authorization required"
   → Delete *.pickle files and re-run
   → Re-authenticate with Google

2. "File not found in Google Drive"
   → Check document name matches exactly
   → Verify file is shared with your account
   → Document must be .docx format

3. No emails being processed
   → Verify emails are marked UNREAD in Gmail
   → Check Gmail API is enabled
   → Review terminal logs for errors

4. Auto-replies too aggressive
   → Increase SIMILARITY_THRESHOLD (0.6 instead of 0.4)
   → Review matched responses in Google Sheets

5. Dashboard won't load
   → Check port 8000 is not in use
   → Verify FastAPI is installed: pip install fastapi uvicorn
   → Check firewall settings

6. "credentials.json not found"
   → Download from Google Cloud Console
   → Save in project root directory
   → Run setup process again
"""


# ============================================================================
# CLI COMMANDS
# ============================================================================

"""
Various command line options:

# Start full system
python run_email_tracker.py

# Test installation
python test_email_tracker_setup.py

# Check imports
python -c "from email_tracker import *; print('OK')"

# Get Python environment
python -c "import sys; print(sys.executable)"
"""


# ============================================================================
# ENVIRONMENT VARIABLES (OPTIONAL)
# ============================================================================

"""
Optional environment variables:

export ONIT_EMAIL_TRACKER_SPREADSHEET_ID="your-id"
export ONIT_EMAIL_TRACKER_DOC_FILE="Email Responses.docx"
export ONIT_EMAIL_TRACKER_PORT="8000"
export ONIT_EMAIL_TRACKER_INTERVAL="60"
"""


# ============================================================================
# FILE STRUCTURE
# ============================================================================

"""
After setup, your directory should look like:

onit/
├── src/email_tracker/
│   ├── __init__.py
│   ├── models.py
│   ├── gmail_service.py
│   ├── categorizer.py
│   ├── doc_reader.py
│   ├── response_matcher.py
│   ├── sheets_logger.py
│   ├── scheduler.py
│   ├── app.py
│   ├── config.py
│   └── web/
│       └── __init__.py
├── credentials.json              ← From Google Cloud
├── gmail_token.pickle            ← Auto-generated
├── drive_token.pickle            ← Auto-generated
├── sheets_token.pickle           ← Auto-generated
├── run_email_tracker.py
├── test_email_tracker_setup.py
├── EMAIL_TRACKER_README.md
└── SETUP_EMAIL_TRACKER.md
"""


# ============================================================================
# NEXT STEPS
# ============================================================================

"""
1. ✅ Read EMAIL_TRACKER_README.md (overview)
2. ✅ Read SETUP_EMAIL_TRACKER.md (detailed setup)
3. ✅ Run test_email_tracker_setup.py (verify installation)
4. ✅ Update run_email_tracker.py (add your Sheets ID)
5. ✅ Run python run_email_tracker.py (start the system)
6. ✅ Open http://localhost:8000 (view dashboard)
7. ✅ Monitor Google Sheets (check logs)
8. ✅ Fine-tune configuration as needed
"""


# ============================================================================
# ADDITIONAL RESOURCES
# ============================================================================

"""
Documentation:
- EMAIL_TRACKER_README.md     - Project overview
- SETUP_EMAIL_TRACKER.md      - Detailed setup guide
- Google Cloud:               - console.cloud.google.com
- Google Workspace:           - workspace.google.com

API Documentation:
- Gmail API:                  - developers.google.com/gmail/api
- Google Sheets API:          - developers.google.com/sheets/api
- Google Drive API:           - developers.google.com/drive/api
- FastAPI:                    - fastapi.tiangolo.com
"""
