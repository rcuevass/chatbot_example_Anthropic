"""Main entry point for the ArXiv Chatbot application."""

import sys
import logging
import signal
from pathlib import Path

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Received shutdown signal. Cleaning up...")
    sys.exit(0)

def main():
    """Main function to start the ArXiv Chatbot."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Import here to handle configuration errors gracefully
        from config import config
        from utils.logger import setup_logger
        from utils.audit_logger import cleanup_audit_logger
        from core.chatbot import ArxivChatbot, ChatbotError
        
        # Setup logging
        log_file = Path("logs") / "chatbot.log"
        logger = setup_logger("main", config.log_level, log_file=log_file)
        
        logger.info("Starting ArXiv Chatbot application")
        
        # Log audit configuration
        if config.enable_audit_logging:
            logger.info("Audit logging is enabled")
            logger.info(f"Audit configuration: {config.get_audit_config_summary()}")
        else:
            logger.info("Audit logging is disabled")
        
        # Initialize and start chatbot
        chatbot = ArxivChatbot()
        
        try:
            chatbot.start_chat_loop()
        except KeyboardInterrupt:
            logger.info("Chat loop interrupted by user")
            print("\n👋 Chat interrupted. Goodbye!")
        finally:
            # Cleanup audit logger
            if hasattr(chatbot, 'audit_logger') and chatbot.audit_logger:
                cleanup_audit_logger()
                logger.info("Audit logger cleaned up")
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start chatbot: {str(e)}")
        print("\nPlease check:")
        print("1. Your ANTHROPIC_API_KEY environment variable is set")
        print("2. You have an active internet connection")
        print("3. Your Python environment has all required dependencies")
        print("4. Your configuration settings are valid")
        
        # Log the error
        try:
            logger = logging.getLogger("main")
            logger.error(f"Application startup failed: {str(e)}")
        except:
            pass  # If logging fails, just continue with exit
        
        sys.exit(1)

if __name__ == "__main__":
    main()
