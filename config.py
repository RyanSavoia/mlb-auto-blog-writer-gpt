# config.py
import os

# Use environment variable in production, fallback for local development
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key-here')
