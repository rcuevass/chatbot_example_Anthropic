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
        
        # Audit logging configuration
        self.enable_audit_logging = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
        self.audit_log_dir = Path(os.getenv("AUDIT_LOG_DIR", "logs/audit"))
        self.audit_log_retention_days = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90"))
        self.log_user_queries = os.getenv("LOG_USER_QUERIES", "true").lower() == "true"
        self.log_api_calls = os.getenv("LOG_API_CALLS", "true").lower() == "true"
        self.log_tool_executions = os.getenv("LOG_TOOL_EXECUTIONS", "true").lower() == "true"
        self.log_errors = os.getenv("LOG_ERRORS", "true").lower() == "true"
        
        # Privacy settings for audit logs
        self.hash_sensitive_data = os.getenv("HASH_SENSITIVE_DATA", "true").lower() == "true"
        self.mask_api_keys = os.getenv("MASK_API_KEYS", "true").lower() == "true"
        
        # Create paper directory if it doesn't exist
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        
        # Create audit log directory if audit logging is enabled
        if self.enable_audit_logging:
            self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        if self.audit_log_retention_days <= 0:
            raise ValueError("AUDIT_LOG_RETENTION_DAYS must be a positive integer")
    
    def get_topic_dir(self, topic: str) -> Path:
        """Get the directory path for a specific topic."""
        topic_name = topic.lower().replace(" ", "_").replace("/", "_")
        return self.paper_dir / topic_name
    
    def get_audit_config_summary(self) -> dict:
        """Get a summary of audit logging configuration."""
        return {
            "enabled": self.enable_audit_logging,
            "log_directory": str(self.audit_log_dir),
            "retention_days": self.audit_log_retention_days,
            "log_user_queries": self.log_user_queries,
            "log_api_calls": self.log_api_calls,
            "log_tool_executions": self.log_tool_executions,
            "log_errors": self.log_errors,
            "hash_sensitive_data": self.hash_sensitive_data,
            "mask_api_keys": self.mask_api_keys
        }

# Global configuration instance
config = Config()
