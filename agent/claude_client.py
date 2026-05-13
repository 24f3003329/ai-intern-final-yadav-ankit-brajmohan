"""
agent/claude_client.py
=====================
Orchestrates LLM interactions using the Anthropic API.
Handles prompt caching, and streaming responses.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Configuration
CLAUDE_MODEL = "claude-sonnet-4-5" 
MAX_TOKENS = 4000
TEMPERATURE = 0.3

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

RESEARCH_SYSTEM_PROMPT = """
You are an expert Senior Research Analyst. Your goal is to produce a high-quality, structured, and objective research report based on a user-provided topic and live web context.


### INSTRUCTIONS
1. **Synthesize, Don't Just Summarize:** Combine your internal knowledge with the provided Live Context. Prioritize the Live Context for recent events, statistics, and current trends to prove the MCP integration is working.
2. **Professional Tone:** Write in a formal, analytical, and objective tone. Avoid fluff or conversational filler.
3. **Structured Formatting:** You MUST use Markdown for the layout. Use hierarchical headers (##, ###), bullet points for readability, and bold text for key terms.

### REPORT STRUCTURE REQUIREMENTS
Please follow this exact structure:
- **# [Title of Research Topic]**
- **## Executive Summary**: A concise 3-4 sentence overview of the topic.
- **## Key Findings**: Use the live context to list the most critical and current facts or developments.
- **## Detailed Analysis**: Break this into 2-3 logical sub-sections relevant to the topic.
- **## Future Outlook/Trends**: Based on current data, what are the emerging trends?
- **## Sources & References**: List the specific URLs or sources provided in the Live Context to validate the research.

### CONSTRAINTS
- Do not mention that you are an AI or that you performed a search.
- If the context is insufficient, provide the best possible report while noting where data might be limited.
- Ensure the formatting is "clean" so it looks professional when converted to PDF.


### CITATION RULES
1. Every time you state a fact from the search results, add an inline clickable link immediately after the sentence using a number in brackets, like this: [1](URL).
2. At the very end of the report, add a "### Sources" section listing every URL used in the report so the user can verify them.



Final Report:
"""

def generate_research(topic: str, web_context: str = ""):
    """
    Generates a research report via Claude with streaming enabled.
    Returns a generator yielding text chunks for real-time UI updates.
    """

    message_content = [
        {
            "type": "text",
            "text": f"WEB CONTEXT DATA: {web_context}",
            "cache_control": {"type": "ephemeral"}
        },
        {
            "type": "text",
            "text": f"User Research Topic: {topic}"
        }
    ]

    try:
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=[{"type": "text", "text": RESEARCH_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": message_content}]
        ) as stream:
            for text_chunk in stream.text_stream:
                yield text_chunk

    except Exception as e:
        yield f"Claude API Error: {str(e)}"