from llama_index.core.tools import FunctionTool
from services.target_structure_rag_service import TargetStructureRagService
from utils.file_cache import FileCache
import asyncio
from services.analysis_rag_service import AnalysisRagService

def create_query_target_structure_tool(rag_service: TargetStructureRagService) -> FunctionTool:
    """
    Factory for a target structure tool that uses the provided rag_service instance.
    """
    def query_target_structure_llamaIndex(query: str) -> str:
        try:
            query_engine = rag_service.get_query_engine()
            if not query_engine:
                return "Target structure system not initialized. Please ensure the RAG service is properly set up."
    
            enhanced_query = f"""
Analyze the microservices architecture and project file organization.
Based on the query below, return the file path (relative to the source directory) most relevant for context:
{query}

Guidelines:
- The answer should be a valid file path (e.g., "Services/CustomerService.cs" or "Models/Order.cs").
- Do not include additional commentary, just the file path.
"""
            response = query_engine.query(enhanced_query)
            return str(response).strip()
        except Exception as e:
            return f"Error searching target structure: {str(e)}"
    
    return FunctionTool.from_defaults(
        fn=query_target_structure_llamaIndex,
        name="query_target_structure",
        description="""
        Retrieves a file path based on the project's architecture and structure.
        Example queries:
        - "Where is the CustomerService implementation located?"
        - "Find the file that contains the Order model."
        """
    )

def create_get_file_content_tool(file_cache: FileCache) -> FunctionTool:
    """
    Factory for a file content tool that uses the provided file_cache instance.
    """
    async def _get_file_content(file_path: str) -> str:
        try:
            content = await file_cache.get_file_content(file_path)
            return content
        except Exception as e:
            return f"Error fetching file content: {str(e)}"
    
    def tool_function(file_path: str) -> str:
        return asyncio.run(_get_file_content(file_path))
    
    return FunctionTool.from_defaults(
        fn=tool_function,
        name="get_file_content",
        description="""
        Retrieves file content using the provided cache for the llamaIndex agent.
        Accepts a file path and returns its content as a string.
        """
    )


def create_query_analysis_tool(rag_service: AnalysisRagService) -> FunctionTool:
    """
    Factory for an analysis tool that uses the provided analysis_rag_service instance.
    """
    def query_analysis_llamaIndex(query: str) -> str:
        try:
            query_engine = rag_service.get_query_engine()
            if not query_engine:
                return "Analysis system not initialized. Please ensure the Analysis RAG service is properly set up."
    
            enhanced_query = f"""
Analyze the source code analysis data.
Based on the query below, return information about the original source code structure:
{query}

Guidelines:
- Return relevant information about classes, methods, patterns, or dependencies.
- If asking about a specific file, return its detailed analysis.
- Include only the most relevant information for the query.
"""
            response = query_engine.query(enhanced_query)
            return str(response).strip()
        except Exception as e:
            return f"Error searching code analysis: {str(e)}"
    
    return FunctionTool.from_defaults(
        fn=query_analysis_llamaIndex,
        name="query_analysis",
        description="""
        Retrieves information from the source code analysis.
        Example queries:
        - "What patterns are used in the source code?"
        - "Describe the structure of the Customer class"
        - "What dependencies are used in the original project?"
        - "Find information about the file UserController.cs"
        """
    )