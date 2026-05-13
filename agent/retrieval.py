"""
agent/retrieval.py
===================
Handles external web intelligence via the Tavily API.
Transforms raw search data into a structured context for LLM consumption.
"""

import os
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
from tavily import TavilyClient

# Load Environment Configuration Variables
load_dotenv()

# ---------------------------------------------------------------------------
# CONFIGURATION & CLIENT INITIALIZATION
# ---------------------------------------------------------------------------

TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
MAX_SEARCH_RESULTS: int = 5
CONTENT_TRUNCATION_LIMIT: int = 1500

# Instantiate Search Client with safety validation fallback
if not TAVILY_API_KEY:
    raise ValueError("Critical Error: 'TAVILY_API_KEY' is missing from host environment.")

client: TavilyClient = TavilyClient(api_key=TAVILY_API_KEY)


# ---------------------------------------------------------------------------
# CORE SEARCH ENGINE LOGIC
# ---------------------------------------------------------------------------

def web_search(query: str) -> str:
    """
    Executes an advanced web search and formats results for RAG (Retrieval-Augmented Generation).
    Returns an error message wrapper if the API provider call execution fails.
    """
    try:
        response: dict = client.search(
            query=query,
            search_depth="advanced",
            max_results=MAX_SEARCH_RESULTS
        )
        
        results_list: List[dict] = response.get("results", [])
        return _format_search_results(results_list)

    except Exception as e:
        # Returns operational string error block so caller can delegate internal logic
        return f"Search Provider Error: {str(e)}"


# ---------------------------------------------------------------------------
# DATA SERIALIZATION HELPERS
# ---------------------------------------------------------------------------

def _format_search_results(results: List[Dict[str, Union[str, float]]]) -> str:
    """
    Serializes raw list objects into a structured context segment for clear LLM citation.
    """
    if not results:
        return "No relevant web results were found for this topic."

    formatted_entries: List[str] = []

    # Iterate through query findings and isolate required parameters
    for idx, item in enumerate(results, start=1):
        title: str = str(item.get("title", "Untitled")).strip()
        url: str = str(item.get("url", "#")).strip()
        
        # Pull text corpus content safely and apply max constraint truncation bounds
        raw_content: str = str(item.get("content", "No content available"))
        truncated_content: str = raw_content[:CONTENT_TRUNCATION_LIMIT].strip()

        # Build clean index item structure using variable array mapping
        entry: str = (
            f"--- SOURCE {idx} ---\n"
            f"TITLE: {title}\n"
            f"URL: {url}\n"
            f"CONTENT: {truncated_content}\n"
        )
        formatted_entries.append(entry)

    return "\n\n".join(formatted_entries)
