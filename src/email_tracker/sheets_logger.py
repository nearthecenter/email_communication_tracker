"""Google Sheets logging service for email tracker."""

import logging
import os
from typing import List
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import EmailLog

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsLogger:
    """Logs email tracking data to Google Sheets."""

    def __init__(
        self,
        spreadsheet_id: str,
        sheet_name: str = "Email Tracker",
        credentials_file: str = "credentials.json",
        token_file: str = "sheets_token.pickle",
    ):
        """Initialize Sheets logger.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet to write to
            credentials_file: Path to credentials JSON
            token_file: Path to token pickle file
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
        self._ensure_sheet_exists()

    def _authenticate(self) -> None:
        """Authenticate with Google Sheets API."""
        creds = None

        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("sheets", "v4", credentials=creds)
        logger.info("Google Sheets service authenticated successfully")

    def _ensure_sheet_exists(self) -> None:
        """Ensure sheet exists and has headers."""
        try:
            # Get sheet info
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            sheet_names = [
                sheet["properties"]["title"] for sheet in sheet_metadata["sheets"]
            ]

            # Create sheet if it doesn't exist
            if self.sheet_name not in sheet_names:
                requests = [
                    {
                        "addSheet": {
                            "properties": {"title": self.sheet_name}
                        }
                    }
                ]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                logger.info(f"Created sheet: {self.sheet_name}")

            # Add headers if sheet is empty
            self._add_headers_if_needed()
        except HttpError as error:
            logger.error(f"An error occurred: {error}")

    def _add_headers_if_needed(self) -> None:
        """Add column headers if sheet is empty."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:Z1"
            ).execute()

            values = result.get("values", [])

            if not values:
                headers = [
                    "Timestamp",
                    "Email ID",
                    "From Email",
                    "Subject",
                    "Category",
                    "Status",
                    "Matched Response",
                    "Reply Sent",
                    "Reply Sent At",
                    "Notes",
                ]
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1:J1",
                    valueInputOption="RAW",
                    body={"values": [headers]}
                ).execute()
                logger.info("Added headers to sheet")
        except HttpError as error:
            logger.error(f"Error adding headers: {error}")

    def log_email(self, email_log: EmailLog) -> bool:
        """Log a single email to Google Sheets."""
        try:
            values = [
                [
                    email_log.timestamp.isoformat(),
                    email_log.email_id,
                    email_log.from_email,
                    email_log.subject,
                    email_log.category,
                    email_log.status,
                    email_log.matched_response or "",
                    str(email_log.reply_sent),
                    email_log.reply_sent_at.isoformat() if email_log.reply_sent_at else "",
                    email_log.notes or "",
                ]
            ]

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A:J",
                valueInputOption="RAW",
                body={"values": values}
            ).execute()

            logger.info(f"Logged email {email_log.email_id} to Google Sheets")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while logging: {error}")
            return False

    def log_emails(self, email_logs: List[EmailLog]) -> bool:
        """Log multiple emails to Google Sheets in batch."""
        try:
            values = [
                [
                    log.timestamp.isoformat(),
                    log.email_id,
                    log.from_email,
                    log.subject,
                    log.category,
                    log.status,
                    log.matched_response or "",
                    str(log.reply_sent),
                    log.reply_sent_at.isoformat() if log.reply_sent_at else "",
                    log.notes or "",
                ]
                for log in email_logs
            ]

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A:J",
                valueInputOption="RAW",
                body={"values": values}
            ).execute()

            logger.info(f"Logged {len(email_logs)} emails to Google Sheets")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while logging: {error}")
            return False

    def get_statistics(self) -> dict:
        """Get email statistics from Google Sheets."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A2:F"
            ).execute()

            values = result.get("values", [])

            stats = {
                "total": len(values),
                "incoming": sum(1 for row in values if len(row) > 5 and row[5] == "incoming"),
                "pending": sum(1 for row in values if len(row) > 5 and row[5] == "pending"),
                "answered": sum(1 for row in values if len(row) > 5 and row[5] == "answered"),
                "manual_reply": sum(1 for row in values if len(row) > 5 and row[5] == "manual_reply"),
                "done": sum(1 for row in values if len(row) > 5 and row[5] == "done"),
            }

            return stats
        except HttpError as error:
            logger.error(f"An error occurred while fetching statistics: {error}")
            return {}
