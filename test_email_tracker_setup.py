"""
Test script to verify email tracker installation and components.
Run this to check if everything is set up correctly.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_imports():
    """Check if all required packages are installed."""
    logger.info("Checking imports...")
    
    required_packages = {
        "google.auth": "google-auth",
        "google.auth.oauthlib": "google-auth-oauthlib",
        "googleapiclient": "google-api-python-client",
        "docx": "python-docx",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "apscheduler": "apscheduler",
    }
    
    missing_packages = []
    
    for module, package_name in required_packages.items():
        try:
            __import__(module)
            logger.info(f"✅ {package_name}")
        except ImportError:
            logger.error(f"❌ {package_name} - NOT INSTALLED")
            missing_packages.append(package_name)
    
    return len(missing_packages) == 0, missing_packages


def check_modules():
    """Check if email_tracker modules can be imported."""
    logger.info("\nChecking email_tracker modules...")
    
    modules = [
        "email_tracker",
        "email_tracker.models",
        "email_tracker.gmail_service",
        "email_tracker.categorizer",
        "email_tracker.doc_reader",
        "email_tracker.response_matcher",
        "email_tracker.sheets_logger",
        "email_tracker.scheduler",
        "email_tracker.web",
        "email_tracker.app",
    ]
    
    missing_modules = []
    
    for module in modules:
        try:
            __import__(module)
            logger.info(f"✅ {module}")
        except ImportError as e:
            logger.error(f"❌ {module} - {e}")
            missing_modules.append(module)
    
    return len(missing_modules) == 0, missing_modules


def check_files():
    """Check if necessary files exist."""
    logger.info("\nChecking files...")
    
    required_files = {
        "src/email_tracker/__init__.py": "Email tracker package",
        "src/email_tracker/models.py": "Data models",
        "src/email_tracker/gmail_service.py": "Gmail service",
        "src/email_tracker/categorizer.py": "Email categorizer",
        "src/email_tracker/doc_reader.py": "Google Drive reader",
        "src/email_tracker/response_matcher.py": "Response matcher",
        "src/email_tracker/sheets_logger.py": "Google Sheets logger",
        "src/email_tracker/scheduler.py": "Email scheduler",
        "src/email_tracker/web/__init__.py": "Web dashboard",
        "src/email_tracker/app.py": "Main app",
        "run_email_tracker.py": "Runner script",
        "SETUP_EMAIL_TRACKER.md": "Setup guide",
    }
    
    missing_files = []
    
    for file_path, description in required_files.items():
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            logger.info(f"✅ {file_path} - {description}")
        else:
            logger.error(f"❌ {file_path} - NOT FOUND")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files


def check_credentials():
    """Check if credentials file exists."""
    logger.info("\nChecking credentials...")
    
    cred_file = Path(__file__).parent / "credentials.json"
    
    if cred_file.exists():
        logger.info(f"✅ credentials.json found")
        return True
    else:
        logger.warning(f"⚠️  credentials.json NOT found")
        logger.info("   You'll need to create it before running the tracker")
        logger.info("   See SETUP_EMAIL_TRACKER.md for instructions")
        return False


def main():
    """Run all checks."""
    logger.info("=" * 60)
    logger.info("📧 Email Tracker - Installation Check")
    logger.info("=" * 60)
    logger.info("")
    
    all_good = True
    
    # Check imports
    imports_ok, missing_packages = check_imports()
    if not imports_ok:
        logger.error(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        logger.info("\nTo install missing packages, run:")
        logger.info(f"  pip install {' '.join(missing_packages)}")
        all_good = False
    else:
        logger.info("\n✅ All required packages installed")
    
    # Check modules
    modules_ok, missing_modules = check_modules()
    if not modules_ok:
        logger.error(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        all_good = False
    else:
        logger.info("\n✅ All modules available")
    
    # Check files
    files_ok, missing_files = check_files()
    if not files_ok:
        logger.error(f"\n❌ Missing files: {', '.join(missing_files)}")
        all_good = False
    else:
        logger.info("\n✅ All files present")
    
    # Check credentials
    creds_ok = check_credentials()
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    if all_good and creds_ok:
        logger.info("✅ System is ready to use!")
        logger.info("\nNext steps:")
        logger.info("1. Ensure credentials.json is in place")
        logger.info("2. Update SPREADSHEET_ID in run_email_tracker.py")
        logger.info("3. Run: python run_email_tracker.py")
    elif all_good:
        logger.info("⚠️  System is mostly ready, but missing credentials")
        logger.info("\nNext steps:")
        logger.info("1. Get credentials.json from Google Cloud")
        logger.info("2. Update SPREADSHEET_ID in run_email_tracker.py")
        logger.info("3. Run: python run_email_tracker.py")
    else:
        logger.info("❌ System has issues to fix")
        logger.info("\nPlease fix the errors above and try again")
    logger.info("=" * 60)
    
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
