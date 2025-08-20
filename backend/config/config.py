import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    MONGODB_URI = os.getenv("MONGO_URI")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

    # Pinecone configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "student-chatbot")
    
    # Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("EMAIL_USER")
    # Clean the password to remove any non-breaking spaces or other Unicode issues
    _raw_password = os.getenv("EMAIL_PASS")
    MAIL_PASSWORD = _raw_password.replace('\xa0', ' ').replace('\u00a0', ' ') if _raw_password else None
    MAIL_DEFAULT_SENDER = os.getenv("EMAIL_USER")
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = False
    
    # Ensure UTF-8 encoding for emails
    MAIL_USE_SSL = False
    MAIL_DEBUG = False
    
    # LangChain configuration
    LANGCHAIN_TRACING_V2 = "true"
    LANGCHAIN_PROJECT = "Faculty Chatbot"
    LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
    
    # Session management
    SESSION_CLEANUP_INTERVAL = 3600  # Cleanup every hour
    SESSION_TIMEOUT = 7200  # Session timeout after 2 hours
    
    # Admin credentials
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "admin123"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

# Dictionary to easily access configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
