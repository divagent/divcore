import os
from tavily import AsyncTavilyClient
from app.service.ser_ai_rag import rag_query
tavily_client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


async def get_dividend_data_tool(tool_input: str):
    """
    Wrapper for the RAG service to ensure standardized output for the agent.
    """
    try:
        result = await rag_query(question=tool_input, top_k=3)
        
        if not result.get("sources"):
            return {"error": "No data found for this query in the dividend database."}
            
        return {
            "data": result["answer"],
            "sources": result["sources"]
        }
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
    
    


async def search_web_tool(query: str):
    """
    Searches the live web for news, macro trends, and recent financial events.
    """
    try:
        # 'search_depth="advanced"' provides more detailed context for financial analysis
        search_result = await tavily_client.search(query, search_depth="advanced", max_results=3)
        
        # We clean the output so the LLM doesn't get overwhelmed with raw JSON
        results = search_result.get("results", [])
        cleaned_context = "\n\n".join([
            f"Source: {r['url']}\nContent: {r['content']}" 
            for r in results
        ])
        
        return {"data": cleaned_context}
    except Exception as e:
        return {"error": f"Web search failed: {str(e)}"}
    
   