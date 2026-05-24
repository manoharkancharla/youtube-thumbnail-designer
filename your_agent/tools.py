import os
from tavily import TavilyClient


def search_web(query: str, max_results: int = 5) -> str:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=True,
    )
    parts = []
    if response.get("answer"):
        parts.append(f"Summary: {response['answer']}\n")
    for r in response.get("results", []):
        parts.append(f"- {r['title']}: {r['content'][:300]}")
    return "\n".join(parts)
