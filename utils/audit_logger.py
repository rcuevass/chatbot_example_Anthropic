"""Audit logging for the ArXiv Chatbot - tracks user interactions, API calls, and tool executions."""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class AuditEventType(Enum):
    """Types of audit events."""
    USER_QUERY = "user_query"
    API_CALL = "api_call"
    TOOL_EXECUTION = "tool_execution"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"

@dataclass
class AuditEvent:
    """Represents an audit event with all relevant metadata."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    session_id: str
    user_id: Optional[str]
    component: str
    operation: str
    details: Dict[str, Any]
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogger:
    """Comprehensive audit logger for tracking all system interactions."""
    
    def __init__(self, log_dir: Path, session_id: Optional[str] = None):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory to store audit logs
            session_id: Unique session identifier
        """
        self.log_dir = log_dir
        self.session_id = session_id or str(uuid.uuid4())
        self.logger = self._setup_audit_logger()
        
        # Track session start
        self._log_session_start()
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Set up the audit logger with file and console handlers."""
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create audit log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for audit logs
        audit_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(audit_file)
        file_handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _log_session_start(self) -> None:
        """Log session start event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SESSION_START,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component="system",
            operation="session_start",
            details={"session_id": self.session_id}
        )
        self._write_event(event)
    
    def log_user_query(self, query: str, user_id: Optional[str] = None, 
                      ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
        """
        Log a user query event.
        
        Args:
            query: User's query text
            user_id: Optional user identifier
            ip_address: Optional IP address
            user_agent: Optional user agent string
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.USER_QUERY,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=user_id,
            component="chatbot",
            operation="user_query",
            details={
                "query": query,
                "query_length": len(query),
                "query_hash": str(hash(query))  # For privacy, log hash instead of full query
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        self._write_event(event)
        return event_id
    
    def log_api_call(self, model: str, max_tokens: int, tool_count: int, 
                    message_count: int, duration_ms: float, success: bool = True,
                    error_message: Optional[str] = None) -> str:
        """
        Log an API call event.
        
        Args:
            model: Model name used
            max_tokens: Maximum tokens requested
            tool_count: Number of tools available
            message_count: Number of messages in conversation
            duration_ms: API call duration in milliseconds
            success: Whether the call was successful
            error_message: Error message if call failed
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.API_CALL,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component="api",
            operation="anthropic_call",
            details={
                "model": model,
                "max_tokens": max_tokens,
                "tool_count": tool_count,
                "message_count": message_count,
                "api_provider": "anthropic"
            },
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        self._write_event(event)
        return event_id
    
    def log_tool_execution(self, tool_name: str, tool_args: Dict[str, Any], 
                          duration_ms: float, success: bool = True,
                          error_message: Optional[str] = None) -> str:
        """
        Log a tool execution event.
        
        Args:
            tool_name: Name of the tool executed
            tool_args: Arguments passed to the tool
            duration_ms: Execution duration in milliseconds
            success: Whether the execution was successful
            error_message: Error message if execution failed
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.TOOL_EXECUTION,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component="tools",
            operation=f"execute_{tool_name}",
            details={
                "tool_name": tool_name,
                "tool_args": tool_args,
                "arg_count": len(tool_args)
            },
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        self._write_event(event)
        return event_id
    
    def log_tool_result(self, tool_name: str, result_size: int, 
                       result_type: str = "text") -> str:
        """
        Log a tool result event.
        
        Args:
            tool_name: Name of the tool that produced the result
            result_size: Size of the result (e.g., character count)
            result_type: Type of result (text, json, etc.)
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.TOOL_RESULT,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component="tools",
            operation=f"result_{tool_name}",
            details={
                "tool_name": tool_name,
                "result_size": result_size,
                "result_type": result_type
            }
        )
        self._write_event(event)
        return event_id
    
    def log_error(self, component: str, operation: str, error_message: str,
                  error_type: str = "exception") -> str:
        """
        Log an error event.
        
        Args:
            component: Component where error occurred
            operation: Operation being performed
            error_message: Error message
            error_type: Type of error
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.ERROR,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component=component,
            operation=operation,
            details={
                "error_type": error_type,
                "error_message": error_message
            },
            success=False,
            error_message=error_message
        )
        self._write_event(event)
        return event_id
    
    def log_security_event(self, event_description: str, severity: str = "info",
                          details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a security-related event.
        
        Args:
            event_description: Description of the security event
            severity: Severity level (info, warning, critical)
            details: Additional details about the event
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            event_type=AuditEventType.SECURITY_EVENT,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component="security",
            operation="security_event",
            details={
                "description": event_description,
                "severity": severity,
                **(details or {})
            }
        )
        self._write_event(event)
        return event_id
    
    def _write_event(self, event: AuditEvent) -> None:
        """Write an audit event to the log file."""
        try:
            # Convert to dict and handle enum serialization
            event_dict = asdict(event)
            event_dict["event_type"] = event.event_type.value
            
            # Write as JSON for structured logging
            self.logger.info(json.dumps(event_dict, default=str))
        except Exception as e:
            # Fallback logging if JSON serialization fails
            self.logger.error(f"Failed to write audit event: {str(e)}")
    
    def end_session(self) -> None:
        """Log session end event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SESSION_END,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=None,
            component="system",
            operation="session_end",
            details={"session_id": self.session_id}
        )
        self._write_event(event)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Dictionary with session statistics
        """
        # This would typically query the audit log files
        # For now, return basic session info
        return {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "log_directory": str(self.log_dir)
        }

# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger(log_dir: Optional[Path] = None) -> AuditLogger:
    """
    Get or create the global audit logger instance.
    
    Args:
        log_dir: Directory for audit logs (uses default if None)
        
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        if log_dir is None:
            log_dir = Path("logs/audit")
        _audit_logger = AuditLogger(log_dir)
    return _audit_logger

def cleanup_audit_logger() -> None:
    """Clean up the global audit logger."""
    global _audit_logger
    if _audit_logger is not None:
        _audit_logger.end_session()
        _audit_logger = None 