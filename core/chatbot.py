"""Core chatbot logic for the ArXiv Chatbot."""

import anthropic
import logging
import time
from typing import List, Dict, Any, Optional, Union

from config import config
from utils.logger import setup_logger
from utils.audit_logger import get_audit_logger, cleanup_audit_logger
from core.tool_executor import ToolExecutor, ToolExecutorError

logger = setup_logger(__name__, config.log_level)

class ChatbotError(Exception):
    """Base exception for chatbot errors."""
    pass

class APIError(ChatbotError):
    """Exception raised when API calls fail."""
    pass

class ArxivChatbot:
    """ArXiv research chatbot with tool capabilities."""
    
    def __init__(self):
        """Initialize the chatbot with Anthropic client and tool executor."""
        try:
            self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            self.tool_executor = ToolExecutor()
            
            # Initialize audit logger if enabled
            self.audit_logger = None
            if config.enable_audit_logging:
                self.audit_logger = get_audit_logger(config.audit_log_dir)
                logger.info("Audit logging enabled")
                logger.info(f"Audit config: {config.get_audit_config_summary()}")
            
            logger.info("ArXiv Chatbot initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize chatbot: {str(e)}"
            logger.error(error_msg)
            
            # Log initialization error to audit log
            if self.audit_logger:
                self.audit_logger.log_error("chatbot", "initialization", error_msg)
            
            raise ChatbotError(error_msg) from e
    
    def process_query(self, query: str, user_id: Optional[str] = None) -> None:
        """
        Process a single user query and print the response.
        
        Args:
            query: User's question or request
            user_id: Optional user identifier for audit tracking
            
        Raises:
            APIError: If API calls fail
            ChatbotError: If processing fails
        """
        if not query.strip():
            print("Please provide a valid query.")
            return
        
        logger.info(f"Processing query: {query[:100]}...")
        
        # Log user query for audit
        query_event_id = None
        if self.audit_logger and config.log_user_queries:
            query_event_id = self.audit_logger.log_user_query(query, user_id)
        
        try:
            messages = [{"role": "user", "content": query}]
            
            # Initial API call
            response = self._call_api(messages)
            
            # Process the response and handle tool calls
            self._process_response(response, messages)
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            
            # Log error for audit
            if self.audit_logger and config.log_errors:
                self.audit_logger.log_error("chatbot", "process_query", error_msg)
            
            print(f"Sorry, I encountered an error: {error_msg}")
            raise ChatbotError(error_msg) from e
    
    def _call_api(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Make an API call to Anthropic.
        
        Args:
            messages: Conversation messages
            
        Returns:
            API response
            
        Raises:
            APIError: If API call fails
        """
        start_time = time.time()
        
        try:
            # Convert messages to proper format for Anthropic API
            formatted_messages = []
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                else:
                    formatted_messages.append(msg)
            
            response = self.client.messages.create(
                max_tokens=config.max_tokens,
                model=config.model_name,
                tools=self.tool_executor.tool_schemas,
                messages=formatted_messages
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log API call for audit
            if self.audit_logger and config.log_api_calls:
                self.audit_logger.log_api_call(
                    model=config.model_name,
                    max_tokens=config.max_tokens,
                    tool_count=len(self.tool_executor.tool_schemas),
                    message_count=len(messages),
                    duration_ms=duration_ms,
                    success=True
                )
            
            return response
            
        except anthropic.APIError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Anthropic API error: {str(e)}"
            logger.error(error_msg)
            
            # Log API error for audit
            if self.audit_logger and config.log_errors:
                self.audit_logger.log_api_call(
                    model=config.model_name,
                    max_tokens=config.max_tokens,
                    tool_count=len(self.tool_executor.tool_schemas),
                    message_count=len(messages),
                    duration_ms=duration_ms,
                    success=False,
                    error_message=error_msg
                )
            
            raise APIError(error_msg) from e
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected API error: {str(e)}"
            logger.error(error_msg)
            
            # Log unexpected error for audit
            if self.audit_logger and config.log_errors:
                self.audit_logger.log_error("api", "anthropic_call", error_msg)
            
            raise APIError(error_msg) from e
    
    def _process_response(self, response: Any, messages: List[Dict[str, Any]]) -> None:
        """
        Process API response and handle tool calls iteratively.
        
        Args:
            response: API response to process
            messages: Conversation messages to update
        """
        process_query = True
        
        while process_query:
            assistant_content = []
            has_tool_calls = False
            
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                    
                elif content.type == 'tool_use':
                    has_tool_calls = True
                    assistant_content.append(content)
                    
                    # Execute the tool
                    tool_result = self._execute_tool(content)
                    
                    # Add assistant message with tool use
                    messages.append({'role': 'assistant', 'content': assistant_content})
                    
                    # Add tool result message
                    messages.append({
                        "role": "user", 
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result
                        }]
                    })
                    
                    # Get next response
                    response = self._call_api(messages)
                    break
            
            # If no tool calls and we have text response, we're done
            if not has_tool_calls and any(c.type == 'text' for c in response.content):
                process_query = False
    
    def _execute_tool(self, tool_content: Any) -> str:
        """
        Execute a tool and return the result.
        
        Args:
            tool_content: Tool use content from API response
            
        Returns:
            Tool execution result as string
        """
        tool_name = tool_content.name
        tool_args = tool_content.input
        tool_id = tool_content.id
        
        print(f"🔧 Calling tool '{tool_name}' with args: {tool_args}")
        logger.info(f"Executing tool: {tool_name} (ID: {tool_id})")
        
        start_time = time.time()
        
        try:
            result = self.tool_executor.execute_tool(tool_name, tool_args)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.debug(f"Tool {tool_name} completed successfully")
            
            # Log tool execution for audit
            if self.audit_logger and config.log_tool_executions:
                self.audit_logger.log_tool_execution(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    duration_ms=duration_ms,
                    success=True
                )
                
                # Log tool result
                self.audit_logger.log_tool_result(
                    tool_name=tool_name,
                    result_size=len(result),
                    result_type="text"
                )
            
            return result
            
        except ToolExecutorError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(error_msg)
            
            # Log tool execution error for audit
            if self.audit_logger and config.log_errors:
                self.audit_logger.log_tool_execution(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    duration_ms=duration_ms,
                    success=False,
                    error_message=error_msg
                )
            
            return error_msg
    
    def start_chat_loop(self) -> None:
        """
        Start the interactive chat loop.
        """
        print("🤖 ArXiv Research Chatbot")
        print("=" * 40)
        print("Ask me about arXiv papers! Type 'quit', 'exit', or 'q' to stop.")
        print("Examples:")
        print("  - Search for 3 papers on 'quantum computing'")
        print("  - Tell me about paper 2412.07992v3")
        print()
        
        # Log session start for audit
        if self.audit_logger:
            self.audit_logger.log_security_event(
                "Chat session started",
                severity="info",
                details={"session_type": "interactive_chat"}
            )
        
        while True:
            try:
                query = input("\n💬 Your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Happy researching!")
                    break
                
                if not query:
                    print("Please enter a question or 'quit' to exit.")
                    continue
                
                print("\n🤔 Processing...")
                self.process_query(query)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in chat loop: {str(e)}")
                
                # Log unexpected error for audit
                if self.audit_logger and config.log_errors:
                    self.audit_logger.log_error("chatbot", "chat_loop", str(e))
                
                print(f"\n❌ An unexpected error occurred: {str(e)}")
                print("Please try again or type 'quit' to exit.")
        
        # Log session end for audit
        if self.audit_logger:
            self.audit_logger.log_security_event(
                "Chat session ended",
                severity="info",
                details={"session_type": "interactive_chat"}
            )
    
    def __del__(self):
        """Cleanup when the chatbot is destroyed."""
        if self.audit_logger:
            cleanup_audit_logger()
