from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.readers.json import JSONReader
from typing import Optional, Dict, Any
import os
import json
from utils import logger

class AnalysisRagService:
    def __init__(self):
        self._query_engine: Optional[VectorStoreIndex] = None

    def initialize(self, json_data: Dict[str, Any], temp_dir: str, force_rebuild: bool = False) -> bool:
        try:
            # Create analysis directory inside temp_dir
            analysis_dir = os.path.join(temp_dir, "analysis")
            os.makedirs(analysis_dir, exist_ok=True)
            
            # Save JSON data inside analysis_dir
            json_file = os.path.join(analysis_dir, "data.json")
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            index_path = os.path.join(analysis_dir, "index")
            
            # Create or load index
            if not os.path.exists(index_path) or force_rebuild:
                reader = JSONReader()
                documents = reader.load_data(json_file)
                
                index = VectorStoreIndex.from_documents(
                    documents,
                    show_progress=True
                )
                index.storage_context.persist(persist_dir=index_path)
            else:
                storage_context = StorageContext.from_defaults(
                    persist_dir=index_path
                )
                index = load_index_from_storage(storage_context)
            
            self._query_engine = index.as_query_engine()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Analysis RAG service: {str(e)}")
            return False
    
    def get_query_engine(self) -> Optional[VectorStoreIndex]:
        """Get the query engine instance."""
        return self._query_engine

    def is_initialized(self) -> bool:
        """Check if the RAG service is initialized."""
        return self._query_engine is not None