"""
Test settings for Time Manager project.
Uses SQLite for faster, simpler test execution.
"""
from time_mamager.settings import *

# Use SQLite for tests (faster and doesn't require MySQL permissions)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database for tests
    }
}

# Disable migrations for faster tests
# Tests will use syncdb-like approach
# Remove this if you want to test migrations
# Enabled by pytest.ini with --no-migrations flag

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug toolbar in tests
DEBUG = False

# Use a simpler logging configuration for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'CRITICAL',
        },
    },
}

# Use test secret key
SECRET_KEY = 'test-secret-key-for-testing-only'

# Disable unnecessary middleware in tests
# MIDDLEWARE = [m for m in MIDDLEWARE if 'SecurityMiddleware' not in m]
