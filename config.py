"""
Configuration module for the Telegram Bot.

Loads all necessary settings from environment variables (.env file)
and provides them as easily accessible constants within a Config class.
It also defines the various states (modes) the bot can be in.
"""
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Holds all configuration variables for the application.
    
    Attributes are loaded from environment variables. Includes a validation
    method to ensure all critical settings are present before starting.
    """
    
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH')
    
    # Google Sheets Configuration
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    DEFAULT_SPREADSHEET_ID = os.getenv('DEFAULT_SPREADSHEET_ID')
    DEFAULT_SHEET_NAME = os.getenv('DEFAULT_SHEET_NAME', 'Sheet1')
    
    # Bot State Configuration
    STATE_FILE = os.getenv('STATE_FILE', 'user_states.json')
    
    # Mandatory Header Configuration
    MANDATORY_HEADER = "timestamp"
    
    # Bot Modes / States
    IDLE_MODE = "idle"
    INPUT_MODE = "input"
    
    # Header CRUD states
    AWAITING_HEADER_ADD = "awaiting_header_add"
    AWAITING_HEADER_RENAME_NEW_NAME = "awaiting_header_rename_new_name"

    # Data CRUD states
    AWAITING_UPDATED_ROW_TEXT = "awaiting_updated_row_text"
    
    @classmethod
    def validate(cls):
        """
        Validates that all required environment variables are set.
        
        Raises:
            ValueError: If any of the essential configuration variables are missing.
        """
        required_vars = [
            ('BOT_TOKEN', cls.BOT_TOKEN),
            ('API_ID', cls.API_ID),
            ('API_HASH', cls.API_HASH),
            ('GOOGLE_CREDENTIALS_FILE', cls.GOOGLE_CREDENTIALS_FILE),
            ('DEFAULT_SPREADSHEET_ID', cls.DEFAULT_SPREADSHEET_ID)
        ]
        
        missing_vars = [name for name, value in required_vars if not value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True