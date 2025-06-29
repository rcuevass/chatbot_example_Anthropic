"""ArXiv paper search and extraction tools."""

import arxiv
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__, config.log_level)

class ArxivToolsError(Exception):
    """Base exception for ArXiv tools."""
    pass

class PaperSearchError(ArxivToolsError):
    """Exception raised when paper search fails."""
    pass

class PaperExtractionError(ArxivToolsError):
    """Exception raised when paper extraction fails."""
    pass

def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
        
    Raises:
        PaperSearchError: If the search fails
    """
    try:
        logger.info(f"Searching for papers on topic: '{topic}' (max_results: {max_results})")
        
        if not topic.strip():
            raise PaperSearchError("Topic cannot be empty")
        
        if max_results <= 0 or max_results > 20:
            raise PaperSearchError("max_results must be between 1 and 20")
        
        # Create arXiv client and search
        client = arxiv.Client()
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = client.results(search)
        
        # Create directory for this topic
        topic_dir = config.get_topic_dir(topic)
        topic_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = topic_dir / "papers_info.json"
        
        # Load existing papers info
        papers_info = _load_papers_info(file_path)
        
        # Process each paper and add to papers_info  
        paper_ids = []
        for paper in papers:
            paper_id = paper.get_short_id()
            paper_ids.append(paper_id)
            
            paper_info = {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'summary': paper.summary,
                'pdf_url': paper.pdf_url,
                'published': str(paper.published.date())
            }
            papers_info[paper_id] = paper_info
            logger.debug(f"Added paper: {paper_id} - {paper.title}")
        
        # Save updated papers_info to json file
        _save_papers_info(file_path, papers_info)
        
        logger.info(f"Successfully found and saved {len(paper_ids)} papers to {file_path}")
        return paper_ids
        
    except arxiv.ArxivError as e:
        error_msg = f"ArXiv API error while searching for '{topic}': {str(e)}"
        logger.error(error_msg)
        raise PaperSearchError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error while searching for papers on '{topic}': {str(e)}"
        logger.error(error_msg)
        raise PaperSearchError(error_msg) from e

def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
        
    Raises:
        PaperExtractionError: If extraction fails due to system errors
    """
    try:
        logger.info(f"Extracting info for paper: {paper_id}")
        
        if not paper_id.strip():
            return "Paper ID cannot be empty."
        
        # Search through all topic directories
        if not config.paper_dir.exists():
            logger.warning(f"Paper directory {config.paper_dir} does not exist")
            return f"No saved information found for paper {paper_id}."
        
        for item in config.paper_dir.iterdir():
            if item.is_dir():
                file_path = item / "papers_info.json"
                if file_path.is_file():
                    try:
                        papers_info = _load_papers_info(file_path)
                        if paper_id in papers_info:
                            logger.info(f"Found paper {paper_id} in {file_path}")
                            return json.dumps(papers_info[paper_id], indent=2)
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {str(e)}")
                        continue
        
        logger.info(f"Paper {paper_id} not found in any topic directory")
        return f"No saved information found for paper {paper_id}."
        
    except Exception as e:
        error_msg = f"Unexpected error while extracting info for paper '{paper_id}': {str(e)}"
        logger.error(error_msg)
        raise PaperExtractionError(error_msg) from e

def _load_papers_info(file_path: Path) -> Dict[str, Any]:
    """Load papers info from JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_papers_info(file_path: Path, papers_info: Dict[str, Any]) -> None:
    """Save papers info to JSON file."""
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2, ensure_ascii=False)
