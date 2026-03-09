#!/usr/bin/env python3
"""
Clean startup script for email tracker that ignores inherited PYTHONPATH.
"""
import sys
import os

# Remove any problematic paths from sys.path
sys.path = [p for p in sys.path if 'onit-oauth' not in p]

# Add the src directory
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now run the actual email tracker
if __name__ == '__main__':
    from email_tracker.app import EmailTrackerApp
    from pathlib import Path
    import asyncio
    import threading
    import logging
    
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
    
    def main():
        from pathlib import Path
        
        logger.info("Starting Email Tracker App...")
        try:
            # Configuration
            SPREADSHEET_ID = "1hSzXPnf3_AVg0NCA3fACSeYPHdh6-04yHAVwPp_cCGY"
            DOC_FILE_NAME = "FAQs for UP Alumni Email.docx"
            DASHBOARD_PORT = 8001
            EMAIL_CHECK_INTERVAL_MINUTES = 1  # Check every minute for fast replies
            
            # Use absolute path for credentials
            project_dir = Path(__file__).parent
            credentials_path = str(project_dir / "credentials.json")
            
            # Check if credentials exist
            if not Path(credentials_path).exists():
                logger.error(f"❌ Credentials file not found at: {credentials_path}")
                logger.info("📋 To set up credentials:")
                logger.info("   1. Go to: https://console.cloud.google.com/")
                logger.info("   2. Create OAuth 2.0 credentials (Desktop App)")
                logger.info("   3. Download as JSON and save as credentials.json")
                logger.info("   4. Place the file in: " + str(project_dir))
                return
            
            app = EmailTrackerApp(
                spreadsheet_id=SPREADSHEET_ID,
                doc_file_name=DOC_FILE_NAME,
                dashboard_port=DASHBOARD_PORT,
                credentials_file=credentials_path
            )
            logger.info("Email Tracker App created successfully")
            
            # Start scheduler in a separate thread
            scheduler_thread = threading.Thread(
                target=run_scheduler_thread, 
                args=(app, EMAIL_CHECK_INTERVAL_MINUTES),  # Use configured interval
                daemon=True
            )
            scheduler_thread.start()
            logger.info(f"Scheduler thread started (checking every {EMAIL_CHECK_INTERVAL_MINUTES} minutes)")
            
            # Start the dashboard in a separate thread
            def run_dashboard():
                import uvicorn
                logger.info(f"Starting dashboard on http://localhost:{DASHBOARD_PORT}")
                uvicorn.run(
                    app.dashboard.app,
                    host="127.0.0.1",
                    port=DASHBOARD_PORT,
                    log_level="info"
                )
            
            dashboard_thread = threading.Thread(target=run_dashboard, daemon=False)
            dashboard_thread.start()
            logger.info(f"Dashboard thread started on port {DASHBOARD_PORT}")
            
            # Keep main thread alive
            root_path = Path(__file__).parent
            app.log_file = root_path / "email_tracker.log"
            
            logger.info("=" * 60)
            logger.info(f"✅ Email Tracker is running!")
            logger.info(f"📊 Dashboard: http://localhost:{DASHBOARD_PORT}")
            logger.info(f"📧 Checking emails every {EMAIL_CHECK_INTERVAL_MINUTES} minutes")
            logger.info(f"📝 Logging to: {SPREADSHEET_ID}")
            logger.info("=" * 60)
            
            while True:
                try:
                    threading.Event().wait(1)
                except KeyboardInterrupt:
                    logger.info("Email Tracker stopped by user")
                    break
            
            # Keep main thread alive
            root_path = Path(__file__).parent
            app.log_file = root_path / "email_tracker.log"
            
            while True:
                try:
                    threading.Event().wait(1)
                except KeyboardInterrupt:
                    logger.info("Email Tracker App stopped by user")
                    break
        except Exception as e:
            logger.error(f"Error in main: {e}", exc_info=True)
            raise
    
    if __name__ == '__main__':
        main()
