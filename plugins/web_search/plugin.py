"""
Web Search plugin - Search the web for real-time information.
"""
import os
import aiohttp
from typing import Dict, Any, Optional, List
from duckduckgo_search import DDGS

from src.tools.base import BaseTool, ToolDefinition
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class WebSearchTool(BaseTool):
    """Web search tool with multiple provider support."""
    
    def __init__(self, provider: str = "duckduckgo", **kwargs):
        """
        Initialize web search tool.
        
        Args:
            provider: Search provider (google, duckduckgo, brave, searxng)
            **kwargs: Provider-specific configuration
        """
        self.provider = provider.lower()
        self.config = kwargs
        logger.info(f"Web search tool initialized with provider: {self.provider}")
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name="web_search",
            description="**ALWAYS use this tool for ANY factual questions, current events, dates, statistics, or information you're unsure about.** This tool searches the web in real-time for accurate, up-to-date information. If asked about anything factual or current, use this FIRST before making claims. Search for: news, facts, dates, people, places, events, products, statistics, or any information that might change.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query - be specific and detailed for better results"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-10, default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> str:
        """
        Execute web search.
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            Formatted search results
        """
        logger.info(f"Executing web search: {query} (provider: {self.provider})")
        
        try:
            if self.provider == "duckduckgo":
                results = await self._search_duckduckgo(query, num_results)
            elif self.provider == "google":
                results = await self._search_google(query, num_results)
            elif self.provider == "brave":
                results = await self._search_brave(query, num_results)
            elif self.provider == "searxng":
                results = await self._search_searxng(query, num_results)
            else:
                return f"Error: Unknown search provider '{self.provider}'"
            
            return self._format_results(results)
        
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Error performing search: {str(e)}"
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Search using DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                return [
                    {
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    async def _search_google(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Search using Google Custom Search API."""
        api_key = os.getenv('GOOGLE_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')
        
        if not api_key or not cse_id:
            raise ValueError("Google API key or CSE ID not configured")
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'num': min(num_results, 10)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if 'items' not in data:
                    return []
                
                return [
                    {
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    }
                    for item in data['items']
                ]
    
    async def _search_brave(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Search using Brave Search API."""
        api_key = os.getenv('BRAVE_API_KEY')
        
        if not api_key:
            raise ValueError("Brave API key not configured")
        
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            'X-Subscription-Token': api_key
        }
        params = {
            'q': query,
            'count': num_results
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                if 'web' not in data or 'results' not in data['web']:
                    return []
                
                return [
                    {
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('description', '')
                    }
                    for item in data['web']['results']
                ]
    
    async def _search_searxng(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Search using SearXNG instance."""
        searxng_url = os.getenv('SEARXNG_URL', 'http://localhost:8080')
        
        url = f"{searxng_url}/search"
        params = {
            'q': query,
            'format': 'json',
            'pageno': 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if 'results' not in data:
                    return []
                
                results = data['results'][:num_results]
                return [
                    {
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('content', '')
                    }
                    for item in results
                ]
    
    def _format_results(self, results: List[Dict[str, str]]) -> str:
        """Format search results as a string."""
        if not results:
            return "No results found."
        
        formatted = "Search Results:\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   URL: {result['url']}\n"
            formatted += f"   {result['snippet']}\n\n"
        
        return formatted.strip()


class Plugin:
    """Main plugin class."""
    
    def __init__(self):
        """Initialize the plugin."""
        # Get search provider from config
        from src.config.manager import ConfigManager
        config = ConfigManager()
        provider = config.get('tools.web_search.default_provider', 'searxng')
        
        self.tools = [WebSearchTool(provider=provider)]
    
    def get_tools(self):
        """Get tools provided by this plugin."""
        return self.tools
    
    def cleanup(self):
        """Cleanup when plugin is unloaded."""
        pass
