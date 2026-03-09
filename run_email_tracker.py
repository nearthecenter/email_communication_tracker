"""
Example runner script for the Email Tracker.
This demonstrates how to use the email tracker system.
"""

import asyncio
import threading
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from email_tracker.app import EmailTrackerApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def run_scheduler_thread(app, interval_minutes=60):
    """Run scheduler in a separate thread."""
    try:
        asyncio.run(app.start_scheduler(interval_minutes=interval_minutes))
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)


def main():
    """Main entry point."""
    
    # ========================================
    # Configure your settings here
    # ========================================
    SPREADSHEET_ID = "1hSzXPnf3_AVg0NCA3fACSeYPHdh6-04yHAVwPp_cCGY"  # Update this!
    DOC_FILE_NAME = "FAQs for UP Alumni Email.docx"
    DASHBOARD_PORT = 8001
    EMAIL_CHECK_INTERVAL_MINUTES = 5
    
    # Verify configuration
    if SPREADSHEET_ID == "YOUR_GOOGLE_SHEETS_ID":
        logger.error("❌ Please update SPREADSHEET_ID in this script!")
        logger.info("   Get your Sheets ID from: docs.google.com/spreadsheets/d/{ID}")
        return
    
    logger.info("=" * 60)
    logger.info("📧 Email Tracker - Starting Up")
    logger.info("=" * 60)
    
    try:
        # Initialize the app
        app = EmailTrackerApp(
            spreadsheet_id=SPREADSHEET_ID,
            doc_file_name=DOC_FILE_NAME,
            dashboard_port=DASHBOARD_PORT,
        )
        
        logger.info(f"✅ Email Tracker initialized")
        logger.info(f"   Spreadsheet ID: {SPREADSHEET_ID}")
        logger.info(f"   Document: {DOC_FILE_NAME}")
        logger.info(f"   Dashboard: http://localhost:{DASHBOARD_PORT}")
        logger.info("")

        # perform one check immediately so sheet/dashboard aren’t stale
        try:
            asyncio.run(app.process_emails_immediately())
            logger.info("✅ Immediate email processing complete")
        except Exception as e:
            logger.error(f"Error during initial email processing: {e}")

        # Start scheduler in background thread
        logger.info("🔄 Starting email scheduler...")
        scheduler_thread = threading.Thread(
            target=run_scheduler_thread,
            args=(app, EMAIL_CHECK_INTERVAL_MINUTES),
            daemon=True
        )
        scheduler_thread.start()
        logger.info(f"✅ Scheduler running (checking every {EMAIL_CHECK_INTERVAL_MINUTES} minutes)")
        logger.info("")
        
        # Start dashboard (blocks until interrupted)
        logger.info("🚀 Starting web dashboard...")
        logger.info(f"   Open your browser: http://localhost:{DASHBOARD_PORT}")
        logger.info("")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        logger.info("")
        
        app.start_dashboard()
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("📧 Email Tracker - Shutting Down")
        logger.info("=" * 60)
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.info("   Make sure credentials.json is in the project root")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
