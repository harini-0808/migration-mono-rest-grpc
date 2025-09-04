from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    def __init__(self):
        self.env = os.getenv("ENV", "development").lower()
        self.is_production = self.env == "production"

        self.DATABASE_URL = os.getenv("DATABASE_URL")
        
        # Logging settings
        self.logs_dir = Path("logs")
        self.log_level = "INFO" if self.is_production else "DEBUG"
        
    @property
    def log_format(self):
        return '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'

# Create global settings instance
settings = Settings()