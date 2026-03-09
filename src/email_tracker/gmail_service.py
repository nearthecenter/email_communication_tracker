"""Gmail API service for email communication tracker."""

import base64
import os
import logging
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import email
from email.mime.text import MIMEText

from .models import Email, EmailStatus
import logging

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailService:
    """Service for interacting with Gmail API."""

    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.pickle"):
        """Initialize Gmail service."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth 2.0."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service authenticated successfully")

    def get_unread_emails(self, max_results: int = 10) -> List[Email]:
        """Fetch unread emails from inbox."""
        try:
            results = self.service.users().messages().list(
                userId="me",
                q="is:unread",
                maxResults=max_results
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                email_obj = self._parse_message(message["id"])
                if email_obj:
                    emails.append(email_obj)

            return emails
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []

    def _parse_message(self, message_id: str) -> Optional[Email]:
        """Parse a Gmail message into Email object."""
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            headers = message["payload"]["headers"]
            body_text = self._get_message_body(message)

            # Extract header information
            email_data = {
                "email_id": message_id,
                "from_email": next(
                    (h["value"] for h in headers if h["name"] == "From"),
                    "unknown@example.com"
                ),
                "subject": next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "(No Subject)"
                ),
                "body": body_text,
            }

            return Email(**email_data)
        except Exception as e:
            logger.error(f"Error parsing message {message_id}: {e}")
            return None

    def _get_message_body(self, message: dict) -> str:
        """Extract text body from Gmail message."""
        try:
            if "parts" in message["payload"]:
                parts = message["payload"]["parts"]
                for part in parts:
                    if part["mimeType"] == "text/plain":
                        if "data" in part["body"]:
                            return base64.urlsafe_b64decode(
                                part["body"]["data"]
                            ).decode("utf-8")
            else:
                if "data" in message["payload"]["body"]:
                    return base64.urlsafe_b64decode(
                        message["payload"]["body"]["data"]
                    ).decode("utf-8")
        except Exception as e:
            logger.error(f"Error extracting message body: {e}")

        return ""

    def send_reply(self, to_email: str, subject: str, body: str, in_reply_to_id: str) -> bool:
        """Send an email reply."""
        try:
            message = MIMEText(body)
            message["to"] = to_email
            message["subject"] = f"Re: {subject}"
            message["In-Reply-To"] = in_reply_to_id
            message["References"] = in_reply_to_id

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode("utf-8")

            self.service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()

            logger.info(f"Reply sent to {to_email}")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while sending reply: {error}")
            return False

    def mark_as_unread(self, message_id: str) -> bool:
        """Mark an email as unread (add the UNREAD label)."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Marked message {message_id} as unread")
            return True
        except HttpError as error:
            logger.error(f"Error marking message as unread: {error}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read (remove the UNREAD label)."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Marked message {message_id} as read")
            return True
        except HttpError as error:
            logger.error(f"Error marking message as read: {error}")
            return False

    def archive_email(self, message_id: str) -> bool:
        """Archive an email."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["INBOX"]}
            ).execute()
            logger.info(f"Archived message {message_id}")
            return True
        except HttpError as error:
            logger.error(f"Error archiving message: {error}")
            return False

    def is_email_read(self, message_id: str) -> bool:
        """Check if an email has been read (opened).
        
        Returns:
            True if email is read (UNREAD label not present), False if unread
        """
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="minimal"
            ).execute()
            
            # Check if UNREAD label is present
            labels = message.get("labelIds", [])
            is_unread = "UNREAD" in labels
            
            logger.debug(f"Message {message_id} is {'unread' if is_unread else 'read'}")
            return not is_unread
        except HttpError as error:
            logger.error(f"Error checking if message is read: {error}")
            return False

    def has_reply_sent(self, message_id: str) -> bool:
        """Check if there's been a reply sent to this email.
        
        This looks for messages sent by the user that reference the original message.
        
        Returns:
            True if a reply has been sent, False otherwise
        """
        try:
            # Get the original message to extract thread ID or details
            original_message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="minimal"
            ).execute()
            
            # Get the thread ID
            thread_id = original_message.get("threadId")
            if not thread_id:
                logger.warning(f"Could not find thread ID for message {message_id}")
                return False
            
            # Get all messages in this thread
            thread = self.service.users().threads().get(
                userId="me",
                id=thread_id,
                format="minimal"
            ).execute()
            
            messages = thread.get("messages", [])
            
            # Check if any message in the thread was sent by the user (has SENT label)
            # and comes after the original message
            original_date = original_message.get("internalDate")
            
            for msg in messages:
                msg_labels = msg.get("labelIds", [])
                msg_date = int(msg.get("internalDate", 0))
                
                # Check if message has SENT label and is after the original
                if "SENT" in msg_labels and msg_date > int(original_date):
                    logger.debug(f"Found reply in thread {thread_id}")
                    return True
            
            logger.debug(f"No reply found in thread {thread_id}")
            return False
        except HttpError as error:
            logger.error(f"Error checking for reply: {error}")
            return False

    def get_email_status(self, message_id: str) -> str:
        """Determine the status of an email based on read status and replies.
        
        Returns:
            "done" if reply has been sent
            "ongoing" if email has been opened/read
            "pending" if email is still unread
        """
        try:
            # Check if there's a reply first
            if self.has_reply_sent(message_id):
                return "done"
            
            # Check if email has been read
            if self.is_email_read(message_id):
                return "ongoing"
            
            # Otherwise it's still pending
            return "pending"
        except Exception as e:
            logger.error(f"Error determining email status: {e}")
            return "pending"

