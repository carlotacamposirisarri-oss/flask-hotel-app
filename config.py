"""
Flask configuration settings for the Hotel Finder app.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Amadeus API Configuration
    AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
    AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
    AMADEUS_API_BASE_URL = "https://api.amadeus.com"
    AMADEUS_API_VERSION = "v2"

    # Hotel filtering criteria
    MIN_STAR_RATING = 5  # Only 5-star hotels
    MIN_REVIEW_SCORE = 4.8  # Minimum review score
    MAX_RESULTS = 10  # Maximum hotels per city

    # Request configuration
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True
    AMADEUS_CLIENT_ID = "test-client-id"
    AMADEUS_CLIENT_SECRET = "test-client-secret"


# Select configuration based on environment
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

current_config = config.get(os.getenv("FLASK_ENV", "development"), DevelopmentConfig)
