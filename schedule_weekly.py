import schedule
import time
import subprocess
import logging
import os
from datetime import datetime

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
log_file = os.path.join(log_dir, f"scheduler_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_weekly_job():
    """Run the weekly SEO opportunity job"""
    logger.info("Running weekly SEO opportunity job...")
    
    try:
        # Run the opportunity tracker
        cmd = ["python", "main.py", "opportunity", "--export"]
        subprocess.run(cmd, check=True)
        
        logger.info("Weekly SEO opportunity job completed successfully")
    except Exception as e:
        logger.error(f"Error running weekly SEO opportunity job: {e}")

def main():
    """Main scheduler function"""
    # Schedule the job to run every Monday at 8:00
    schedule.every().monday.at("08:00").do(run_weekly_job)
    
    logger.info("Scheduler started, waiting for jobs...")
    
    # Run the job right away for initial execution
    run_weekly_job()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()