"""Configuration management for the ArXiv Chatbot."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the chatbot application."""
    
    def __init__(self):
        self.anthropic_api_key = self._get_required_env_var("ANTHROPIC_API_KEY")
        self.paper_dir = Path(os.getenv("PAPER_DIR", "papers"))
        self.model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2048"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Create paper directory if it doesn't exist
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate configuration
        self._validate_config()
    
    def _get_required_env_var(self, var_name: str) -> str:
        """Get a required environment variable or raise an error."""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value
    
    def _validate_config(self) -> None:
        """Validate the configuration."""
        if self.max_tokens <= 0:
            raise ValueError("MAX_TOKENS must be a positive integer")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    def get_topic_dir(self, topic: str) -> Path:
        """Get the directory path for a specific topic."""
        topic_name = topic.lower().replace(" ", "_").replace("/", "_")
        return self.paper_dir / topic_name

# Global configuration instance
config = Config()
