# migration_service.py
# migration_service.py
import os
import certifi
import requests
from urllib3 import disable_warnings # Suppress SSL warnings (temporary for debugging)
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()  # Set globally for requests
os.environ['SSL_CERT_FILE'] = certifi.where()  # For other SSL uses

# Create session (insecure for debugging, to confirm bypass)
secure_session = requests.Session()
secure_session.verify = False  # Temporary for debugging

# Debug SSL setup
print("Certifi CA bundle path:", certifi.where())
print("REQUESTS_CA_BUNDLE:", os.environ.get("REQUESTS_CA_BUNDLE"))
try:
    response = secure_session.get("https://api.smith.langchain.com/info", headers={"x-api-key": os.environ.get("LANGCHAIN_API_KEY")})
    print("Manual test to LangSmith /info:", response.status_code, response.text)
except Exception as e:
    print("Manual test to LangSmith /info failed:", e)

from dotenv import load_dotenv
load_dotenv()

# Critical imports that might trigger HTTPS calls
from config.llm_config import pydantic_ai_model, llm_config
from llama_index.core.agent import ReActAgent
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer, SimpleComposableMemory

# Other imports
from pydantic import BaseModel
from typing import List, Dict, Optional
from pydantic_ai import Agent
import json
import asyncio
import re
import aiofiles
import subprocess
from utils.logger import logger, llm_logger
from utils.file_utils import (
    read_file,
    load_yaml_file,
    ensure_directory_exists,
    join_paths,
    sanitize_content,
    copy_static_files_to_wwwroot
)
import zipfile
import tiktoken
from utils.file_cache import FileCache
from utils.tools import create_query_target_structure_tool, create_get_file_content_tool, create_query_analysis_tool
from services.target_structure_rag_service import TargetStructureRagService
from services.analysis_rag_service import AnalysisRagService
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import logging
from langsmith import Client, traceable
from langsmith.run_helpers import trace
import time
from datetime import datetime

# Initialize LangSmith client
langsmith_client = Client(api_key=os.environ.get("LANGCHAIN_API_KEY"), session=secure_session)
print("LangSmith client initialized:", langsmith_client)

encoder = tiktoken.encoding_for_model("gpt-4o")



class CodeGenerationOutput(BaseModel):
    generated_code: str
    dependencies: List[str]

code_generation_agent = Agent(
    model=pydantic_ai_model,
    result_type=CodeGenerationOutput,
    system_prompt="You are an expert .NET developer specialized in code migration and modernization.",
)

class TokenTracker:
    """Tracks token usage across the entire migration process."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_prompt_tokens = 0
        self.total_response_tokens = 0
        self.total_requests = 0
        self.file_stats = {}
        self.microservice_stats = {}
        
    def add_file_tokens(self, file_name: str, prompt_tokens: int, response_tokens: int, microservice: str = "Miscellaneous"):
        """Add token usage for a specific file."""
        self.total_prompt_tokens += prompt_tokens
        self.total_response_tokens += response_tokens
        self.total_requests += 1
        
        # Per-file stats
        self.file_stats[file_name] = {
            "prompt_tokens": self.file_stats.get(file_name, {}).get("prompt_tokens", 0) + prompt_tokens,
            "response_tokens": self.file_stats.get(file_name, {}).get("response_tokens", 0) + response_tokens,
            "requests": self.file_stats.get(file_name, {}).get("requests", 0) + 1,
            "microservice": microservice
        }
        
        # Per-microservice stats
        if microservice not in self.microservice_stats:
            self.microservice_stats[microservice] = {
                "prompt_tokens": 0,
                "response_tokens": 0,
                "requests": 0,
                "files_processed": 0
            }
        
        self.microservice_stats[microservice]["prompt_tokens"] += prompt_tokens
        self.microservice_stats[microservice]["response_tokens"] += response_tokens
        self.microservice_stats[microservice]["requests"] += 1
        
        if file_name not in [f for f, stats in self.file_stats.items() if stats.get("microservice") == microservice]:
            self.microservice_stats[microservice]["files_processed"] += 1
    
    def get_summary(self) -> Dict:
        """Get comprehensive token usage summary."""
        return {
            "total_tokens": self.total_prompt_tokens + self.total_response_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_response_tokens": self.total_response_tokens,
            "total_requests": self.total_requests,
            "average_prompt_tokens_per_request": self.total_prompt_tokens / max(1, self.total_requests),
            "average_response_tokens_per_request": self.total_response_tokens / max(1, self.total_requests),
            "file_stats": self.file_stats,
            "microservice_stats": self.microservice_stats,
            "top_consuming_files": sorted(
                [(f, stats["prompt_tokens"] + stats["response_tokens"]) 
                 for f, stats in self.file_stats.items()], 
                key=lambda x: x[1], reverse=True
            )[:10]
        }
    
    def log_summary(self):
        """Log the complete token usage summary."""
        summary = self.get_summary()
        logger.info(f"=== MIGRATION TOKEN USAGE SUMMARY ===")
        logger.info(f"Total Tokens: {summary['total_tokens']:,}")
        logger.info(f"Total Prompt Tokens: {summary['total_prompt_tokens']:,}")
        logger.info(f"Total Response Tokens: {summary['total_response_tokens']:,}")
        logger.info(f"Total Requests: {summary['total_requests']}")
        logger.info(f"Average Tokens per Request: {summary['average_prompt_tokens_per_request'] + summary['average_response_tokens_per_request']:.2f}")
        
        logger.info(f"=== MICROSERVICE BREAKDOWN ===")
        for ms_name, stats in summary['microservice_stats'].items():
            total_ms_tokens = stats['prompt_tokens'] + stats['response_tokens']
            logger.info(f"{ms_name}: {total_ms_tokens:,} tokens ({stats['files_processed']} files, {stats['requests']} requests)")
        
        logger.info(f"=== TOP 5 TOKEN-CONSUMING FILES ===")
        for file_name, token_count in summary['top_consuming_files'][:5]:
            logger.info(f"{file_name}: {token_count:,} tokens")

class Migrator:
    def __init__(self):
        self.prompts = None
        self.output_dir = None
        self.source_dir = None
        self.repo_name = None
        self.target_version = None
        self.target_structure = None  
        self.instruction = None  
        self.llm = Settings.llm
        
        # Token tracking
        self.token_tracker = TokenTracker()
        
        # Create per-request instances.
        self.file_cache = FileCache()
        self.rag_service = TargetStructureRagService()  
        self.analysis_rag_service = AnalysisRagService()

        self.composable_memory = None
        
        self.tools = [
            create_query_target_structure_tool(self.rag_service),
            create_get_file_content_tool(self.file_cache),
            create_query_analysis_tool(self.analysis_rag_service)
        ]
        self.agent = ReActAgent(
            tools=self.tools,
            llm=llm_config._llm,
            verbose=True,
            memory=self.composable_memory
        )

        self.prompt_log_dir = None  # Initialize as None
        self.prompt_logger = logging.getLogger("prompt_logger")
        self.prompt_logger.setLevel(logging.INFO)
        self.prompt_logger.propagate = False

    @traceable(name="migration_initialize")
    async def initialize(self, output_dir: str, source_dir: str) -> None:
       self.output_dir = output_dir
       self.source_dir = source_dir
       ensure_directory_exists(self.output_dir)
       self.prompts = await load_yaml_file()

        # Set up prompt logger after output_dir is defined
       self.prompt_log_dir = join_paths(self.output_dir, "prompt_logs")
       ensure_directory_exists(self.prompt_log_dir)
       if not self.prompt_logger.handlers:
            prompt_handler = logging.FileHandler(
                join_paths(self.prompt_log_dir, "full_prompts.log"),
                encoding="utf-8"
            )
            prompt_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.prompt_logger.addHandler(prompt_handler)

       if not self.prompts:
           raise ValueError("prompts.yml failed to load. Is it missing, empty, or malformed?")
       if "file_type_prompts" not in self.prompts or "ocelot" not in self.prompts["file_type_prompts"]:
           raise ValueError("Missing 'file_type_prompts.ocelot.prompt' in prompts.yml")

    @traceable(name="zip_repository")
    def zip_repo(self) -> str:
        """
        Zip the repository folder and return the zip file path.
        """
        repo_dir = join_paths(self.output_dir, self.repo_name)
        zip_path = join_paths(self.output_dir, f"{self.repo_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_file_path, os.path.dirname(repo_dir))
                    zipf.write(full_file_path, arcname)
        return zip_path

    @traceable(name="extract_routes")
    def extract_routes(self, code: str) -> List[str]:
        """
        Extract all route strings from the given C# controller code.
        """      
        patterns = [
            r'\[Route\("([^"]+)"\)\]',
            r'\[HttpGet\("([^"]+)"\)\]',
            r'\[HttpPost\("([^"]+)"\)\]',
            r'\[HttpPut\("([^"]+)"\)\]',
            r'\[HttpDelete\("([^"]+)"\)\]'
        ]
        routes = set()
        for pattern in patterns:
            matches = re.findall(pattern, code)
            for m in matches:
                routes.add(m)
        return list(routes)

    @traceable(name="create_solution") 
    def create_solution(self, project_dir: str, project_name: str) -> None:
        """
        Create a solution file in the project directory and add any csproj files to it.
        """
        # Create a new solution
        sln_name = f"{project_name}.sln"
        try:
            subprocess.run(
                ["dotnet", "new", "sln", "-n", project_name, "--force"],
                cwd=project_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Created solution file {sln_name} in {project_dir}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating solution for {project_name}: {e.stderr.strip()}")
            raise
    
        # Find all csproj files in the project_dir
        csproj_files = []
        for root, _, files in os.walk(project_dir):
            csproj_files.extend([os.path.join(root, f) for f in files if f.endswith(".csproj")])
    
        # Add each csproj file to the solution
        for csproj in csproj_files:
            try:
                subprocess.run(
                    ["dotnet", "sln", sln_name, "add", csproj],
                    cwd=project_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                logger.info(f"Added {csproj} to solution {sln_name}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error adding {csproj} to solution {sln_name}: {e.stderr.strip()}")
                raise

    # chunking
    def estimate_tokens(self, text: str) -> int:
        return len(encoder.encode(text))

    @traceable(name="chunk_large_file")
    def chunk_large_file(self, content: str, max_chunk_size: int = 10000, file_type: str = "cs") -> List[str]:
        logger.debug(f"Checking chunking for {file_type} file with size {len(content)} characters, {self.estimate_tokens(content)} tokens")
        if self.estimate_tokens(content) <= max_chunk_size:
            logger.debug(f"No chunking needed for {file_type} file; size below threshold of {max_chunk_size} tokens")
            return [content]

        logger.debug(f"Chunking {file_type} file with size {len(content)} characters, {self.estimate_tokens(content)} tokens")
        lines = content.splitlines()
        chunks = []
        current_chunk = []
        current_size = 0

        in_method = False
        in_struct = False
        method_start_keywords = ['public class', 'private class', 'public interface', 'private interface',
                                'public void', 'private void', 'public async', 'private async',
                                'public string', 'private string', 'public int', 'private int']
        method_end_keywords = ['}']
        struct_start_keywords = ['public struct', 'private struct', 'public record', 'private record']
        struct_end_keywords = ['}']

        for line in lines:
            line_stripped = line.strip()

            if any(keyword in line_stripped for keyword in struct_start_keywords):
                if current_size + len(line) > max_chunk_size and current_chunk and not in_method:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_size = len(line)
                    in_struct = True
                    logger.debug(f"Starting struct in chunk, line: {line_stripped[:50]}")
                else:
                    current_chunk.append(line)
                    current_size += len(line)
                    in_struct = True

            elif any(keyword in line_stripped for keyword in struct_end_keywords) and in_struct:
                current_chunk.append(line)
                current_size += len(line)
                in_struct = False
                if current_size > max_chunk_size * 0.8:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                    logger.debug(f"Completed struct, created chunk with {len(current_chunk)} lines")
                else:
                    logger.debug(f"Completed struct, continuing chunk")

            elif any(keyword in line_stripped for keyword in method_start_keywords):
                if current_size + len(line) > max_chunk_size and current_chunk and not in_struct:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_size = len(line)
                    in_method = True
                    logger.debug(f"Starting method in chunk, line: {line_stripped[:50]}")
                else:
                    current_chunk.append(line)
                    current_size += len(line)
                    in_method = True

            elif any(keyword in line_stripped for keyword in method_end_keywords) and in_method:
                current_chunk.append(line)
                current_size += len(line)
                in_method = False
                if current_size > max_chunk_size * 0.8:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                    logger.debug(f"Completed method, created chunk with {len(current_chunk)} lines")
                else:
                    logger.debug(f"Completed method, continuing chunk")

            else:
                if current_size + len(line) > max_chunk_size and current_chunk and not in_method and not in_struct:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_size = len(line)
                    logger.debug(f"Reached size limit, created chunk with {len(current_chunk)} lines")
                else:
                    current_chunk.append(line)
                    current_size += len(line)

        if current_chunk:
            chunks.append("\n".join(current_chunk))
            logger.debug(f"Added final chunk with {len(current_chunk)} lines")

        logger.info(f"Created {len(chunks)} chunks for {file_type} file")
        return chunks
    
    @traceable(name="generate_gateway")
    async def generate_gateway(self, migration_results: List[Dict]) -> None:
        """Generate Ocelot configuration for the Gateway project using prompts.yml."""
        if self.prompts is None:
            logger.error("Prompts not initialized. Ensure initialize() is called before generate_gateway.")
            raise ValueError("Prompts are not initialized")

        repo_dir = join_paths(self.output_dir, self.repo_name)
        gateway_dir = join_paths(repo_dir, "Gateway")
        ensure_directory_exists(gateway_dir)
    
        microservices = [
            ms["name"].replace("Api", "").lower()
            for ms in self.target_structure.get("microservices", [])
            if ms["name"].lower() != "gateway"
        ]
        microservices_list = ", ".join([ms for ms in microservices if ms != "auth"])
    
        has_auth = any("auth" in ms.lower() for ms in microservices)
        if not has_auth:
            auth_instruction = "No authentication detected; exclude AuthenticationOptions."
            auth_case = "none"
        elif "auth" in microservices:
            auth_instruction = "Authentication in separate AuthService; include /auth/{everything} route and AuthenticationOptions for other routes."
            auth_case = "separate"
        else:
            auth_instruction = "Authentication in Gateway; include AuthenticationOptions for all routes."
            auth_case = "gateway"
    
        try:
            ocelot_prompt = self.prompts['file_type_prompts']['ocelot']['prompt']
        except KeyError as e:
            logger.error(f"Missing ocelot prompt in prompts.yml: {str(e)}")
            raise ValueError("Ocelot prompt not found in prompts.yml")
    
        routes_input = []
        for i, ms_name in enumerate(microservices):
            port = 5000 if ms_name == "auth" else 5001 + i
            routes_input.append({
                "microservice": ms_name,
                "port": port,
                "routes": [f"/api/{ms_name}/{{everything}}"]
            })
    
        prompt = f"""
    ### Ocelot Configuration
    {ocelot_prompt}
    
    ### Instruction
    {self.instruction or "split into microservices"}
    
    ### Microservices
    {microservices_list}
    
    ### Authentication Handling
    {auth_instruction}
    
    ### Routes
    {json.dumps(routes_input, indent=2)}
    
    Generate a valid JSON configuration for ocelot.json with Routes and GlobalConfiguration.
    For each microservice, create a route with:
    - DownstreamPathTemplate: /api/<microservice_name>/{{everything}}
    - DownstreamScheme: http
    - DownstreamHostAndPorts: localhost, port as specified
    - UpstreamPathTemplate: /api/<microservice_name>/{{everything}}
    - UpstreamHttpMethod: ["GET", "POST", "PUT", "DELETE"]
    If authentication case is 'separate', add /auth/{{everything}} route on port 5000 without AuthenticationOptions.
    If authentication case is 'gateway' or 'separate', add AuthenticationOptions with "AuthenticationProviderKey": "Bearer" and empty "AllowedScopes" for non-auth routes.
    Set GlobalConfiguration BaseUrl to "http://localhost:5004".
    Your entire response must be ONLY the valid JSON object. No explanations, no extra text, no markdown. Start with '{{' and end with '}}'. Do not include any other characters.
    """
        
        # Track tokens for gateway generation
        prompt_tokens = self.estimate_tokens(prompt)
        
        try:
            with trace(name="generate_ocelot_config", 
                      inputs={"prompt_tokens": prompt_tokens, "microservices": len(microservices)}) as run_context:
                response = llm_config._llm.complete(prompt)
                response_str = str(response)
                response_tokens = self.estimate_tokens(response_str)
                
                # Add to token tracker
                self.token_tracker.add_file_tokens("ocelot.json", prompt_tokens, response_tokens, "Gateway")
                
                # Add to LangSmith context
                if run_context:
                    run_context.end(outputs={
                        "response_tokens": response_tokens,
                        "total_tokens": prompt_tokens + response_tokens
                    })
                
                sanitized_response = sanitize_content(response_str)
                match = re.search(r"(\{.*\})", sanitized_response, re.DOTALL)
                if not match:
                    raise ValueError("No JSON object found in ocelot config response")
                gateway_config = json.loads(match.group(1))
        
                ocelot_path = join_paths(gateway_dir, "ocelot.json")
                async with aiofiles.open(ocelot_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(gateway_config, indent=4))
                logger.info(f"Wrote ocelot.json to {ocelot_path}")
                
        except Exception as e:
            logger.error(f"Error generating ocelot.json: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type((ValueError)))
    @traceable(name="generate_code")
    async def generate_code(self, content: str, file_type: str, description: str, instructions: str, file_name: str, agent: ReActAgent, namespace: Optional[str] = None, microservice_name: Optional[str] = None, project_name: Optional[str] = None) -> Optional[Dict]:
        """Generate code for a specific file with dynamic prompt selection from prompts.yml."""
        logger.info(f"Generating code for file: {file_name}, type: {file_type}, microservice: {microservice_name}, project: {project_name}")
    
        # Infer project layer based on project_name
        layer = None
        if project_name:
            project_name_lower = project_name.lower()
            if 'domain' in project_name_lower:
                layer = 'Domain'
            elif 'application' in project_name_lower:
                layer = 'Application'
            elif 'infrastructure' in project_name_lower:
                layer = 'Infrastructure'
            elif 'presentation' in project_name_lower:
                layer = 'Presentation'
            logger.info(f"Inferred project layer: {layer}")
    
        # Select the prompt from prompts.yml
        file_type_prompt = ''
        if self.prompts and 'file_type_prompts' in self.prompts and file_type in self.prompts['file_type_prompts']:
            file_type_prompt = self.prompts['file_type_prompts'][file_type].get('prompt', '')
            logger.info(f"Using prompt from prompts.yml for {file_type}: {file_type_prompt[:100]}...")  # Truncate for readability
        else:
            logger.warning(f"No prompt found in prompts.yml for file_type: {file_type}. Using default prompt construction.")
            file_type_prompt = f"Generate a {file_type} file for a .NET project targeting {self.target_version} with appropriate SDK and build properties."
    
        # Customize prompt with microservice-specific details
        if microservice_name and microservice_name != 'Unknown':
            ms_name = microservice_name.replace("Grpc", "").lower()
            ms_name_capitalized = ms_name.capitalize()
            file_type_prompt = file_type_prompt.replace("customerGrpc", f"{ms_name}Grpc")
            file_type_prompt = file_type_prompt.replace("CustomerGrpc", f"{ms_name_capitalized}Grpc")
            logger.info(f"Customized prompt with microservice name: {ms_name}")
    
        # Construct the prompt directly without format_args
        prompt = f"""Generate code for a file named {file_name} of type {file_type}, following these strict guidelines:
    
        VALIDATION RULES:
        1. The file must contain exactly one primary type (class, interface, or record) for C# files.
        2. The namespace must reflect the project and folder structure.
        3. No regions or commented-out code are allowed.
        4. Follow standard .NET naming conventions.
        5. Include all necessary using directives at the top.
    
        Description: {description}
        Instructions: {instructions}
        Target Framework: {self.target_version}
        Microservice Name: {microservice_name or 'Unknown'}
        Project Name: {project_name or 'Unknown'}
        Project Layer: {layer or 'Unknown'}
    
        For csproj files: Use the computed list of dependencies to create corresponding PackageReference entries, including only packages that are not part of the default set for {self.target_version} (exclude system and default packages).
    
        Generate clean, modern .NET code using the following principles:
        - Leverage the latest C# features appropriate for the target framework.
        - Follow SOLID principles and adopt clean architecture.
        - Implement proper dependency injection.
        - Use async/await where applicable.
        - Handle errors appropriately.
        - Include XML documentation for public APIs.
    
        Output Requirements:
        The response MUST be a valid JSON object with exactly two keys:
        1. "generated_code": containing the generated code as a string.
        2. "dependencies": an array of dependency names.
        Do not include any extra text or commentary in the response.
    
        Source content (if applicable):
        {content}"""
    
        if namespace:
            prompt += f"\nThe namespace for this file should be: {namespace}"
    
        # Prepend the specific prompt from prompts.yml
        if file_type_prompt:
            prompt = f"{file_type_prompt}\n\nAdditional Context:\n- Microservice Name: {microservice_name or 'Unknown'}\n- Project Name: {project_name or 'Unknown'}\n- Project Layer: {layer or 'Unknown'}\n\n{prompt}"
            logger.info(f"Prepended prompt for {file_type}: {file_type_prompt[:100]}...")  # Truncate for readability
    
        # Log the final prompt being sent to the LLM
        logger.info(f"Final prompt for {file_name}: {prompt[:500]}...")  # Truncate for readability
        
        # Log full prompt to LangSmith
        self.prompt_logger.info(f"=== FULL PROMPT FOR {file_name} ===\n{prompt}\n=== END PROMPT ===")
    
        prompt_token_count = self.estimate_tokens(prompt)
        logger.debug(f"Prompt token count for generate_code ({file_name}): {prompt_token_count}")

        max_input_tokens = 100000
        if prompt_token_count > max_input_tokens:
            logger.error(f"Prompt for {file_name} exceeds token limit: {prompt_token_count} tokens")
            raise ValueError(f"Prompt size ({prompt_token_count} tokens) exceeds maximum allowed ({max_input_tokens} tokens)")

        total_prompt_tokens_file = prompt_token_count
        total_response_tokens_file = 0

        chunkable_file_types = ["model", "proto", "grpc_service_cs", "service", "interface"]
        if file_type in chunkable_file_types and self.estimate_tokens(content) > 10000:
            logger.info(f"Chunking source content for {file_name}: {self.estimate_tokens(content)} tokens")
            chunks = self.chunk_large_file(content, max_chunk_size=10000, file_type=file_type)
            logger.info(f"Split content into {len(chunks)} chunks for {file_name}")

            results = []
            combined_dependencies = set()
            tasks = []
            
            with trace(name=f"generate_code_chunked_{file_name}", 
                      inputs={"file_name": file_name, "chunks": len(chunks), "file_type": file_type, "microservice": microservice_name}) as run_context:
                
                for i, chunk in enumerate(chunks):
                    chunk_prompt = prompt + f"\n\n[CHUNK CONTEXT: This is part {i+1} of {len(chunks)} of a larger file. Please generate only the code for this specific chunk. For the first chunk only, include all necessary using statements and namespace declarations at the top. For subsequent chunks, generate only the class/method content without any using statements or namespace wrappers.]"
                    chunk_prompt_token_count = self.estimate_tokens(chunk_prompt)
                    total_prompt_tokens_file += chunk_prompt_token_count
                    logger.debug(f"Prompt token count for generate_code chunk {i+1}/{len(chunks)} ({file_name}): {chunk_prompt_token_count}")
                    tasks.append(asyncio.to_thread(agent.chat, chunk_prompt))
                
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(chunk_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error processing chunk {i+1} for {file_name}: {str(result)}")
                        raise ValueError(f"Failed to process chunk {i+1} for {file_name}: {str(result)}")
                    
                    sanitized_response = sanitize_content(str(result))
                    response_token_count = self.estimate_tokens(sanitized_response)
                    total_response_tokens_file += response_token_count
                    logger.debug(f"LLM response token count for generate_code chunk {i+1}/{len(chunks)} ({file_name}): {response_token_count}")
                    logger.debug(f"Raw LLM response for chunk {i+1} of {file_name}: {sanitized_response[:500]}...")
                    match = re.search(r"(\{.*\})", sanitized_response, re.DOTALL)
                    if not match:
                        logger.error(f"No JSON object found in LLM response for chunk {i+1} of {file_name}")
                        raise ValueError(f"No JSON object found in the response for chunk {i+1}")
                    
                    json_result = json.loads(match.group(1))
                    results.append(json_result["generated_code"])
                    combined_dependencies.update(json_result["dependencies"])
                    logger.info(f"Generated chunk {i+1}/{len(chunks)} for {file_name}: {len(json_result['generated_code'].splitlines())} lines")
                
                combined_code = "\n".join(results)
                logger.info(f"Combined {len(chunks)} chunks for {file_name}: {len(combined_code.splitlines())} lines")
                
                # Track tokens for chunked file
                self.token_tracker.add_file_tokens(file_name, total_prompt_tokens_file, total_response_tokens_file, microservice_name or "Miscellaneous")
                
                # Update LangSmith context
                if run_context:
                    run_context.end(outputs={
                        "total_prompt_tokens": total_prompt_tokens_file,
                        "total_response_tokens": total_response_tokens_file,
                        "total_tokens": total_prompt_tokens_file + total_response_tokens_file,
                        "chunks_processed": len(chunks)
                    })
                
                logger.debug(f"Total token count for generate_code ({file_name}): {total_prompt_tokens_file + total_response_tokens_file} (Prompt: {total_prompt_tokens_file}, Response: {total_response_tokens_file})")
                
                return {"generated_code": combined_code, "dependencies": list(combined_dependencies)}

        logger.info(f"No chunking needed for {file_name}; content size: {self.estimate_tokens(content)} tokens")

        with trace(name=f"generate_code_single_{file_name}", 
                  inputs={"file_name": file_name, "file_type": file_type, "microservice": microservice_name, "prompt_tokens": prompt_token_count}) as run_context:
            
            response = await asyncio.to_thread(agent.chat, prompt)
            sanitized_response = sanitize_content(str(response))
            response_token_count = self.estimate_tokens(sanitized_response)
            total_response_tokens_file = response_token_count
            
            # Track tokens for single file
            self.token_tracker.add_file_tokens(file_name, total_prompt_tokens_file, total_response_tokens_file, microservice_name or "Miscellaneous")
            
            # Update LangSmith context
            if run_context:
                run_context.end(outputs={
                    "response_tokens": response_token_count,
                    "total_tokens": total_prompt_tokens_file + total_response_tokens_file,
                    "response_preview": sanitized_response[:200]
                })
            
            logger.debug(f"LLM response token count for generate_code ({file_name}): {response_token_count}")
            logger.info(f"Raw LLM response for {file_name}: {sanitized_response[:500]}...")

            match = re.search(r"(\{.*\})", sanitized_response, re.DOTALL)
            if not match:
                logger.error(f"No JSON object found in LLM response for {file_name}")
                raise ValueError("No JSON object found in the response")
            json_str = match.group(1)
            json_result = json.loads(json_str)
            logger.info(f"Generated code for {file_name}: {json_result['generated_code'][:500]}...")  # Truncate for readability
            logger.info(f"Dependencies for {file_name}: {json_result['dependencies']}")
            logger.debug(f"Total token count for generate_code ({file_name}): {total_prompt_tokens_file + total_response_tokens_file} (Prompt: {total_prompt_tokens_file}, Response: {total_response_tokens_file})")
            
            return json_result

    @traceable(name="process_file")
    async def process_file(self, file_path: str, file_info: Dict, agent: ReActAgent, file_cache: FileCache, project_dir: str, project_name: str) -> Dict:
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        file_type = file_info.get('file_type', 'unknown')
        description = file_info.get('description', '')
        instructions = file_info.get('instructions', '')
        microservice_name = file_info.get('microservice_name', 'Miscellaneous')
    
        logger.info(f"Processing file: {file_name} (type: {file_type}, microservice: {microservice_name})")
    
        # Compute namespace based on project structure
        relative_path = os.path.relpath(file_path, project_dir)
        parts = relative_path.split(os.sep)
        if len(parts) > 1:
            directories = parts[:-1]  # Exclude the file name
            namespace = project_name + '.' + '.'.join(directories)
        else:
            namespace = project_name  # File is in project root
    
        # Read source content if applicable
        source_files = file_info.get('source_files', [])
        source_content = ""
        source_tokens=0
        if source_files:
            source_paths = [join_paths(self.source_dir, f) for f in source_files]
            contents = await asyncio.gather(*[read_file(path) for path in source_paths])
            source_content = "\n".join([c for c in contents if c])
            source_tokens = self.estimate_tokens(source_content)
            logger.info(f"Read {len(source_files)} source files for {file_name}, total content size: {len(source_content)} characters, {source_tokens} tokens")
    
        try:
            # Normalize the file_path to avoid redundant segments
            file_path = os.path.normpath(file_path)
            logger.info(f"Resolved file path for writing: {file_path}")
    
            # Generate code with the computed namespace
            generated = await self.generate_code(source_content, file_type, description, 
                                                 instructions, file_name, agent, 
                                                 namespace=namespace,
                                                 microservice_name=microservice_name,
                                                 project_name=project_name)
            
            if not generated or "generated_code" not in generated:
                raise ValueError(f"Code generation failed for {file_name}")
    
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            ensure_directory_exists(directory)
            logger.info(f"Ensured directory exists: {directory}")
    
            # Write the generated code
            sanitized_code = sanitize_content(generated["generated_code"])
            generated_tokens = self.estimate_tokens(sanitized_code)
            logger.info(f"Generated file {file_name}: {len(sanitized_code.splitlines())} lines, {generated_tokens} tokens")
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(sanitized_code)
            await file_cache.update_file(file_path, sanitized_code)
            logger.info(f"Successfully wrote file to: {file_path}")
    
            # Return result (routes only for REST controllers)
            result = {
                "file": file_name,
                "dependencies": generated.get("dependencies", []),
                "routes": []
            }
            if file_type == "controller_cs":
                result["routes"] = self.extract_routes(sanitized_code)
            result["status"] = "success"
            return result
        except Exception as e:
            logger.error(f"Error processing file {file_name} at {file_path}: {str(e)}")
            return {
                "file": file_name,
                "dependencies": [],
                "routes": [],
                "status": "failed",
                "error": str(e)
            }    
          
    @traceable(name="process_folder_with_routes")
    async def process_folder_with_routes(self, base_path: str, folder_data: dict, migration_results: dict, project_dependencies: set, agent: ReActAgent, file_cache: FileCache, microservice_name: str, project_dir: str, project_name: str) -> None:
        logger.info(f"Processing folder: {base_path}")
    
        if folder_data.get("target_files"):
            for file_name, file_info in folder_data["target_files"].items():
                try:
                    full_path = os.path.normpath(join_paths(base_path, file_name))
                    logger.info(f"Processing file at: {full_path}")
                    file_info['microservice_name'] = microservice_name
                    result = await self.process_file(full_path, file_info, agent, file_cache, project_dir, project_name)
                    migration_results["successful_files"].append(full_path)
                    if result.get("dependencies"):
                        project_dependencies.update(result.get("dependencies", []))
                    if result.get("routes"):
                        migration_results["file_routes"][full_path] = result["routes"]
                except Exception as e:
                    logger.error(f"Error processing file {full_path}: {e}")
                    migration_results["failed_files"].append(
                        {"file": full_path, "error": str(e)}
                    )
    
        if folder_data.get("subfolders"):
            for subfolder_name, subfolder_data in folder_data["subfolders"].items():
                subfolder_path = os.path.normpath(join_paths(base_path, subfolder_name))
                ensure_directory_exists(subfolder_path)
                logger.info(f"Processing subfolder: {subfolder_path}")
                await self.process_folder_with_routes(subfolder_path, subfolder_data, migration_results, project_dependencies, agent, file_cache, microservice_name, project_dir, project_name)

    @traceable(name="process_and_zip_projects")
    async def process_and_zip_projects(self, target_structure: Dict, target_version: str, repo_name: str) -> Dict:
        """
        Updated to process microservices instead of a flat projects list.
        """
        try:
            # Reset token tracker for new migration
            self.token_tracker.reset()
            
            # Validate target_structure
            if not target_structure or not isinstance(target_structure, dict):
                logger.error("Invalid or empty target_structure provided")
                raise ValueError("Target structure is None or invalid")
    
            # Set self.target_structure for use in generate_gateway
            self.target_structure = target_structure
    
            # Process microservices
            migration_results = await self.process_microservices(target_structure, target_version, repo_name)
    
            # Generate gateway
            await self.generate_gateway(migration_results)
    
            # Zip the repository
            zip_path = self.zip_repo()
            
            # Log final token summary
            self.token_tracker.log_summary()
            
            # Create token usage report
            token_summary = self.token_tracker.get_summary()
            
            # Save token report to file
            token_report_path = join_paths(self.output_dir, f"{repo_name}_token_usage.json")
            async with aiofiles.open(token_report_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(token_summary, indent=2))
            logger.info(f"Token usage report saved to: {token_report_path}")
    
            return {
                "migration_results": migration_results, 
                "zip_file": zip_path,
                "token_usage": token_summary
            }
        except Exception as e:
            logger.error(f"Error in process_and_zip_projects: {str(e)}")
            # Still log summary even on error
            self.token_tracker.log_summary()
            raise

    @traceable(name="process_microservices")
    async def process_microservices(self, target_structure: Dict, target_version: str, repo_name: str) -> List[Dict]:
        """Process all microservices in parallel."""
        self.repo_name = repo_name
        self.target_version = target_version
        repo_dir = join_paths(self.output_dir, repo_name)
        ensure_directory_exists(repo_dir)
    
        microservices = target_structure.get("microservices", [])
        logger.info(f"Processing microservices: {[ms['name'] for ms in microservices]}")
        tasks = [
            self.process_single_microservice(microservice, repo_dir)
            for microservice in microservices
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        flattened_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing microservice: {str(result)}")
                continue
            flattened_results.extend(result)
        total_expected = sum(len(ms.get('projects', [])) for ms in microservices)
        if len(flattened_results) != total_expected:
            logger.warning(f"Processed {len(flattened_results)} of {total_expected} projects across {len(microservices)} microservices")
        return flattened_results   

    @traceable(name="process_single_microservice")
    async def process_single_microservice(self, microservice: Dict, repo_dir: str) -> List[Dict]:
        ms_name = microservice.get("name", "Miscellaneous")
        ms_dir = join_paths(repo_dir, ms_name)
        ensure_directory_exists(ms_dir)
        ms_results = []
    
        file_cache = FileCache()
        tools = [
            create_query_target_structure_tool(self.rag_service),
            create_get_file_content_tool(file_cache),
            create_query_analysis_tool(self.analysis_rag_service)
        ]
        chat_memory_buffer = ChatMemoryBuffer.from_defaults()
        composable_memory = SimpleComposableMemory.from_defaults(
            primary_memory=chat_memory_buffer,
        )
        agent = ReActAgent(
            tools=tools,
            llm=llm_config._llm,
            verbose=True,
            memory=composable_memory
        )
    
        try:
            projects = microservice.get("projects", [])
            desired_order = ['domain', 'infrastructure', 'service', 'application', 'presentation']
            def order_key(project: Dict) -> int:
                project_name = project.get("project_name", "").lower()
                for idx, key in enumerate(desired_order):
                    if key in project_name:
                        return idx
                return len(desired_order)
            sorted_projects = sorted(projects, key=order_key)
    
            for project in sorted_projects:
                project_name = project.get("project_name", "unknown")
                if ms_name.lower() == 'gateway':
                    project_dir = ms_dir
                    project_name = "Gateway"  # Consistent namespace base for Gateway
                else:
                    project_dir = join_paths(ms_dir, project_name)
                ensure_directory_exists(project_dir)
    
                migration_results = {
                    "successful_files": [],
                    "failed_files": [],
                    "total_files": 0,
                    "success_rate": 0,
                    "target_version": self.target_version,
                    "project_name": project_name,
                    "microservice": ms_name,
                    "file_routes": {}
                }
                project_dependencies = set()
    
                root_files = project["target_structure"].get("root", {})
                normal_files, special_files = {}, {}
                for file_name, file_info in root_files.items():
                    if file_name.endswith(".csproj") or file_name.lower() == "program.cs":
                        special_files[file_name] = file_info
                    else:
                        normal_files[file_name] = file_info
    
                for file_name, file_info in normal_files.items():
                    if file_name.endswith('ocelot.json'):
                        logger.info(f"Skipping ocelot.json: {file_name}")
                        continue
                    try:
                        clean_file_name = file_name
                        if ms_name.lower() == 'gateway' and file_name.startswith('Gateway/'):
                            clean_file_name = file_name[len('Gateway/'):]
                            logger.info(f"Stripped Gateway/ prefix: {file_name} -> {clean_file_name}")
                        file_info['microservice_name'] = ms_name
                        output_path = join_paths(ms_dir if ms_name.lower() == 'gateway' else project_dir, clean_file_name)
                        result = await self.process_file(output_path, file_info, agent, file_cache, project_dir, project_name)
                        migration_results["successful_files"].append(clean_file_name)
                        migration_results["total_files"] += 1
                        project_dependencies.update(result.get("dependencies", []))
                        if result.get("routes"):
                            migration_results["file_routes"][clean_file_name] = result["routes"]
                    except Exception as e:
                        migration_results["failed_files"].append({"file": file_name, "error": str(e)})
                        migration_results["total_files"] += 1
    
                for file_name, file_info in special_files.items():
                    if file_name.endswith('ocelot.json'):
                        logger.info(f"Skipping ocelot.json: {file_name}")
                        continue
                    try:
                        clean_file_name = file_name
                        if ms_name.lower() == 'gateway' and file_name.startswith('Gateway/'):
                            clean_file_name = file_name[len('Gateway/'):]
                            logger.info(f"Stripped Gateway/ prefix: {file_name} -> {clean_file_name}")
                        file_info['microservice_name'] = ms_name
                        output_path = join_paths(ms_dir if ms_name.lower() == 'gateway' else project_dir, clean_file_name)
                        result = await self.process_file(output_path, file_info, agent, file_cache, project_dir, project_name)
                        migration_results["successful_files"].append(clean_file_name)
                        migration_results["total_files"] += 1
                        project_dependencies.update(result.get("dependencies", []))
                        if result.get("routes"):
                            migration_results["file_routes"][clean_file_name] = result["routes"]
                    except Exception as e:
                        migration_results["failed_files"].append({"file": file_name, "error": str(e)})
                        migration_results["total_files"] += 1
    
                folders = project["target_structure"].get("folders", {})
                logger.info(f"Folders to process: {list(folders.keys())}")
                for folder_name, folder_info in folders.items():
                    logger.info(f"Processing folder: {folder_name}")
                    folder_path = join_paths(ms_dir if ms_name.lower() == 'gateway' else project_dir, folder_name)
                    ensure_directory_exists(folder_path)
                    await self.process_folder_with_routes(
                        folder_path, folder_info, migration_results,
                        project_dependencies, agent, file_cache, ms_name, project_dir, project_name
                    )
    
                if migration_results["total_files"] > 0:
                    migration_results["success_rate"] = (
                        len(migration_results["successful_files"]) / migration_results["total_files"]
                    ) * 100
    
                ms_results.append(migration_results)
    
                if "Views" in project["target_structure"].get("folders", {}):
                    copy_static_files_to_wwwroot(self.source_dir, project_dir)
    
            self.create_solution(ms_dir, ms_name)
        finally:
            composable_memory.reset()
    
        return ms_results
    
   # gRPC-specific processing
    @traceable(name="process_and_zip_projects_grpc")
    async def process_and_zip_projects_grpc(self, target_structure: Dict, target_version: str, repo_name: str) -> Dict:
        # Reset token tracker for new migration
        self.token_tracker.reset()
        
        self.target_structure = target_structure
        self.target_version = target_version
        self.repo_name = repo_name
        if self.target_structure is None:
            logger.error("Target structure is None in process_and_zip_projects_grpc")
            raise ValueError("Target structure is not provided")
        migration_results = await self.process_microservices_grpc(target_structure, target_version, repo_name)
        zip_path = self.zip_repo()
        
        # Log final token summary
        self.token_tracker.log_summary()
        
        # Create token usage report
        token_summary = self.token_tracker.get_summary()
        
        # Save token report to file
        token_report_path = join_paths(self.output_dir, f"{repo_name}_grpc_token_usage.json")
        async with aiofiles.open(token_report_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(token_summary, indent=2))
        logger.info(f"Token usage report saved to: {token_report_path}")
        
        return {
            "migration_results": migration_results, 
            "zip_file": zip_path,
            "token_usage": token_summary
        }

    @traceable(name="process_microservices_grpc")
    async def process_microservices_grpc(self, target_structure: Dict, target_version: str, repo_name: str) -> List[Dict]:
        self.repo_name = repo_name
        self.target_version = target_version
        repo_dir = join_paths(self.output_dir, self.repo_name)
        ensure_directory_exists(repo_dir)

        microservices = target_structure.get("microservices", [])
        tasks = [
            self.process_single_microservice_grpc(microservice, repo_dir)
            for microservice in microservices
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        flattened_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing microservice: {str(result)}")
                continue
            flattened_results.extend(result)
        return flattened_results

    @traceable(name="process_single_microservice_grpc")
    async def process_single_microservice_grpc(self, microservice: Dict, repo_dir: str) -> List[Dict]:
        ms_name = microservice.get("name", "unknown")
        ms_dir = join_paths(repo_dir, ms_name)
        ensure_directory_exists(ms_dir)
        ms_results = []

        file_cache = FileCache()
        tools = [
            create_query_target_structure_tool(self.rag_service),
            create_get_file_content_tool(file_cache),
            create_query_analysis_tool(self.analysis_rag_service)
        ]
        chat_memory_buffer = ChatMemoryBuffer.from_defaults()
        composable_memory = SimpleComposableMemory.from_defaults(primary_memory=chat_memory_buffer)
        agent = ReActAgent.from_tools(tools=tools, llm=llm_config._llm, verbose=True, memory=composable_memory)


        try:
            projects = microservice.get("projects", [])
            desired_order = ['domain', 'infrastructure', 'service', 'application', 'presentation']
            def order_key(project: Dict) -> int:
                project_name = project.get("project_name", "").lower()
                for idx, key in enumerate(desired_order):
                    if key in project_name:
                        return idx
                return len(desired_order)
            sorted_projects = sorted(projects, key=order_key)

            for project in sorted_projects:
                project_name = project.get("project_name", "unknown")
                project_dir = ms_dir if ms_name.lower() == 'gateway' else join_paths(ms_dir, project_name)
                ensure_directory_exists(project_dir)

                migration_results = {
                    "successful_files": [],
                    "failed_files": [],
                    "total_files": 0,
                    "success_rate": 0,
                    "target_version": self.target_version,
                    "project_name": project_name,
                    "microservice": ms_name,
                    "file_routes": {}
                }
                project_dependencies = set()

                root_files = project["target_structure"].get("root", {})
                normal_files, special_files = {}, {}
                for file_name, file_info in root_files.items():
                    if file_name.endswith(".csproj") or file_name.lower() == "program.cs":
                        special_files[file_name] = file_info
                    elif "wwwroot" not in file_name.lower():
                        normal_files[file_name] = file_info
                    else:
                        logger.info(f"Skipping wwwroot file in root for LLM processing: {file_name}")

                tasks = []
                for file_name, file_info in normal_files.items():
                 output_path = join_paths(project_dir, file_name)
                 tasks.append(self.process_file(output_path, file_info, agent, file_cache, project_dir, project_name))

              
                for file_name, file_info in special_files.items():
                    output_path = join_paths(project_dir, file_name)
                    tasks.append(self.process_file(output_path, file_info, agent, file_cache, project_dir, project_name))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        migration_results["failed_files"].append({"file": "unknown", "error": str(result)})
                        migration_results["total_files"] += 1
                    else:
                        if result["status"] == "success":
                            migration_results["successful_files"].append(result["file"])
                        else:
                            migration_results["failed_files"].append({"file": result["file"], "error": result["error"]})
                        migration_results["total_files"] += 1
                        project_dependencies.update(result.get("dependencies", []))
                        if result.get("routes"):
                            migration_results["file_routes"][result["file"]] = result["routes"]

                folders = project["target_structure"].get("folders", {})
                logger.info(f"Folders to process: {list(folders.keys())}")
                for folder_name, folder_info in folders.items():
                    if folder_name.lower() == "wwwroot":
                        logger.info(f"Skipping wwwroot folder for LLM processing: {folder_name}")
                        continue
                    folder_path = join_paths(project_dir, folder_name)
                    ensure_directory_exists(folder_path)
                    await self.process_folder_with_routes(
                        folder_path, folder_info, migration_results, project_dependencies, agent, file_cache, ms_name, project_dir, project_name
                    )

                # Copy wwwroot if it exists in target_structure or source directory
                if "wwwroot" in folders or os.path.exists(join_paths(self.source_dir, "wwwroot")):
                    logger.info(f"Copying wwwroot static files for project: {project_name}")
                    copy_static_files_to_wwwroot(self.source_dir, project_dir)
                    migration_results["successful_files"].append("wwwroot")
                    migration_results["total_files"] += 1  # Count wwwroot as one processed item

                if migration_results["total_files"] > 0:
                    migration_results["success_rate"] = (
                        len(migration_results["successful_files"]) / migration_results["total_files"]
                    ) * 100

                ms_results.append(migration_results)

            self.create_solution(ms_dir, ms_name)
        finally:
            composable_memory.reset()

        return ms_results