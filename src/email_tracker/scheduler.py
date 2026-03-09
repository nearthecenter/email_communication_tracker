"""Email scheduler for periodic checks and automation."""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .models import Email, EmailStatus, EmailLog
from .gmail_service import GmailService
from .categorizer import EmailCategorizer
from .doc_reader import DocReader
from .response_matcher import ResponseMatcher
from .sheets_logger import SheetsLogger

logger = logging.getLogger(__name__)


class EmailScheduler:
    """Scheduler for automated email processing."""

    def __init__(
        self,
        gmail_service: GmailService,
        categorizer: EmailCategorizer,
        doc_reader: DocReader,
        response_matcher: ResponseMatcher,
        sheets_logger: SheetsLogger,
        doc_file_name: str = "Email Responses.docx",
    ):
        """Initialize email scheduler.
        
        Args:
            gmail_service: GmailService instance
            categorizer: EmailCategorizer instance
            doc_reader: DocReader instance
            response_matcher: ResponseMatcher instance
            sheets_logger: SheetsLogger instance
            doc_file_name: Name of the Google Drive .docx file
        """
        self.gmail_service = gmail_service
        self.categorizer = categorizer
        self.doc_reader = doc_reader
        self.response_matcher = response_matcher
        self.sheets_logger = sheets_logger
        self.doc_file_name = doc_file_name
        self.scheduler = AsyncIOScheduler()
        self.document_content = None
        self.is_running = False

    async def start(self, interval_minutes: int = 60) -> None:
        """Start the email scheduler.
        
        Args:
            interval_minutes: Check emails every N minutes (default: 60)
        """
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Load document once at startup
        self.document_content = self.doc_reader.get_answers_by_name(
            self.doc_file_name
        )
        if not self.document_content:
            logger.warning(
                f"Could not load {self.doc_file_name}. Auto-reply will be disabled."
            )

        # Schedule job
        self.scheduler.add_job(
            self._process_emails,
            IntervalTrigger(minutes=interval_minutes),
            id="email_processor",
            name="Email Processing Job",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True
        logger.info(f"Email scheduler started (checking every {interval_minutes} minutes)")

    async def stop(self) -> None:
        """Stop the email scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Email scheduler stopped")

    async def _process_emails(self) -> None:
        """Process unread emails."""
        logger.info("Starting email processing job...")

        try:
            # Fetch unread emails
            unread_emails = self.gmail_service.get_unread_emails(max_results=20)
            logger.info(f"Found {len(unread_emails)} unread emails")

            processed_emails = []

            for email in unread_emails:
                processed_email = await self._process_single_email(email)
                processed_emails.append(processed_email)

            # Log to Google Sheets
            email_logs = []
            for e in processed_emails:
                try:
                    log = EmailLog.from_email(e)
                    email_logs.append(log)
                except Exception as log_error:
                    logger.error(f"Failed to create log for email {getattr(e, 'email_id', 'unknown')}: {log_error}")
                    # Create a basic log entry
                    try:
                        email_logs.append(EmailLog(
                            email_id=getattr(e, 'email_id', 'unknown'),
                            from_email=getattr(e, 'from_email', 'unknown@example.com'),
                            subject=getattr(e, 'subject', '(No Subject)'),
                            category=getattr(e, 'category', 'error'),
                            status=getattr(e, 'status', 'manual_reply'),
                            matched_response=None,
                            reply_sent=False,
                            reply_sent_at=None,
                            notes=f"Log creation failed: {log_error}",
                        ))
                    except Exception as fallback_error:
                        logger.error(f"Failed to create fallback log: {fallback_error}")

            if email_logs:
                success = self.sheets_logger.log_emails(email_logs)
                if not success:
                    logger.error("Failed to log emails to Google Sheets")
                else:
                    logger.info(f"Successfully logged {len(email_logs)} emails to Google Sheets")
            else:
                logger.warning("No email logs to write to Google Sheets")

            logger.info(f"Processed {len(processed_emails)} emails")
        except Exception as e:
            logger.error(f"Error in email processing job: {e}", exc_info=True)

    async def _process_single_email(self, email: Email) -> Email:
        """Process a single email."""
        try:
            # Categorize email
            email.category = self.categorizer.categorize(email)

            # Try to find matching response
            if self.document_content:
                matched_response, confidence = self.response_matcher.find_response(
                    email, self.document_content
                )

                if matched_response and confidence >= 0.4:  # 40% confidence threshold
                    email.matched_response = matched_response
                    email.status = EmailStatus.PENDING

                    # Send auto-reply
                    success = self.gmail_service.send_reply(
                        to_email=email.from_email,
                        subject=email.subject,
                        body=self._format_reply_body(matched_response),
                        in_reply_to_id=email.email_id,
                    )

                    if success:
                        email.reply_sent = True
                        email.reply_sent_at = datetime.utcnow()
                        email.status = EmailStatus.DONE
                        logger.info(f"Auto-reply sent for email {email.email_id}")
                    else:
                        email.status = EmailStatus.PENDING
                        email.notes = "Failed to send auto-reply"
                else:
                    # No matching response found – leave the message unread
                    # so it will stay in the inbox for manual review.
                    email.status = EmailStatus.MANUAL_REPLY
                    self.gmail_service.mark_as_unread(email.email_id)
            else:
                # Document not loaded, give up on this run and mark it read
                # so we don't try infinitely until the document is available.
                email.status = EmailStatus.PENDING
                self.gmail_service.mark_as_read(email.email_id)

            return email
        except Exception as e:
            logger.error(f"Error processing email {email.email_id}: {e}")
            email.status = EmailStatus.MANUAL_REPLY
            email.notes = f"Error: {str(e)}"
            return email

    def _format_reply_body(self, response: str) -> str:
        """Format the reply body with a professional header."""
        header = (
            "Thank you for your email.\n\n"
            "Here's the information you requested:\n\n"
        )
        footer = (
            "\n\nBest regards,\nAutomated Email Response System"
        )
        return header + response + footer

    async def process_emails_now(self) -> None:
        """Process emails immediately (useful for testing)."""
        await self._process_emails()

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "is_running": self.is_running,
            "has_document": self.document_content is not None,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time),
                }
                for job in self.scheduler.get_jobs()
            ],
        }
