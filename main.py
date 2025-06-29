"""Main entry point for the ArXiv Chatbot application."""

import sys
import logging
from pathlib import Path

def main():
    """Main function to start the ArXiv Chatbot."""
    try:
        # Import here to handle configuration errors gracefully
        from config import config
        from utils.logger import setup_logger
        from core.chatbot import ArxivChatbot, ChatbotError
        
        # Setup logging
        log_file = Path("logs") / "chatbot.log"
        logger = setup_logger("main", config.log_level, log_file)
        
        logger.info("Starting ArXiv Chatbot application")
        
        # Initialize and start chatbot
        chatbot = ArxivChatbot()
        chatbot.start_chat_loop()
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start chatbot: {str(e)}")
        print("\nPlease check:")
        print("1. Your ANTHROPIC_API_KEY environment variable is set")
        print("2. You have an active internet connection")
        print("3. Your Python environment has all required dependencies")
        sys.exit(1)

if __name__ == "__main__":
    main()
