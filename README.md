# ArXiv Research Chatbot

A production-ready AI-powered chatbot for searching, analyzing, and discussing academic papers from arXiv.
Built with Anthropic's Claude API and designed for researchers, students, and academics.

This repo is motivated by, and heavily dependent on the
[MCP: Build Rich-Context AI Apps with Anthropic](https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic/) 
short DeepLearning.AI course. It is an attempt to have a modularized version of the chatbot and with production-ready
code.

## Features

- 🔍 **Smart Paper Search**: Search arXiv by topic with intelligent relevance ranking
- 📄 **Paper Information Extraction**: Get detailed information about specific papers
- 💾 **Local Storage**: Automatically saves paper metadata for faster future access
- 🤖 **AI-Powered Conversations**: Natural language interactions about research papers
- 🛡️ **Production-Ready**: Comprehensive error handling, logging, and configuration management
- ⏱️ **Execution Timing**: Built-in timing for performance monitoring
- 📊 **Verbose Logging**: Multiple verbosity levels for detailed debugging
- 🔐 **Audit Logging**: Comprehensive audit trail for compliance and security monitoring

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Run the chatbot**:
   ```bash
   python main.py
   ```

## Example Usage

```
💬 Your question: Search for 3 papers on "quantum computing"
🔧 Calling tool 'search_papers' with args: {'topic': 'quantum computing', 'max_results': 3}
I found 3 papers on quantum computing...

💬 Your question: Tell me about paper 2501.12345v1
🔧 Calling tool 'extract_info' with args: {'paper_id': '2501.12345v1'}
This paper discusses quantum error correction...
```

## Enhanced Logging

The chatbot includes a sophisticated logging system with multiple verbosity levels and execution timing:

### Verbosity Levels
- **Minimal**: Only warnings and errors
- **Normal**: Standard info, warnings, and errors
- **Verbose**: Detailed info with execution timing
- **Debug**: All details including function calls and arguments

### Timing Features
- **Function Decorators**: Use `@log_execution_time()` to automatically time function execution
- **Context Managers**: Use `create_timed_logger()` for timing code blocks
- **Function Call Logging**: Use `@log_function_call()` to log function invocations

### Example Usage
```python
from utils.logger import setup_logger, VerbosityLevel, log_execution_time

# Set up verbose logger with timing
logger = setup_logger("my_app", verbosity=VerbosityLevel.VERBOSE, enable_timing=True)

# Time a function execution
@log_execution_time(operation_name="Data Processing")
def process_data():
    # Your code here
    pass

# Time a code block
with create_timed_logger("my_app", "Database Query", logger):
    # Database operations
    pass
```

## Audit Logging System

The chatbot includes a comprehensive audit logging system designed for compliance, security monitoring, and performance analysis.

### Features

- **Session Tracking**: Complete session lifecycle tracking with unique session IDs
- **User Interaction Logging**: All user queries and system responses
- **API Call Monitoring**: Detailed tracking of Anthropic API calls with performance metrics
- **Tool Execution Logging**: Complete audit trail of tool executions and results
- **Error Tracking**: Comprehensive error logging with context and stack traces
- **Security Events**: Specialized logging for security-related events
- **Privacy Protection**: Configurable data masking and hashing for sensitive information

### Audit Event Types

- `user_query`: User interactions and queries
- `api_call`: Anthropic API calls with performance metrics
- `tool_execution`: Tool executions with arguments and results
- `tool_result`: Tool execution results and metadata
- `error`: System errors and exceptions
- `session_start/end`: Session lifecycle events
- `security_event`: Security-related events and alerts

### Configuration

Add these environment variables to your `.env` file for audit logging:

```bash
# Audit Logging Configuration
ENABLE_AUDIT_LOGGING=true                    # Enable/disable audit logging
AUDIT_LOG_DIR=logs/audit                    # Directory for audit logs
AUDIT_LOG_RETENTION_DAYS=90                 # Log retention period in days

# What to log
LOG_USER_QUERIES=true                       # Log user queries
LOG_API_CALLS=true                          # Log API calls
LOG_TOOL_EXECUTIONS=true                    # Log tool executions
LOG_ERRORS=true                             # Log errors

# Privacy Settings
HASH_SENSITIVE_DATA=true                    # Hash sensitive data in logs
MASK_API_KEYS=true                          # Mask API keys in logs
```

### Audit Log Format

Audit logs are stored in JSON format for easy parsing and analysis:

```json
{
  "event_id": "uuid",
  "event_type": "user_query",
  "timestamp": "2024-01-15T10:30:45.123456",
  "session_id": "session-uuid",
  "user_id": null,
  "component": "chatbot",
  "operation": "user_query",
  "details": {
    "query": "Search for quantum computing papers",
    "query_length": 32,
    "query_hash": "hash-value"
  },
  "duration_ms": null,
  "success": true,
  "error_message": null,
  "ip_address": null,
  "user_agent": null
}
```

### Audit Analysis Tools

The chatbot includes a comprehensive audit analysis tool for generating reports and insights:

#### Performance Metrics
```bash
# Generate performance report for last 7 days
python utils/audit_analyzer.py --report-type performance --days 7

# Export to file
python utils/audit_analyzer.py --report-type performance --days 7 --output reports/performance.json
```

#### Compliance Reports
```bash
# Generate compliance report for last 30 days
python utils/audit_analyzer.py --report-type compliance --days 30

# Export to file
python utils/audit_analyzer.py --report-type compliance --days 30 --output reports/compliance.json
```

#### Session Analysis
```bash
# Analyze specific session
python utils/audit_analyzer.py --report-type session --session-id "your-session-id"
```

### Programmatic Usage

```python
from utils.audit_analyzer import AuditAnalyzer
from pathlib import Path

# Create analyzer
analyzer = AuditAnalyzer(Path("logs/audit"))

# Get performance metrics
metrics = analyzer.get_performance_metrics(days=7)
print(f"API success rate: {metrics['performance']['api']['success_rate']:.2%}")

# Get compliance report
compliance = analyzer.get_compliance_report(days=30)
print(f"Total sessions: {compliance['summary']['total_sessions']}")

# Export reports
analyzer.export_report("performance", Path("reports/performance.json"), days=7)
analyzer.export_report("compliance", Path("reports/compliance.json"), days=30)
```

### Security and Privacy

The audit logging system includes several privacy and security features:

- **Data Hashing**: Sensitive data can be hashed instead of stored in plain text
- **API Key Masking**: API keys are automatically masked in logs
- **Configurable Logging**: Granular control over what gets logged
- **Retention Policies**: Automatic log cleanup based on configurable retention periods
- **Session Isolation**: Each session has a unique identifier for tracking

### Compliance Features

The audit system supports various compliance requirements:

- **Complete Audit Trail**: Every interaction is logged with timestamps
- **Session Tracking**: Full session lifecycle from start to end
- **Error Monitoring**: Comprehensive error tracking with context
- **Performance Metrics**: API call performance and success rates
- **Security Events**: Specialized logging for security incidents
- **Export Capabilities**: Easy export of audit data for external analysis

## Configuration

Set these environment variables in your `.env` file:

- `ANTHROPIC_API_KEY` (required): Your Anthropic API key
- `PAPER_DIR` (optional): Directory for storing papers (default: "papers")
- `ANTHROPIC_MODEL` (optional): Claude model to use (default: "claude-3-haiku-20240307")
- `MAX_TOKENS` (optional): Max tokens per response (default: 2048)
- `LOG_LEVEL` (optional): Logging level (default: "INFO")
- `LOG_VERBOSITY` (optional): Log verbosity level - minimal, normal, verbose, debug (default: "normal")
- `ENABLE_TIMING` (optional): Enable execution timing logs (default: "true")

## License

MIT License
