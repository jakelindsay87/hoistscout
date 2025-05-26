"""Cron hook script for scheduled crawling."""

import os
import sys
import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_crawl import main as run_crawl_main

# Configure logging for cron
log_file = Path(__file__).parent / "cron_crawl.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def send_notification(subject: str, message: str, is_error: bool = False):
    """Send email notification about crawl status.
    
    Args:
        subject: Email subject
        message: Email body
        is_error: Whether this is an error notification
    """
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        notify_email = os.getenv("NOTIFY_EMAIL")
        
        if not all([smtp_server, smtp_user, smtp_pass, notify_email]):
            logger.warning("Email configuration incomplete, skipping notification")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = notify_email
        msg['Subject'] = f"[HoistScraper] {subject}"
        
        # Add timestamp and hostname
        hostname = os.getenv("HOSTNAME", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        body = f"""
HoistScraper Crawl Report
========================

Timestamp: {timestamp}
Hostname: {hostname}
Status: {'ERROR' if is_error else 'SUCCESS'}

{message}

---
This is an automated message from HoistScraper.
        """.strip()
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            
        logger.info(f"Notification sent: {subject}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")


async def cron_main():
    """Main function for cron execution."""
    start_time = datetime.now()
    logger.info("Starting scheduled crawl")
    
    try:
        # Get configuration from environment
        config_file = os.getenv("CRAWL_CONFIG", "sites.yml")
        analyze_terms = os.getenv("ANALYZE_TERMS", "false").lower() == "true"
        
        # Run the crawl
        await run_crawl_main(cfg=config_file, once=True, analyze_terms=analyze_terms)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        success_message = f"""
Crawl completed successfully!

Duration: {duration}
Configuration: {config_file}
Terms Analysis: {'Enabled' if analyze_terms else 'Disabled'}

Check the logs for detailed results.
        """.strip()
        
        logger.info(f"Scheduled crawl completed in {duration}")
        send_notification("Crawl Completed Successfully", success_message)
        
    except Exception as e:
        end_time = datetime.now()
        duration = end_time - start_time
        
        error_message = f"""
Crawl failed with error!

Duration: {duration}
Error: {str(e)}

Please check the logs for more details.
        """.strip()
        
        logger.error(f"Scheduled crawl failed after {duration}: {str(e)}")
        send_notification("Crawl Failed", error_message, is_error=True)
        
        # Re-raise the exception for proper exit code
        raise


def setup_cron_environment():
    """Setup environment variables and paths for cron execution."""
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    os.chdir(backend_dir)
    
    # Set default environment variables if not present
    env_defaults = {
        "CRAWL_CONFIG": "sites.yml",
        "ANALYZE_TERMS": "false",
        "OLLAMA_HOST": "http://localhost:11434",
        "CRAWL_CONCURRENCY": "8"
    }
    
    for key, default_value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
            logger.info(f"Set default environment variable: {key}={default_value}")


def health_check():
    """Perform basic health checks before running crawl."""
    logger.info("Performing health checks")
    
    # Check if Ollama is accessible
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        import httpx
        response = httpx.get(f"{ollama_host}/api/tags", timeout=10)
        if response.status_code == 200:
            logger.info("Ollama service is accessible")
        else:
            logger.warning(f"Ollama service returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not reach Ollama service: {str(e)}")
    
    # Check configuration file exists
    config_file = os.getenv("CRAWL_CONFIG", "sites.yml")
    if not Path(config_file).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    logger.info("Health checks completed")


if __name__ == "__main__":
    try:
        # Setup environment for cron execution
        setup_cron_environment()
        
        # Perform health checks
        health_check()
        
        # Run the crawl
        asyncio.run(cron_main())
        
    except KeyboardInterrupt:
        logger.info("Cron crawl interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error(f"Cron crawl failed: {str(e)}")
        sys.exit(1)
    
    logger.info("Cron crawl completed successfully")
    sys.exit(0) 