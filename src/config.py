"""
Application configuration classes
"""

import os
from typing import Optional


class Config:
    """Base configuration"""
    
    # Flask core
    SECRET_KEY: Optional[str] = None
    
    # Security
    FORCE_HTTPS: bool = False
    
    # Database
    USE_DATABASE: bool = True
    
    # Redis
    USE_REDIS: bool = False
    REDIS_URL: str = 'redis://localhost:6379'
    
    # Rate limiting
    RATELIMIT_ENABLED: bool = True
    RATELIMIT_STORAGE_URL: Optional[str] = None
    RATELIMIT_STRATEGY: str = 'fixed-window'
    RATELIMIT_DEFAULT: str = '200 per day;50 per hour'
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # External APIs
    GEMINI_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    
    # Session
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # CSRF Protection
    WTF_CSRF_TIME_LIMIT: int = 7200  # 2 hours (in seconds)
    
    @classmethod
    def init_from_env(cls):
        """Initialize configuration from environment variables"""
        config = cls()
        
        # Flask core
        secret_key = os.getenv('FLASK_SECRET_KEY', '')
        invalid_keys = {
            '',
            'your-secret-key-change-in-production',
            'change_me',
            'changeme',
            'change_me_to_a_secure_random_value',
        }
        if not secret_key or secret_key.strip().lower() in invalid_keys:
            raise RuntimeError('FLASK_SECRET_KEY environment variable must be set to a secure value')
        config.SECRET_KEY = secret_key
        
        # Security
        config.FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'False').lower() == 'true'
        
        # Database
        config.USE_DATABASE = os.getenv('USE_DATABASE', 'True').lower() == 'true'
        
        # Redis
        config.USE_REDIS = os.getenv('USE_REDIS', 'False').lower() == 'true'
        config.REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        if config.USE_REDIS:
            config.RATELIMIT_STORAGE_URL = config.REDIS_URL
        else:
            config.RATELIMIT_STORAGE_URL = 'memory://'
        
        # OAuth
        config.GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
        config.GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
        
        # External APIs
        config.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        config.WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
        
        return config


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    FORCE_HTTPS = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    USE_DATABASE = False
    USE_REDIS = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-testing-only'


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration instance based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = config_map.get(config_name, DevelopmentConfig)
    return config_class.init_from_env()
