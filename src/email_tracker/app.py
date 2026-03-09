"""Main entry point for email tracker application."""

import asyncio
import logging
from typing import Optional
from .gmail_service import GmailService
from .categorizer import EmailCategorizer
from .doc_reader import DocReader
from .response_matcher import ResponseMatcher
from .sheets_logger import SheetsLogger
from .scheduler import EmailScheduler
from .web import EmailTrackerDashboard

logger = logging.getLogger(__name__)


class EmailTrackerApp:
    """Main application for email tracking."""

    def __init__(
        self,
        spreadsheet_id: str,
        doc_file_name: str = "Email Responses.docx",
        dashboard_port: int = 8000,
        credentials_file: str = "credentials.json",
    ):
        """Initialize email tracker app.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID for logging
            doc_file_name: Name of Google Drive .docx file containing answers
            dashboard_port: Port for web dashboard
            credentials_file: Path to Google credentials JSON
        """
        self.spreadsheet_id = spreadsheet_id
        self.doc_file_name = doc_file_name
        self.dashboard_port = dashboard_port
        self.credentials_file = credentials_file

        # Initialize services
        self.gmail_service = GmailService(credentials_file=credentials_file)
        self.categorizer = EmailCategorizer()
        self.doc_reader = DocReader(credentials_file=credentials_file)
        self.response_matcher = ResponseMatcher(similarity_threshold=0.4)
        self.sheets_logger = SheetsLogger(
            spreadsheet_id=spreadsheet_id,
            credentials_file=credentials_file,
        )
        self.scheduler = EmailScheduler(
            gmail_service=self.gmail_service,
            categorizer=self.categorizer,
            doc_reader=self.doc_reader,
            response_matcher=self.response_matcher,
            sheets_logger=self.sheets_logger,
            doc_file_name=doc_file_name,
        )
        self.dashboard = EmailTrackerDashboard(
            sheets_logger=self.sheets_logger,
            port=dashboard_port,
        )

    async def start_scheduler(self, interval_minutes: int = 60) -> None:
        """Start email processing scheduler.
        
        Args:
            interval_minutes: Check emails every N minutes
        """
        await self.scheduler.start(interval_minutes=interval_minutes)

    async def stop_scheduler(self) -> None:
        """Stop email processing scheduler."""
        await self.scheduler.stop()

    async def process_emails_immediately(self) -> None:
        """Process emails immediately (useful for testing)."""
        # Ensure document is loaded
        if not self.scheduler.document_content:
            self.scheduler.document_content = self.doc_reader.get_answers_by_name(
                self.doc_file_name
            )
            if self.scheduler.document_content:
                logger.info("Document loaded for immediate processing")
            else:
                logger.warning("Could not load document for immediate processing")
        
        await self.scheduler.process_emails_now()

    def start_dashboard(self) -> None:
        """Start the web dashboard."""
        self.dashboard.run()

    def get_status(self) -> dict:
        """Get application status."""
        return {
            "scheduler": self.scheduler.get_status(),
            "sheets_logger": {
                "spreadsheet_id": self.spreadsheet_id,
                "sheet_name": self.sheets_logger.sheet_name,
            },
            "dashboard": {
                "port": self.dashboard_port,
            },
        }


async def main():
    """Example usage of EmailTrackerApp."""
    # Configure these with your values
    SPREADSHEET_ID = "your-google-sheets-id"
    DOC_FILE_NAME = "Email Responses.docx"
    DASHBOARD_PORT = 8000

    # Initialize app
    app = EmailTrackerApp(
        spreadsheet_id=SPREADSHEET_ID,
        doc_file_name=DOC_FILE_NAME,
        dashboard_port=DASHBOARD_PORT,
    )

    logger.info("Email Tracker Application initialized")
    logger.info(f"Status: {app.get_status()}")

    # Start scheduler (check emails every 60 minutes)
    await app.start_scheduler(interval_minutes=60)

    # In a real application, you'd run the dashboard in a separate thread
    # For now, just keep the scheduler running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await app.stop_scheduler()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run async main
    asyncio.run(main())
