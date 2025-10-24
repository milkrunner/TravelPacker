"""
Web application entry point for NikNotes
Flask-based web interface for the trip packing assistant

This module uses the application factory pattern for better testability
and configuration management.
"""

import os
from dotenv import load_dotenv

# Load environment variables before creating app
load_dotenv()

# Import application factory
from src.factory import create_app

# Create application instance
app = create_app(config_name=os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run the development server
    debug_mode = app.config.get('DEBUG', False)
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
