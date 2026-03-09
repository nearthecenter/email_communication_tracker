"""Google Drive .docx reader for email responses."""

import logging
import io
import os
from typing import Optional, Dict
from docx import Document
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DocReader:
    """Reads .docx documents from Google Drive."""

    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "drive_token.pickle"):
        """Initialize Google Drive service."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
        self.document_cache: Dict[str, str] = {}

    def _authenticate(self) -> None:
        """Authenticate with Google Drive API."""
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

        self.service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service authenticated successfully")

    def get_file_id_by_name(self, file_name: str) -> Optional[str]:
        """Find file ID by file name."""
        try:
            query = f"name='{file_name}' and trashed=false and mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            results = self.service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1
            ).execute()

            files = results.get("files", [])
            if files:
                logger.info(f"Found file: {files[0]['name']} (ID: {files[0]['id']})")
                return files[0]["id"]
            else:
                logger.warning(f"No file found with name: {file_name}")
                return None
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

    def download_docx_content(self, file_id: str) -> Optional[str]:
        """Download and extract text content from .docx file."""
        try:
            # Check cache first
            if file_id in self.document_cache:
                logger.info(f"Using cached content for file {file_id}")
                return self.document_cache[file_id]

            # Download file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            # Parse .docx
            doc = Document(fh)
            full_text = "\n".join([para.text for para in doc.paragraphs])

            # Cache the content
            self.document_cache[file_id] = full_text
            logger.info(f"Downloaded and cached content from file {file_id}")
            return full_text
        except HttpError as error:
            logger.error(f"An error occurred while downloading: {error}")
            return None
        except Exception as e:
            logger.error(f"Error parsing docx: {e}")
            return None

    def get_answers_by_name(self, file_name: str) -> Optional[str]:
        """Get answers document content by file name."""
        file_id = self.get_file_id_by_name(file_name)
        if file_id:
            return self.download_docx_content(file_id)
        return None

    def extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from document content."""
        sections = {}
        current_section = "General"
        sections[current_section] = []

        for line in content.split("\n"):
            # Detect section headers (lines that are all caps or prefixed with #)
            if line.strip() and (line.isupper() or line.startswith("#")):
                current_section = line.strip().replace("#", "").strip()
                sections[current_section] = []
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(line)

        # Join lines back together
        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def clear_cache(self) -> None:
        """Clear document cache."""
        self.document_cache.clear()
        logger.info("Document cache cleared")
