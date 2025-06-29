"""Core chatbot logic for the ArXiv Chatbot."""

import anthropic
import logging
from typing import List, Dict, Any, Optional

from config import config
from utils.logger import setup_logger
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
            logger.info("ArXiv Chatbot initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize chatbot: {str(e)}"
            logger.error(error_msg)
            raise ChatbotError(error_msg) from e
    
    def process_query(self, query: str) -> None:
        """
        Process a single user query and print the response.
        
        Args:
            query: User's question or request
            
        Raises:
            APIError: If API calls fail
            ChatbotError: If processing fails
        """
        if not query.strip():
            print("Please provide a valid query.")
            return
        
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            messages = [{'role': 'user', 'content': query}]
            
            # Initial API call
            response = self._call_api(messages)
            
            # Process the response and handle tool calls
            self._process_response(response, messages)
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
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
        try:
            response = self.client.messages.create(
                max_tokens=config.max_tokens,
                model=config.model_name,
                tools=self.tool_executor.tool_schemas,
                messages=messages
            )
            return response
        except anthropic.APIError as e:
            error_msg = f"Anthropic API error: {str(e)}"
            logger.error(error_msg)
            raise APIError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected API error: {str(e)}"
            logger.error(error_msg)
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
        
        try:
            result = self.tool_executor.execute_tool(tool_name, tool_args)
            logger.debug(f"Tool {tool_name} completed successfully")
            return result
        except ToolExecutorError as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(error_msg)
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
                print(f"\n❌ An unexpected error occurred: {str(e)}")
                print("Please try again or type 'quit' to exit.")
