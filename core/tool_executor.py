"""Tool execution logic for the ArXiv Chatbot."""

import json
import logging
from typing import Dict, Any, Callable, Union

from config import config
from utils.logger import setup_logger
from tools.arxiv_tools import search_papers, extract_info
from tools.schemas import TOOL_SCHEMAS

logger = setup_logger(__name__, config.log_level)

class ToolExecutorError(Exception):
    """Base exception for tool executor."""
    pass

class ToolNotFoundError(ToolExecutorError):
    """Exception raised when a tool is not found."""
    pass

class ToolExecutionError(ToolExecutorError):
    """Exception raised when tool execution fails."""
    pass

class ToolExecutor:
    """Handles tool mapping and execution."""
    
    def __init__(self):
        self._tool_mapping: Dict[str, Callable] = {
            "search_papers": search_papers,
            "extract_info": extract_info
        }
        
        # Validate that all tools in schemas have corresponding functions
        schema_tools = {tool["name"] for tool in TOOL_SCHEMAS}
        mapping_tools = set(self._tool_mapping.keys())
        
        if schema_tools != mapping_tools:
            missing_in_mapping = schema_tools - mapping_tools
            missing_in_schemas = mapping_tools - schema_tools
            
            error_parts = []
            if missing_in_mapping:
                error_parts.append(f"Missing in mapping: {missing_in_mapping}")
            if missing_in_schemas:
                error_parts.append(f"Missing in schemas: {missing_in_schemas}")
            
            raise ToolExecutorError(f"Tool schema and mapping mismatch: {'; '.join(error_parts)}")
    
    @property
    def available_tools(self) -> list:
        """Get list of available tool names."""
        return list(self._tool_mapping.keys())
    
    @property
    def tool_schemas(self) -> list:
        """Get tool schemas for API calls."""
        return TOOL_SCHEMAS
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
            
        Returns:
            String representation of the tool execution result
            
        Raises:
            ToolNotFoundError: If the tool is not found
            ToolExecutionError: If tool execution fails
        """
        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
        
        if tool_name not in self._tool_mapping:
            available = ", ".join(self.available_tools)
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found. Available tools: {available}"
            )
        
        try:
            # Get the tool function
            tool_function = self._tool_mapping[tool_name]
            
            # Execute the tool
            result = tool_function(**tool_args)
            
            # Convert result to string representation
            result_str = self._format_result(result)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            logger.debug(f"Tool result: {result_str[:200]}...")  # Log first 200 chars
            
            return result_str
            
        except TypeError as e:
            error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg) from e
    
    def _format_result(self, result: Any) -> str:
        """
        Format tool result as a string.
        
        Args:
            result: The result from tool execution
            
        Returns:
            String representation of the result
        """
        if result is None:
            return "The operation completed but didn't return any results."
        elif isinstance(result, list):
            return ', '.join(str(item) for item in result)
        elif isinstance(result, dict):
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return str(result)
