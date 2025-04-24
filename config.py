import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")
AHREFS_API_KEY = os.getenv("AHREFS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Database Configuration
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

# Application Settings
DOMAIN = os.getenv("DOMAIN", "asendia.ai")
COMPETITORS = os.getenv("COMPETITORS", "").split(",")
TARGET_LOCALES = os.getenv("TARGET_LOCALES", "en-us").split(",")
USER_PROFILES = ["recruiter", "talent_acquisition", "hr_manager", "candidate"]
INDUSTRY_VERTICALS = ["tech", "healthcare", "finance", "retail", "manufacturing"]

# Content settings
MIN_WORD_COUNT = 1200
MAX_WORD_COUNT = 2500
CONTENT_UPDATE_FREQUENCY = 7  # days