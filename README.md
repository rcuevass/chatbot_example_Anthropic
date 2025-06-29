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

## Configuration

Set these environment variables in your `.env` file:

- `ANTHROPIC_API_KEY` (required): Your Anthropic API key
- `PAPER_DIR` (optional): Directory for storing papers (default: "papers")
- `ANTHROPIC_MODEL` (optional): Claude model to use (default: "claude-3-haiku-20240307")
- `MAX_TOKENS` (optional): Max tokens per response (default: 2048)
- `LOG_LEVEL` (optional): Logging level (default: "INFO")

## License

MIT License
