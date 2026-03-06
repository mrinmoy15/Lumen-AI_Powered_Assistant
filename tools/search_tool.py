"""tools/search_tool.py — DuckDuckGo web search tool."""
from langchain_community.tools import DuckDuckGoSearchRun

search_tool = DuckDuckGoSearchRun(region="us-en")
