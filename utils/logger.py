"""Logging configuration for the ArXiv Chatbot."""

import logging
import sys
import time
import functools
from typing import Optional, Callable, Any, ContextManager
from pathlib import Path
from enum import Enum

class VerbosityLevel(Enum):
    """Verbosity levels for logging."""
    MINIMAL = "minimal"      # Only errors and critical info
    NORMAL = "normal"        # Standard info, warnings, errors
    VERBOSE = "verbose"      # Detailed info including timing
    DEBUG = "debug"          # All details including function calls

def setup_logger(
    name: str = "arxiv_chatbot",
    level: str = "INFO",
    verbosity: VerbosityLevel = VerbosityLevel.VERBOSE,
    log_file: Optional[Path] = None,
    enable_timing: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbosity: Verbosity level controlling log detail
        log_file: Optional path to log file
        enable_timing: Whether to enable execution timing logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Adjust log level based on verbosity
    effective_level = _get_effective_level(level, verbosity)
    logger.setLevel(effective_level)
    
    # Create formatters based on verbosity
    console_formatter = _create_formatter(verbosity, include_timing=enable_timing)
    file_formatter = _create_formatter(verbosity, include_timing=enable_timing, is_file=True)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(effective_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Store verbosity and timing settings in logger for use by decorators
    setattr(logger, 'verbosity', verbosity)
    setattr(logger, 'enable_timing', enable_timing)
    
    return logger

def _get_effective_level(level: str, verbosity: VerbosityLevel) -> int:
    """Get effective logging level based on base level and verbosity."""
    base_level = getattr(logging, level.upper())
    
    if verbosity == VerbosityLevel.MINIMAL:
        return max(base_level, logging.WARNING)
    elif verbosity == VerbosityLevel.NORMAL:
        return base_level
    elif verbosity == VerbosityLevel.VERBOSE:
        return min(base_level, logging.INFO)
    elif verbosity == VerbosityLevel.DEBUG:
        return logging.DEBUG
    
    return base_level

def _create_formatter(verbosity: VerbosityLevel, include_timing: bool = True, is_file: bool = False) -> logging.Formatter:
    """Create a formatter based on verbosity level."""
    if verbosity == VerbosityLevel.MINIMAL:
        format_str = '%(levelname)s: %(message)s'
    elif verbosity == VerbosityLevel.NORMAL:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    elif verbosity == VerbosityLevel.VERBOSE:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    else:  # DEBUG
        format_str = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d:%(funcName)s] - %(message)s'
    
    if include_timing and verbosity in [VerbosityLevel.VERBOSE, VerbosityLevel.DEBUG]:
        format_str = '%(asctime)s.%(msecs)03d - ' + format_str.split(' - ', 1)[1]
    
    return logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')

def log_execution_time(logger: Optional[logging.Logger] = None, operation_name: Optional[str] = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger instance to use (if None, will try to get from function module)
        operation_name: Custom name for the operation (if None, uses function name)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get logger if not provided
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger
            
            # Check if timing is enabled
            if not getattr(func_logger, 'enable_timing', False):
                return func(*args, **kwargs)
            
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            # Log start if verbose enough
            if func_logger.level <= logging.INFO:
                func_logger.info(f"Starting operation: {op_name}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log completion with timing
                if func_logger.level <= logging.INFO:
                    func_logger.info(f"Completed operation: {op_name} (took {execution_time:.3f}s)")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                func_logger.error(f"Failed operation: {op_name} after {execution_time:.3f}s - {str(e)}")
                raise
        
        return wrapper
    return decorator

def log_function_call(logger: Optional[logging.Logger] = None, include_args: bool = False):
    """
    Decorator to log function calls with optional argument details.
    
    Args:
        logger: Logger instance to use
        include_args: Whether to include function arguments in logs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger
            
            # Only log if debug level is enabled
            if func_logger.level <= logging.DEBUG:
                if include_args:
                    args_str = ", ".join([repr(arg) for arg in args])
                    kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
                    all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                    func_logger.debug(f"Calling {func.__name__}({all_args})")
                else:
                    func_logger.debug(f"Calling {func.__name__}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def create_timed_logger(name: str, operation: str, logger: Optional[logging.Logger] = None) -> ContextManager:
    """
    Create a context manager for timing operations.
    
    Args:
        name: Logger name
        operation: Operation name to log
        logger: Logger instance to use
    
    Returns:
        Context manager for timing operations
    """
    if logger is None:
        logger = logging.getLogger(name)
    
    class TimedLogger:
        def __init__(self, logger: logging.Logger, operation: str):
            self.logger = logger
            self.operation = operation
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            if self.logger.level <= logging.INFO:
                self.logger.info(f"Starting: {self.operation}")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start_time is not None:
                execution_time = time.time() - self.start_time
                if exc_type is None:
                    if self.logger.level <= logging.INFO:
                        self.logger.info(f"Completed: {self.operation} (took {execution_time:.3f}s)")
                else:
                    self.logger.error(f"Failed: {self.operation} after {execution_time:.3f}s - {str(exc_val)}")
    
    return TimedLogger(logger, operation)
