"""Web search tools for evidence gathering."""

import re
from typing import Optional
from langchain_core.tools import tool


def get_web_search_tools():
    """Get web search tools."""
    
    @tool
    def web_search(query: str, num_results: int = 5) -> str:
        """Search the web for information.
        
        Args:
            query: Search query
            num_results: Number of results to return (default: 5)
            
        Returns:
            Search results with titles, URLs, and snippets
        """
        try:
            # Try DuckDuckGo first (no API key needed)
            from langchain_community.tools import DuckDuckGoSearchRun
            
            search = DuckDuckGoSearchRun()
            results = search.run(query)
            
            return results
            
        except Exception as e:
            return f"Search error: {str(e)}\n\n(Note: Web search requires internet connection)"
    
    @tool
    def fetch_url(url: str) -> str:
        """Fetch and extract text content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text content
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; TruthfulnessEvaluator/0.1)'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.post']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length] + "\n... (content truncated)"
            
            return text
            
        except Exception as e:
            return f"Error fetching URL: {str(e)}"
    
    return [web_search, fetch_url]


class WebEvidenceGatherer:
    """Gather evidence from web sources."""
    
    def __init__(self) -> None:
        tools = get_web_search_tools()
        self.search_tool = tools[0]  # web_search
        self.fetch_tool = tools[1]   # fetch_url
    
    async def gather_evidence(
        self, 
        claim: str, 
        max_results: int = 3
    ) -> list[dict]:
        """
        Gather evidence from web for a claim.
        
        Returns:
            List of evidence dictionaries
        """
        evidence = []
        
        # Search for the claim
        try:
            search_result = self.search_tool.invoke({"query": claim, "num_results": max_results})
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
        
        # DuckDuckGo returns text with embedded URLs
        # Parse by looking for URL patterns and associated text
        
        # Extract URLs from search results
        url_pattern = r'https?://[^\s\)\]\>\,]+'
        urls = re.findall(url_pattern, search_result)
        
        # Split text by URLs to get snippets
        parts = re.split(url_pattern, search_result)
        
        # Create evidence from search results
        for i, url in enumerate(urls[:max_results]):
            # Get the text before or after this URL as the snippet
            snippet = ""
            if i < len(parts):
                snippet = parts[i] if i > 0 else parts[i] if i < len(parts) else ""
            
            # Clean up snippet
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            # Take middle portion if too long
            if len(snippet) > 600:
                snippet = snippet[100:700]
            
            if snippet or url:
                evidence.append({
                    "source": url,
                    "source_type": "web",
                    "content": snippet or f"Search result for: {claim}",
                    "relevance": 0.6,
                    "fetched": False
                })
        
        # If no URLs found but we have text, use the whole result
        if not evidence and search_result:
            evidence.append({
                "source": "duckduckgo_search",
                "source_type": "web",
                "content": search_result[:1500],
                "relevance": 0.5,
                "fetched": False
            })
        
        # Fetch full content for top result if it's a real URL
        if evidence and evidence[0]["source"].startswith("http"):
            try:
                full_content = self.fetch_tool.invoke({"url": evidence[0]["source"]})
                if not full_content.startswith("Error"):
                    evidence[0]["content"] = full_content[:2000]
                    evidence[0]["fetched"] = True
                    evidence[0]["relevance"] = 0.8
            except Exception:
                pass  # Keep the snippet version
        
        return evidence
