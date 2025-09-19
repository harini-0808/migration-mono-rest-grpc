# analysis service

import os
import certifi
import requests
from urllib3 import disable_warnings
disable_warnings()  # Suppress SSL warnings (temporary for debugging)
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()  # Set globally for requests
os.environ['SSL_CERT_FILE'] = certifi.where()  # For other SSL uses

# Create session (insecure for debugging)
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
from typing import Dict,List,Literal,Optional
import os
from config.llm_config import pydantic_ai_model
from config.llm_config import llm_config
from pydantic_ai import Agent
from pydantic import BaseModel
import aiofiles
import json
import asyncio
from llama_index.core.agent import ReActAgent
from utils import logger
import tiktoken
import re
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.file_utils import sanitize_content

encoder = tiktoken.encoding_for_model("gpt-4o")


class AnalyzeOutputStructure(BaseModel):
    file_type: Literal[
        'controller',
        'config',
        'view',
        'model',
        'repository',
        'layout',
        'service',
        'middleware',
        'program',
        'program_cs_grpc',
        'csproj',
        'ocelot',
        'csproj_grpc',
        'proto',
        'grpc_service_cs'

    ]
    description: str
    classnames: List[str]
    namespace: List[str]
    methods: List[str]
    external_references: List[str]
    framework_features: List[str]
    dependencies: List[str]
    patterns_used: List[str]
    routes: Optional[List[str]] = None    # new field for controller routes
    extra_notes: Optional[str] = None     # optional field for extra context

class TargetFileMapping(BaseModel):
    source_files: List[str]
    description: str
    namespace: str 
    file_type: Literal[
        'controller',
        'config',
        'view',
        'model',
        'repository',
        'interface',
        'layout',
        'razor_component',
        'service',
        'middleware',
        'program',
        'program_cs_grpc',
        'csproj',
        'ocelot',
        'csproj_grpc',
        'proto',
        'grpc_service_cs'
    ]

class TargetFolder(BaseModel):
    target_files: Optional[Dict[str, TargetFileMapping]] = None
    subfolders: Optional[Dict[str, "TargetFolder"]] = None

class TargetStructure(BaseModel):
    root: Dict[str, TargetFileMapping]
    folders: Dict[str, TargetFolder]

class ProjectTargetStructure(BaseModel):
    project_name: str
    target_structure: TargetStructure

class ListOfProjects(BaseModel):
    projects: List[ProjectTargetStructure]

project_structure_analyzer_agent = Agent(
    model = pydantic_ai_model,
    result_type=AnalyzeOutputStructure,
    system_prompt="You are an expert .NET code analyzer specialized in understanding and documenting code structure.",
)

target_structure_creator_agent = Agent(
    model = pydantic_ai_model,
    result_type=ListOfProjects,
    system_prompt="You are an expert .NET Architect specialized in designing microservice architectures.",
)


async def flatten_dict(d, parent_key='', sep='/'):
        items = []
        for key, value in d.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                # Recursively await the nested call
                nested_items = await flatten_dict(value, new_key, sep) 
                items.extend(nested_items.items())
            else:
                items.append((new_key, value))
        return dict(items)


class ProjectAnalyzer:          
    def __init__(self, project_path: str):
        self.start_path = project_path
        self.ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.vs',
            'bin', 'obj', '.vscode', '.idea'
        ]
    
        self.agent = ReActAgent.from_tools(tools=[], llm=llm_config._llm, verbose=True)
    async def create_basic_tree(self) -> Dict:
      tree = {}
      
      for root, dirs, files in os.walk(self.start_path):
          # Skip ignored directories
          dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.ignore_patterns)]
          
          # Get path relative to start path
          rel_path = os.path.relpath(root, self.start_path)
          if rel_path == '.':
              current = tree
          else:
              # Navigate to correct nested dictionary
              current = tree
              for part in rel_path.split(os.sep):
                  current = current.setdefault(part, {})
          
          # Add files to current directory
          for file in files:
              if not any(pattern in file for pattern in self.ignore_patterns):
                  current[file] = "file"
                  
      return tree
    
    async def analyze_code_file(self, file_path: str) -> Optional[Dict]:
      if not file_path.endswith(('.cs', '.cshtml', '.razor', '.csproj', '.config', '.json', '.aspx')):
        return None


      try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
          code_content = await f.read()

      # Include corresponding .aspx markup if this is a code-behind file
        if file_path.endswith(".aspx.cs"):
            markup_file = file_path[:-3]  # remove '.cs'
            if os.path.exists(markup_file):
                async with aiofiles.open(markup_file, 'r', encoding='utf-8') as mf:
                    markup_content = await mf.read()
                code_content += f"\n\n// Corresponding ASPX Markup:\n{markup_content}"
    

        prompt = f"""Analyze this C# code file for migration purposes:

  Code content:
  {code_content}

  Provide a detailed analysis including:
  - File type ('controller',
       'config',
       'view',
       'model',
       'repository',
       'layout',
       'service',
       'middleware',
       'program' (for program.cs file),
       'csproj,
       'csproj_grpc',
       'program_cs_grpc')
  - Description of the file's purpose
  - Class names
  - Namespaces
  - Methods
  - External references
  - Framework features used
  - Dependencies
  - Design patterns used
  - Routes (for controllers only, extract from [Route], [HttpGet], [HttpPost], [HttpPut], [HttpDelete] attributes; if none, infer as /api/[controller_name_without_controller]s, e.g., CustomerController -> /api/customers, /api/customers/{{id}})
    Ensure routes are accurate and reflect the controller's endpoints.
  - If ASPX markup is present, infer entity fields from control IDs (like txtFirstName → FirstName, txtEmail → Email). 
    Avoid merging fields unless clearly combined in code-behind. Maintain original field names from markup.

  
  """
        
        result = await project_structure_analyzer_agent.run(
          user_prompt=prompt,
          model_settings={'temperature': 0.2}
        )

        # tokens = encoder.encode(result)
        # token_count = len(tokens)

        logger.info(f"Completed analysis for file: {file_path}.")
        return json.loads(result.data.model_dump_json())
      except Exception as e:
        logger.info(f"Error analyzing {file_path}: {str(e)}")
        return None
   
    async def create_analyzed_tree(self) -> Dict:
        tree = {}
        
        analysis_tasks = []
        semaphore = asyncio.Semaphore(10)  
        
        for root, _, files in os.walk(self.start_path):
            if any(pattern in root for pattern in self.ignore_patterns):
                continue
                
            for file in files:
                if file.endswith(('.cs', '.cshtml', '.razor')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.start_path)
                    
                    # Create a coroutine that respects the semaphore
                    async def analyze_with_semaphore(file_path, rel_path):
                        async with semaphore:
                            result = await self.analyze_code_file(file_path)
                            return rel_path, result
                    
                    analysis_tasks.append(analyze_with_semaphore(file_path, rel_path))
        
        # Run all analysis tasks concurrently
        results = await asyncio.gather(*analysis_tasks)
        
        # Build the tree from results
        for rel_path, analysis in results:
            if analysis:
                current = tree
                parts = rel_path.split(os.sep)
                
                # Build the path in the tree
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = analysis
        
        return tree

    async def create_target_structure(self, analyzed_structure: Dict, target_version: str, instruction: Optional[str] = None) -> Dict:
       # Default instruction if none provided
      instruction_text = instruction or (
          "Use the best of your knowledge to split into microservices following the onion ring architecture. "
            "Each microservice should be composed of multiple projects/layers such as Domain, Application, Infrastructure, and Presentation."
        )
      flattened_structure = await flatten_dict(analyzed_structure)

      has_auth = any(
          "auth" in file.lower() or "identity" in file.lower() or "login" in file.lower()
          for file in flattened_structure.keys()
      )
      logger.info(f"Authentication detected: {has_auth}")
       # Dynamic Instruction-Based Parsing
      instruction_lower = instruction_text.lower()
      instruction_clean = re.sub(r"\s*,\s*", " and ", instruction_lower)
      instruction_clean = re.sub(r"split into|microservices|services|api", "", instruction_clean)
      instruction_parts = [part.strip() for part in instruction_clean.split("and") if part.strip()]
      microservices = []
      for part in instruction_parts:
          name = re.sub(r"\s*(service|microservice)\s*", "", part).rstrip("s")
          if name and name not in microservices and name != "gateway":
              microservices.append(name)
      
      # Fallback: Derive from repo if instruction is vague
      if not microservices:
          logger.warning(f"No microservices parsed from instruction: '{instruction_text}', analyzing repo")
          possible_ms = {k.split('.')[0].lower().rstrip("s") for k in flattened_structure.keys()
                        if k.lower().endswith((".cs", ".csproj")) and "gateway" not in k.lower()}
          microservices = sorted(list(possible_ms))[:2]
          if not microservices:
              microservices = ["default1", "default2"]
              logger.error(f"No microservices found in repo, using defaults: {microservices}")
          else:
              logger.info(f"Derived microservices from repo: {microservices}")
      
      logger.debug(f"Final microservices: {microservices}")
      
      auth_type_str = "jwt"
    

      # Determine the case and set auth instruction
      if not has_auth:
          # Case 1: No auth in source
          auth_instruction = """
- No authentication is detected in the source repository.
- DO NOT include authentication in any microservice.
- The Gateway microservice MUST handle routing only with Ocelot.
"""
          logger.info("Case 1: No authentication detected in source; Gateway is routing-only")
          auth_enabled = False
      elif "auth" in instruction_lower or "auth service" in instruction_lower or "auth microservice" in instruction_lower or "authentication microservice" in instruction_lower:
          # Case 2: Auth in source, explicit auth service in instruction
          auth_instruction = f"""
- Authentication MUST be implemented in a separate 'AuthService' microservice with {auth_type_str.upper()} support:
  - **AuthService.Domain**: Entities/User.cs (from Infrastructure/Identity/ApplicationUser.cs), AuthService.Domain.csproj
  - **AuthService.Application**: Interfaces/IAuthService.cs, Services/AuthService.cs (from Infrastructure/Identity/Services/IdentityService.cs), AuthService.Application.csproj
  - **AuthService.Infrastructure**: Data/AuthDbContext.cs (from Infrastructure/Persistence/ApplicationDbContext.cs), AuthService.Infrastructure.csproj
  - **AuthService.Presentation**: Controllers/AuthController.cs (from WebApi/Controllers/AuthenticationController.cs), Models/JwtSettings.cs, Models/User.cs, Models/UserLogin.cs, appsettings.json, Program.cs, AuthService.Presentation.csproj
  - AuthService.sln
- The Gateway microservice MUST handle routing only, with no authentication logic or folders (e.g., Controllers/, Data/, Entities/, Models/, Views/).
- Ensure no empty folders or authentication-related files in the Gateway.
"""
          logger.info("Case 2: Authentication detected and explicitly requested as separate AuthService")
          auth_enabled = True
          if "AuthService" not in microservices:
            microservices.append("AuthService")
      else:
          # Case 3: Auth in source, no auth mentioned in instruction
          auth_instruction = f"""
- Authentication is detected in the source repository but not explicitly addressed in the instruction.
- By default, authentication MUST be included in the 'Gateway' microservice with {auth_type_str.upper()} support:
  - **Controllers/AuthController.cs**: Authentication endpoints (e.g., /login, /token), sourced from WebApi/Controllers/AuthenticationController.cs
  - **Data/AuthDbContext.cs**: EF Core context for auth data, sourced from Infrastructure/Persistence/ApplicationDbContext.cs
  - **Entities/User.cs**: User entity, sourced from Infrastructure/Identity/ApplicationUser.cs
  - **ocelot.json**: Routing configuration for all microservices
  - **appsettings.json**: Include JWT settings
  - **Program.cs**: Add JWT middleware configuration
  - **Gateway.csproj**: Project file with dependencies for routing and authentication
- DO NOT include a Models/ folder in the Gateway microservice. The User.cs file MUST be placed in the Entities/ folder, not Models/.
- DO NOT include a Views/ folder or any other folders unless explicitly listed above.
- Ensure no empty folders are included in the Gateway structure.
"""
          logger.info("Case 3: Authentication detected in source; included in Gateway by default")
          auth_enabled = True     
      
      prompt = f"""
You are a seasoned .NET Architect and microservices expert tasked with transforming a legacy .NET project into a modern, domain-driven microservice architecture. The goal is to identify natural service boundaries from the source code structure and dependencies, and design a target architecture that resolves common pitfalls.
Each microservice should be composed of multiple projects/layers such as Domain, Application, Infrastructure, and Presentation.


### Important Note:
If any target file is partially derived from code in a different file (not directly related), include that file in "source_files" as well. In the "description", explicitly mention how content from each source file contributes to generating the target file.

## Note:
Every microservice should have a .csproj and a Program.cs file, and follow the onion ring architecture.

### Input Details:
1. **Analyzed Legacy Structure**:
{json.dumps(analyzed_structure, indent=2)}

2. **Target .NET Version**: {target_version}

3. **Microservice Architecture Requirements**:
   - Split the project into microservices as specified: {instruction_text}.
   - ALWAYS include a 'Gateway' microservice for routing with Ocelot, unless explicitly excluded in the instruction.
   - Handle authentication based on the following conditions:
{auth_instruction}
   - For microservices specified in the instruction (e.g., User, Product, WebUI), include only their domain-specific logic and entities, adhering to the authentication strategy above.


### Key Requirements:
- **Mandatory MVC & Onion Architecture Structure**:
  * Each microservice must have Controllers/, Models/, and Views/ folders.
  * Each microservice should be split into multiple projects/layers (e.g., Domain, Application, Infrastructure, and Presentation).
  * Controller views must be in a Views/[ControllerNameWithoutSuffix]/ folder structure.
  * Shared views in Views/Shared/ with a proper _Layout.cshtml.
  * View models must be in a Models/ViewModels/ subfolder.
  * Every file should include source file mappings.
-**Gateway Specifics**:
  * The Gateway microservice MUST include at minimum: appsettings.json, Gateway.csproj, ocelot.json, Program.cs.
  * In Case 1 (no authentication), the Gateway MUST only handle routing with Ocelot and MUST NOT include Controllers/, Data/, Entities/, Models/, or Views/ folders.
  * In Case 3 (authentication in Gateway), include only the authentication files listed in the authentication conditions (Controllers/AuthController.cs, Data/AuthDbContext.cs, Entities/User.cs) and DO NOT include a Models/ or Views/ folder. The User.cs file MUST be in Entities/, not Models/.
  * In Case 2 (separate AuthService), the Gateway MUST NOT include authentication logic, Models/, or Views/ folders.
  * No empty folders — omit directories that would contain no files.
- **Code Quality**:
  * Convert WebForms .aspx to Razor views with proper @model directives.
  * Separate business logic from controllers into a Services/ folder.
  * Convert ASCX user controls to ViewComponents or partial views.
- **Project Essentials**:
  * Each microservice requires:
    - A .csproj file with proper dependencies.
    - A Program.cs file with a modern minimal hosting model.
    - An appsettings.json file.
    - A launchSettings.json file (inside a Properties folder).
- **Transformation Rules**:
  * Map .aspx.cs code-behind files to controllers.
  * Convert Web.config settings to appsettings.json.
  * Transform master pages to _Layout.cshtml.
  * Migrate ASPX markup to Razor syntax with Tag Helpers.


### Output Schema:
{{
  "microservices": [
    {{
      "name": "string",
      "projects": [
        {{
          "project_name": "string",
          "target_structure": {{
            "root": {{
              "file_name": {{
                "source_files": ["string"],
                "file_type": "controller|config|model|repository|view|layout|service|interface|middleware|program|csproj",
                "description": "string",
                "namespace": "string"
              }}
            }},
            "folders": {{
              "Controllers": {{
                "target_files": {{
                  "[ControllerName].cs": {{
                    "source_files": ["legacy_path.aspx.cs"],
                    "description": "string",
                    "file_type": "controller",
                    "namespace": "ServiceName.Controllers",
                    "routes": ["string"]
                  }}
                }},
                "subfolders": {{}}
              }},
              "Views": {{
                "target_files": {{
                  "_ViewImports.cshtml": {{"...": "..."}},
                  "_ViewStart.cshtml": {{"...": "..."}}
                }},
                "subfolders": {{
                  "[ControllerName]": {{
                    "target_files": {{
                      "[ActionName].cshtml": {{
                        "source_files": ["legacy_path.aspx"],
                        "description": "Converted Razor view",
                        "file_type": "cshtml"
                      }}
                    }}
                  }},
                  "Shared": {{
                    "target_files": {{
                      "_Layout.cshtml": {{"...": "..."}},
                      "[PartialView].cshtml": {{"...": "..."}}
                    }}
                  }}
                }}
              }},
              "Models": {{
                "target_files": {{}},
                "subfolders": {{
                  "Entities": {{
                    "target_files": {{}}
                  }},
                  "ViewModels": {{
                    "target_files": {{}}
                  }},
                  "Data": {{
                    "target_files": {{
                      "ApplicationDbContext.cs": {{"...": "..."}}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      ]
    }}
  ]
}}


"""
    
      llm = llm_config._llm
      with open('prompt.txt', 'w', encoding="utf-8") as f:
          f.write(prompt)

      response_new = llm.complete(prompt)
      sanitized_response = sanitize_content(str(response_new))

      with open("response_new.json", "w", encoding="utf-8") as f:
          f.write(sanitized_response)
    
      json_match = re.search(r'({.*})', sanitized_response, re.DOTALL)
      if json_match:
          sanitized_response = json_match.group(1)
      else:
                raise ValueError("JSON response not found in agent output.")
          
            
      target_structure = json.loads(sanitized_response)
      
      # Sanitize LLM response to enforce Case 2 Gateway structure
      for ms in target_structure.get('microservices', []):
          ms_name = ms.get('name', '').lower()
          if ms_name == 'gateway' and (
              "auth" in instruction_lower or "auth service" in instruction_lower or 
              "auth microservice" in instruction_lower or "authentication microservice" in instruction_lower
          ):
              # Case 2: Ensure Gateway is routing-only
              logger.info("Sanitizing Gateway for Case 2: Removing authentication-related folders")
              if 'projects' not in ms or not isinstance(ms.get('projects'), list) or not ms.get('projects'):
                  logger.warning("Gateway microservice has invalid or missing projects. Adding default structure.")
                  ms['projects'] = [{
                      'project_name': 'Gateway',
                      'target_structure': {
                          'root': {
                              'appsettings.json': {
                                  'file_type': 'config',
                                  'description': 'Gateway configuration',
                                  'namespace': '',
                                  'source_files': []
                              },
                              'Gateway.csproj': {
                                  'file_type': 'csproj',
                                  'description': 'API Gateway project with Ocelot dependencies',
                                  'namespace': '',
                                  'source_files': []
                              },
                              'ocelot.json': {
                                  'file_type': 'ocelot',
                                  'description': 'Ocelot routing configuration',
                                  'namespace': '',
                                  'source_files': []
                              },
                              'Program.cs': {
                                  'file_type': 'program',
                                  'description': 'Gateway entry point with Ocelot middleware',
                                  'namespace': 'Gateway',
                                  'source_files': []
                              }
                          },
                          'folders': {}
                      }
                  }]
              else:
                  # Remove authentication-related folders
                  for project in ms.get('projects', []):
                      if 'target_structure' in project:
                          folders = project['target_structure'].get('folders', {})
                          for folder in ['Controllers', 'Data', 'Entities', 'Models', 'Views']:
                              if folder in folders:
                                  logger.info(f"Removing {folder} folder from Gateway in Case 2")
                                  del folders[folder]
                          project['target_structure']['folders'] = {}  # Ensure no other folders remain
  
      # Validate Gateway structure
      if auth_enabled:
          gateway = next(
              (ms for ms in target_structure.get('microservices', []) if ms.get('name', '').lower() == 'gateway'),
              None
          )
      
          if not gateway:
              logger.error("Gateway microservice is missing from the microservices list.")
              raise KeyError("Gateway microservice not found in the microservices list.")
      
          projects = gateway.get('projects')
          if not projects or not isinstance(projects, list) or not projects:
              logger.warning(f"Gateway microservice has invalid or missing 'projects' key: {projects}. Adding default structure.")
              gateway['projects'] = [{
                  'project_name': 'Gateway',
                  'target_structure': {
                      'root': {
                          'appsettings.json': {
                              'file_type': 'config',
                              'description': 'Gateway configuration',
                              'namespace': '',
                              'source_files': []
                          },
                          'Gateway.csproj': {
                              'file_type': 'csproj',
                              'description': 'API Gateway project with Ocelot dependencies',
                              'namespace': '',
                              'source_files': []
                          },
                          'ocelot.json': {
                              'file_type': 'ocelot',
                              'description': 'Ocelot routing configuration',
                              'namespace': '',
                              'source_files': []
                          },
                          'Program.cs': {
                              'file_type': 'program',
                              'description': 'Gateway entry point with Ocelot middleware',
                              'namespace': 'Gateway',
                              'source_files': []
                          }
                      },
                      'folders': {}
                  }
              }]
              projects = gateway['projects']             
      
          gateway_project = projects[0].get('target_structure')
          if not gateway_project:
              logger.error("First project in Gateway microservice has no 'target_structure'")
              raise KeyError("Gateway microservice project missing 'target_structure'")
      
          # Only validate authentication files for Case 3
          if not (
              "auth" in instruction_lower or "auth service" in instruction_lower or 
              "auth microservice" in instruction_lower or "authentication microservice" in instruction_lower
          ):
              # Case 3: Validate authentication files in Gateway
              required_auth_files = ['Controllers/AuthController.cs', 'Data/AuthDbContext.cs', 'Entities/User.cs']
              missing_files = [
                  f for f in required_auth_files
                  if not any(
                      f.lower() in (
                          f'{folder}/{file}' if folder else file
                      ).lower()
                      for folder, files in gateway_project.get('folders', {}).items()
                      for file in files.get('target_files', {})
                  ) and f not in gateway_project.get('root', {})
              ]
          
              if missing_files:
                  logger.warning(f"Gateway missing required authentication files: {missing_files}")
              
                  # Ensure the top-level folders exist
                  gateway_project.setdefault('folders', {})
                  folders = gateway_project['folders']
                  folders.setdefault('Controllers', {'target_files': {}})
                  folders.setdefault('Data', {'target_files': {}})
                  folders.setdefault('Entities', {'target_files': {}})
              
                  # Populate missing files
                  for f in missing_files:
                      if f == 'Controllers/AuthController.cs':
                          folders['Controllers']['target_files']['AuthController.cs'] = {
                              'file_type': 'controller',
                              'description': 'Authentication endpoints (e.g., /login, /token)',
                              'namespace': 'Gateway.Controllers',
                              'routes': ['/api/auth/login', '/api/auth/token'],
                              'source_files': ['WebApi/Controllers/AuthenticationController.cs']
                          }
                      elif f == 'Data/AuthDbContext.cs':
                          folders['Data']['target_files']['AuthDbContext.cs'] = {
                              'file_type': 'dbcontext',
                              'description': 'EF Core context for auth data',
                              'namespace': 'Gateway.Data',
                              'source_files': ['Infrastructure/Persistence/ApplicationDbContext.cs']
                          }
                      elif f == 'Entities/User.cs':
                          folders['Entities']['target_files']['User.cs'] = {
                              'file_type': 'entity',
                              'description': 'User entity for authentication',
                              'namespace': 'Gateway.Entities',
                              'source_files': ['Infrastructure/Identity/ApplicationUser.cs']
                          }
          else:
              # Case 2: Ensure no authentication-related folders
              logger.info("Case 2: Skipping Gateway authentication validation")
              folders = gateway_project.get('folders', {})
              for folder in ['Controllers', 'Data', 'Entities', 'Models', 'Views']:
                  if folder in folders:
                      logger.info(f"Removing {folder} folder from Gateway in Case 2 validation")
                      del folders[folder]
              gateway_project['folders'] = {}  # Ensure no folders remain
      
      with open("response_new.json", "w", encoding="utf-8") as f:
          f.write(json.dumps(target_structure, indent=2))
      
      return target_structure


    async def create_grpc_target_structure(self, analyzed_structure: Dict, target_version: str, instruction: Optional[str] = None) -> Dict:
    # Default instruction updated to reflect ADO.NET usage instead of EF
      instruction_text = instruction or (
          "Use the best of your knowledge to split into microservices following the onion ring architecture. "
          "Each microservice should be composed of multiple projects/layers such as Domain, Application, Infrastructure, and Presentation. "
          "Use ADO.NET with manual MySQL queries (MySqlConnection, MySqlCommand, MySqlDataReader) for data access instead of Entity Framework."
      )
      
      flattened_structure = await flatten_dict(analyzed_structure)
      
      # Detect authentication
      has_auth = any(
          "auth" in file.lower() or "identity" in file.lower() or "login" in file.lower()
          for file in flattened_structure.keys()
      )
      # Filter unsupported file types for gRPC mappings
      unsupported_types = ['.asmx', '.ascx', '.aspx']
      
      valid_files = {
          k: v for k, v in flattened_structure.items()
          if not any(k.lower().endswith(ext) for ext in unsupported_types)
      }
      logger.debug(f"Valid source files: {list(valid_files.keys())}")
      filtered_structure = valid_files
      # Dynamic Instruction-Based Parsing
      instruction_lower = instruction_text.lower()
      
      instruction_clean = re.sub(r"\s*,\s*", " and ", instruction_lower)
      instruction_clean = re.sub(r"split into|microservices|services|api", "", instruction_clean)
      instruction_parts = [part.strip() for part in instruction_clean.split("and") if part.strip()]
      microservices = []
      for part in instruction_parts:
          name = re.sub(r"\s*(service|microservice)\s*", "", part).rstrip("s")
          if name and name not in microservices and name != "gateway":
              microservices.append(name + "Grpc")
      
      # Fallback: Derive from entities and UI logic
      if not microservices:
          logger.warning(f"No microservices parsed from instruction: '{instruction_text}', analyzing repo")
          possible_ms = set()
          for file in filtered_structure.keys():
              if file.lower().endswith((".cs", ".csproj")) and "gateway" not in file.lower():
                  if "entity" in file.lower() or "repository" in file.lower():
                      name = file.split('/')[-1].split('.')[0].lower().rstrip("s")
                      possible_ms.add(name + "Grpc")
          # Infer customer from Customers/Default.aspx.cs
          if any("customers/default.aspx.cs" in file.lower() for file in flattened_structure.keys()):
              possible_ms.add("customerGrpc")
          microservices = sorted(list(possible_ms))
          # Ensure product and customer are included if relevant
          if any("product" in file.lower() for file in filtered_structure.keys()):
              microservices.append("productGrpc")
          if any("customer" in file.lower() for file in flattened_structure.keys()):
              microservices.append("customerGrpc")
          microservices = sorted(list(set(microservices)))
          if not microservices:
              microservices = ["productGrpc", "customerGrpc"]
              logger.error(f"No microservices found in repo, using defaults: {microservices}")
          else:
              logger.info(f"Derived microservices from repo: {microservices}")
      logger.debug(f"Final microservices: {microservices}")
      
      # Authentication handling updated for ADO.NET
      auth_type_str = "jwt"
      
      if not has_auth:
          auth_instruction = """
  - No authentication is detected in the source repository.
  - DO NOT include authentication in any microservice.
  - The Gateway microservice MUST act as a gRPC client, routing HTTP requests to gRPC microservices using controllers and .proto files.
  """
          logger.info("Case 1: No authentication detected in source; Gateway is routing-only")
          auth_enabled = False
      elif "auth service" in instruction_lower or "authentication service" in instruction_lower or "authentication" in instruction_lower:
          auth_instruction = f"""
  - Authentication MUST be implemented in a separate 'AuthService' microservice with {auth_type_str.upper()} support:
    - **AuthService.Domain**: Entities/User.cs (from HelloASP/Models/IdentityModels.cs), AuthService.Domain.csproj
    - **AuthService.Application**: Interfaces/IAuthService.cs, Services/AuthService.cs (from HelloASP/App_Start/IdentityConfig.cs), AuthService.Application.csproj
    - **AuthService.Infrastructure**: Data/AuthDataAccess.cs (implements MySQL queries for user data using MySqlConnection, MySqlCommand, MySqlDataReader), AuthService.Infrastructure.csproj (include MySQLConnector)
    - **AuthService.Presentation**: Services/AuthService.cs, Protos/auth.proto, appsettings.json (include connection string), Program.cs, AuthService.Presentation.csproj
  - The Gateway microservice MUST handle routing only, with no authentication logic.
  """
          logger.info("Case 2: Authentication requested as separate AuthService")
          auth_enabled = True
          microservices.append("AuthService")
      else:
          auth_instruction = f"""
  - Authentication is detected in the source repository but not explicitly addressed.
  - Include authentication in the 'Gateway' microservice with {auth_type_str.upper()} support:
    - **Data/AuthDataAccess.cs**: ADO.NET-based data access for user data using MySqlConnection, MySqlCommand, MySqlDataReader
    - **Entities/User.cs**: User entity (from HelloASP/Models/IdentityModels.cs)
    - **appsettings.json**: Include connection string for MySQL Server
    - **Program.cs**: Add gRPC and JWT middleware configuration, remove EF middleware
  """
          logger.info("Case 3: Authentication included in Gateway by default")
          auth_enabled = True
      
      # Construct prompt with ADO.NET instructions
      prompt = f"""
  You are a seasoned .NET Architect and microservices expert tasked with transforming a legacy ASP.NET Web Forms project into a modern, domain-driven microservice architecture using gRPC and ADO.NET. The goal is to identify natural service boundaries from the source code structure and dependencies, and design a target architecture that resolves common pitfalls.
  Each microservice should be composed of multiple projects/layers such as Domain, Application, Infrastructure, and Presentation. Use ADO.NET (MySqlConnection, MySqlCommand, MySqlDataReader) with manual MySQL queries for data access instead of Entity Framework.
   ### Important Notes:
    - The legacy project uses ASP.NET Web Forms (.aspx, .aspx.cs), SOAP services (.asmx), and user controls (.ascx). DO NOT map .asmx, .ascx, or .aspx.cs files to .proto or grpc_service_cs files. Instead, derive gRPC services from entity and repository files (e.g., HelloASP.Data/Entity/Product.cs, HelloASP.Data/Repository/ProductRepository.cs).
    - For the 'customerGrpc' microservice, infer Customer entity from HelloASP/Customers/Default.aspx.cs if no Customer.cs exists, creating a Customer.cs with properties inferred from the input file. Use the same properties in CustomerDto.cs and CustomerDataAccess.cs to ensure consistency.
    - For files without source_files (e.g., appsettings.json, Program.cs), use provided descriptions, instructions, or default templates.
    - Include detailed 'instructions' in the target_structure to guide code generation.
    - Include a 'webUI' microservice with MVC structure (Controllers, Views, Models) to interact with gRPC services via clients.
    - Use ADO.NET with `MySQLConnector` (e.g., `MySQLConnection`, `MySQLCommand`, `MySQLDataReader`) and inline MySQL queries for data access. Retrieve connection strings from `appsettings.json` using `Configuration.GetConnectionString("DefaultConnection")`.
  ### Requirements:
  - **Mandatory Onion Architecture**:
    * Domain: Entities (e.g., Product.cs), Repositories (e.g., IProductRepository.cs).
    * Application: DTOs, Interfaces, Services.
    * Infrastructure: Data (e.g., ProductDataAccess.cs with MySQL queries using MySQLConnection), Repositories (e.g., ProductRepository.cs calling ProductDataAccess.cs).
    * Presentation: Protos (.proto files), Services (gRPC implementations), appsettings.json (with MySQL connection string), Program.cs, .csproj.
  - **gRPC Specifics**:
    * Generate .proto files from entities and repositories, defining RPCs for CRUD operations (e.g., GetProduct, ListProducts).
    * Service implementations (e.g., ProductGrpcService.cs) should use async methods and inherit from generated service base classes.
    * Example: For Product.cs with Id, Name, Description, create product.proto with ProductService (GetProduct, ListProducts) and messages (ProductRequest, ProductResponse).
  - **Gateway**:
    * Include appsettings.json (with MySQL connection string if auth_enabled), Gateway.csproj (include MySQLConnector if auth_enabled), Program.cs, gateway.sln.
    * Include Controllers folder with controller files for each microservice (e.g., productGrpcController.cs, cartGrpcController.cs) to handle HTTP requests and route to gRPC services.
    * Include Protos folder with .proto files for each microservice (e.g., productgrpc.proto, cartgrpc.proto) to define client-side gRPC service definitions.
    * Configure Program.cs to set up gRPC clients and HTTP endpoints for routing, remove EF middleware.
  - **WebUI**:
    * Include MVC structure: Controllers (e.g., ProductController.cs), Views (e.g., Product/Index.cshtml), Models.
    * Include gRPC clients (e.g., ProductGrpcClient.cs) derived from .proto files.
    * Include launchSettings.json.
  - **Transformation Rules**:
    * Derive .proto files from entity/repository files (e.g., Product.cs, ProductRepository.cs).
    * Map .aspx.cs business logic to Application layer services (e.g., ProductService.cs) if relevant.
    * Convert Web.config settings to appsettings.json with MySQL connection strings.
    * For webUI, convert .aspx to Razor views and .aspx.cs to MVC controllers using gRPC clients.
  ### Input Details:
  1. **Analyzed Legacy Structure**:  
  {json.dumps(filtered_structure, indent=2)}
  2. **Target .NET Version**: {target_version}
  3. **Microservice Architecture**:
    - Split into microservices: {', '.join(microservices)}.
    - ALWAYS include 'Gateway' for Ocelot routing and 'webUI' for MVC UI.
    - Handle authentication:
  {auth_instruction}
  ### Output Schema:
  {{
    "microservices": [
      {{
        "name": "string",
        "projects": [
          {{
            "project_name": "string",
            "target_structure": {{
              "root": {{
                "file_name": {{
                  "source_files": ["string"],
                  "file_type": "config|model|repository|service|program_cs_grpc|csproj_grpc|proto|grpc_service_cs|controller|view|data_access",
                  "description": "string",
                  "namespace": "string"
                }}
              }},
              "folders": {{
                "Entities": {{
                  "target_files": {{
                    "EntityName.cs": {{
                      "source_files": ["legacy/EntityName.cs"],
                      "file_type": "model",
                      "description": "Entity description",
                      "namespace": "Microservice.Domain.Entities"
                    }}
                  }}
                }},
                "Data": {{
                  "target_files": {{
                    "DataAccessName.cs": {{
                      "source_files": ["legacy/EntityName.cs"],
                      "file_type": "data_access",
                      "description": "ADO.NET data access with SQL queries matching entity properties",
                      "namespace": "Microservice.Infrastructure.Data"
                    }}
                  }}
                }},
                "Protos": {{
                  "target_files": {{
                    "[ServiceName].proto": {{
                      "source_files": ["legacy/EntityName.cs", "legacy/RepositoryName.cs"],
                      "file_type": "proto",
                      "description": "gRPC service definition",
                      "namespace": ""
                    }}
                  }}
                }}
              }}
            }}
          }}
        ]
      }}
    ]
  }}
  ### Example:(***only for reference, do not generate this as the target structure, taking this as reference generate the target structure according to the input dynamically.***)
  {{
    "microservices": [
      {{
        "name": "customerGrpc",
        "projects": [
          {{
            "project_name": "CustomerGrpc.Domain",
            "target_structure": {{
              "root": {{
                "CustomerGrpc.Domain.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Domain project file for Customer microservice",
                  "namespace": "CustomerGrpc.Domain"
                }}
              }},
              "folders": {{
                "Entities": {{
                  "target_files": {{
                    "Customer.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "model",
                      "description": "Customer entity inferred from UI logic",
                      "namespace": "CustomerGrpc.Domain.Entities"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Repositories": {{
                  "target_files": {{
                    "ICustomerRepository.cs": {{
                      "source_files": [],
                      "file_type": "interface",
                      "description": "Interface for Customer repository",
                      "namespace": "CustomerGrpc.Domain.Repositories"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }},
          {{
            "project_name": "CustomerGrpc.Application",
            "target_structure": {{
              "root": {{
                "CustomerGrpc.Application.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Application project file for Customer microservice",
                  "namespace": "CustomerGrpc.Application"
                }}
              }},
              "folders": {{
                "DTOs": {{
                  "target_files": {{
                    "CustomerDto.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "dto",
                      "description": "DTO for Customer entity",
                      "namespace": "CustomerGrpc.Application.DTOs"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Interfaces": {{
                  "target_files": {{
                    "ICustomerService.cs": {{
                      "source_files": [],
                      "file_type": "interface",
                      "description": "Interface for Customer service",
                      "namespace": "CustomerGrpc.Application.Interfaces"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Services": {{
                  "target_files": {{
                    "CustomerService.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "service",
                      "description": "Implementation of Customer service",
                      "namespace": "CustomerGrpc.Application.Services"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }},
          {{
            "project_name": "CustomerGrpc.Infrastructure",
            "target_structure": {{
              "root": {{
                "CustomerGrpc.Infrastructure.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Infrastructure project file for Customer microservice, includes MySQLConnector",
                  "namespace": "CustomerGrpc.Infrastructure",
                  "instructions": "Target net8.0; include MySQLConnector for ADO.NET; reference Domain and Application projects"
                }}
              }},
              "folders": {{
                "Data": {{
                  "target_files": {{
                    "CustomerDataAccess.cs": {{
                      "source_files": [],
                      "file_type": "data_access",
                      "description": "ADO.NET data access for Customer with MySQL queries using MySqlConnection, MySqlCommand, MySqlDataReader",
                      "namespace": "CustomerGrpc.Infrastructure.Data",
                      "instructions": "Implement async CRUD methods (GetCustomer, ListCustomers) using MySQLConnection and parameterized MySQL queries"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Repositories": {{
                  "target_files": {{
                    "CustomerRepository.cs": {{
                      "source_files": [],
                      "file_type": "repository",
                      "description": "Implementation of Customer repository calling CustomerDataAccess.cs",
                      "namespace": "CustomerGrpc.Infrastructure.Repositories"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }},
          {{
            "project_name": "CustomerGrpc.Presentation",
            "target_structure": {{
              "root": {{
                "appsettings.json": {{
                  "source_files": ["HelloASP/Web.config"],
                  "file_type": "config",
                  "description": "Configuration for Customer gRPC service with MySQL connection string"
                }},
                "CustomerGrpc.Presentation.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Presentation project file for Customer microservice",
                  "namespace": "CustomerGrpc.Presentation"
                }},
                "Program.cs": {{
                  "source_files": [],
                  "file_type": "program_cs_grpc",
                  "description": "Entry point for the Customer gRPC service, no EF middleware"
                }}
              }},
              "folders": {{
                "Protos": {{
                  "target_files": {{
                    "customergrpc.proto": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "proto",
                      "description": "gRPC service definition for Customer",
                      "namespace": ""
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Services": {{
                  "target_files": {{
                    "CustomerGrpcService.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "grpc_service_cs",
                      "description": "gRPC service implementation for Customer",
                      "namespace": "CustomerGrpc.Presentation.Services"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Properties": {{
                  "target_files": {{
                    "launchSettings.json": {{
                      "source_files": [],
                      "file_type": "config",
                      "description": "Launch settings for the Customer gRPC service"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }}
        ]
      }},
      {{
        "name": "gateway",
        "projects": [
          {{
            "project_name": "Gateway",
            "target_structure": {{
              "root": {{
                "appsettings.json": {{
                  "source_files": ["HelloASP/Web.config"],
                  "file_type": "config",
                  "description": "Configuration settings for Gateway with MySQL connection string if auth_enabled"
                }},
                "Gateway.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Gateway project file, includes MySQLConnector if auth_enabled",
                  "instructions": "Target net8.0; include Grpc.Net.Client, Grpc.Net.ClientFactory, Microsoft.AspNetCore.Mvc, Microsoft.Extensions.Logging, and MySQLConnector if auth_enabled"
                }},
                "Program.cs": {{
                  "source_files": [],
                  "file_type": "program_cs_grpc",
                  "description": "Entry point for the Gateway application, no EF middleware"
                }},
                "gateway.sln": {{
                  "source_files": [],
                  "file_type": "sln",
                  "description": "Solution file for Gateway microservice"
                }}
              }},
              "folders": {{
                "Entity": {{
                  "target_files": {{
                    "User.cs": {{
                      "source_files": [],
                      "file_type": "model",
                      "description": "User entity for authentication",
                      "namespace": "Gateway.Entity"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Data": {{
                  "target_files": {{
                    "AuthDataAccess.cs": {{
                      "source_files": [],
                      "file_type": "data_access",
                      "description": "ADO.NET data access for authentication with MySQL queries",
                      "namespace": "Gateway.Data",
                      "instructions": "Implement async methods for user authentication using MySqlConnection, MySqlCommand, MySqlDataReader"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Protos": {{
                  "target_files": {{
                    "customergrpc.proto": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "proto",
                      "description": "gRPC service definition for Customer",
                      "namespace": ""
                    }},
                    "productgrpc.proto": {{
                      "source_files": ["HelloASP.Data/Entity/Product.cs"],
                      "file_type": "proto",
                      "description": "gRPC service definition for Product",
                      "namespace": ""
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Controllers": {{
                  "target_files": {{
                    "CustomerGrpcController.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "controller",
                      "description": "Controller for Customer gRPC routing",
                      "namespace": "Gateway.Controllers"
                    }},
                    "ProductGrpcController.cs": {{
                      "source_files": ["HelloASP/Product/ProductList.aspx.cs"],
                      "file_type": "controller",
                      "description": "Controller for Product gRPC routing",
                      "namespace": "Gateway.Controllers"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Properties": {{
                  "target_files": {{
                    "launchSettings.json": {{
                      "source_files": [],
                      "file_type": "config"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }}
        ]
      }},
      {{
        "name": "productGrpc",
        "projects": [
          {{
            "project_name": "ProductGrpc.Domain",
            "target_structure": {{
              "root": {{
                "ProductGrpc.Domain.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Domain project file for Product microservice",
                  "namespace": "ProductGrpc.Domain"
                }}
              }},
              "folders": {{
                "Entities": {{
                  "target_files": {{
                    "Product.cs": {{
                      "source_files": ["HelloASP.Data/Entity/Product.cs"],
                      "file_type": "model",
                      "description": "Product entity",
                      "namespace": "ProductGrpc.Domain.Entities"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Repositories": {{
                  "target_files": {{
                    "IProductRepository.cs": {{
                      "source_files": [],
                      "file_type": "interface",
                      "description": "Interface for Product repository",
                      "namespace": "ProductGrpc.Domain.Repositories"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }},
          {{
            "project_name": "ProductGrpc.Application",
            "target_structure": {{
              "root": {{
                "ProductGrpc.Application.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Application project file for Product microservice",
                  "namespace": "ProductGrpc.Application"
                }}
              }},
              "folders": {{
                "DTOs": {{
                  "target_files": {{
                    "ProductDto.cs": {{
                      "source_files": ["HelloASP.Data/Entity/Product.cs"],
                      "file_type": "dto",
                      "description": "DTO for Product entity",
                      "namespace": "ProductGrpc.Application.DTOs"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Interfaces": {{
                  "target_files": {{
                    "IProductService.cs": {{
                      "source_files": [],
                      "file_type": "interface",
                      "description": "Interface for Product service",
                      "namespace": "ProductGrpc.Application.Interfaces"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Services": {{
                  "target_files": {{
                    "ProductService.cs": {{
                      "source_files": ["HelloASP.Data/Repository/ProductRepository.cs"],
                      "file_type": "service",
                      "description": "Implementation of Product service",
                      "namespace": "ProductGrpc.Application.Services"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }},
          {{
            "project_name": "ProductGrpc.Infrastructure",
            "target_structure": {{
              "root": {{
                "ProductGrpc.Infrastructure.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Infrastructure project file for Product microservice, includes MySQLConnector",
                  "namespace": "ProductGrpc.Infrastructure",
                  "instructions": "Target net8.0; include MySQLConnector for ADO.NET; reference Domain and Application projects"
                }}
              }},
              "folders": {{
                "Data": {{
                  "target_files": {{
                    "ProductDataAccess.cs": {{
                      "source_files": ["HelloASP.Data/Entity/Product.cs"],
                      "file_type": "data_access",
                      "description": "ADO.NET data access for Product with MySQL queries using MySqlConnection, MySqlCommand, MySqlDataReader",
                      "namespace": "ProductGrpc.Infrastructure.Data",
                      "instructions": "Implement async CRUD methods (GetProduct, ListProducts) using MySQLConnection and parameterized MySQL queries"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Repositories": {{
                  "target_files": {{
                    "ProductRepository.cs": {{
                      "source_files": ["HelloASP.Data/Repository/ProductRepository.cs"],
                      "file_type": "repository",
                      "description": "Implementation of Product repository calling ProductDataAccess.cs",
                      "namespace": "ProductGrpc.Infrastructure.Repositories"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }},
          {{
            "project_name": "ProductGrpc.Presentation",
            "target_structure": {{
              "root": {{
                "appsettings.json": {{
                  "source_files": ["HelloASP/Web.config"],
                  "file_type": "config",
                  "description": "Configuration for Product gRPC service with MySQL connection string"
                }},
                "ProductGrpc.Presentation.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Presentation project file for Product microservice",
                  "namespace": "ProductGrpc.Presentation"
                }},
                "Program.cs": {{
                  "source_files": [],
                  "file_type": "program_cs_grpc",
                  "description": "Entry point for the Product gRPC service, no EF middleware"
                }}
              }},
              "folders": {{
                "Protos": {{
                  "target_files": {{
                    "productgrpc.proto": {{
                      "source_files": ["HelloASP.Data/Entity/Product.cs", "HelloASP.Data/Repository/ProductRepository.cs"],
                      "file_type": "proto",
                      "description": "gRPC service definition for Product",
                      "namespace": ""
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Services": {{
                  "target_files": {{
                    "ProductGrpcService.cs": {{
                      "source_files": ["HelloASP.Data/Repository/ProductRepository.cs"],
                      "file_type": "grpc_service_cs",
                      "description": "gRPC service implementation for Product",
                      "namespace": "ProductGrpc.Presentation.Services"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Properties": {{
                  "target_files": {{
                    "launchSettings.json": {{
                      "source_files": [],
                      "file_type": "config",
                      "description": "Launch settings for the Product gRPC service"
                    }}
                  }},
                  "subfolders": {{}}
                }}
              }}
            }}
          }}
        ]
      }},
      {{
        "name": "webUI",
        "projects": [
          {{
            "project_name": "WebUI.Presentation",
            "target_structure": {{
              "root": {{
                "appsettings.json": {{
                  "source_files": ["HelloASP/Web.config"],
                  "file_type": "config",
                  "description": "Configuration for WebUI with MySQL connection string if auth_enabled"
                }},
                "WebUI.Presentation.csproj": {{
                  "source_files": [],
                  "file_type": "csproj_grpc",
                  "description": "Web UI project file"
                }},
                "Program.cs": {{
                  "source_files": [],
                  "file_type": "program_cs_grpc",
                  "description": "Entry point for the WebUI application, no EF middleware"
                }}
              }},
              "folders": {{
                "Controllers": {{
                  "target_files": {{
                    "AuthController.cs": {{
                      "source_files": [],
                      "file_type": "controller",
                      "description": "Controller for authentication UI",
                      "namespace": "WebUI.Presentation.Controllers"
                    }},
                    "CustomerController.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "controller",
                      "description": "Controller for Customer UI",
                      "namespace": "WebUI.Presentation.Controllers"
                    }},
                    "HomeController.cs": {{
                      "source_files": [],
                      "file_type": "controller",
                      "description": "Controller for home page",
                      "namespace": "WebUI.Presentation.Controllers"
                    }},
                    "ProductController.cs": {{
                      "source_files": ["HelloASP/Product/ProductList.aspx.cs"],
                      "file_type": "controller",
                      "description": "Controller for Product UI",
                      "namespace": "WebUI.Presentation.Controllers"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Models": {{
                  "target_files": {{
                    "Customer.cs": {{
                      "source_files": ["HelloASP/Customers/Default.aspx.cs"],
                      "file_type": "model",
                      "description": "Customer model for UI",
                      "namespace": "WebUI.Presentation.Models"
                    }},
                    "LoginViewModel.cs": {{
                      "source_files": [],
                      "file_type": "model",
                      "description": "Model for login view",
                      "namespace": "WebUI.Presentation.Models"
                    }},
                    "Product.cs": {{
                      "source_files": ["HelloASP.Data/Entity/Product.cs"],
                      "file_type": "model",
                      "description": "Product model for UI",
                      "namespace": "WebUI.Presentation.Models"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "Views": {{
                  "target_files": {{
                    "_ViewImports.cshtml": {{
                      "source_files": ["HelloASP/Views/_ViewStart.cshtml"],
                      "file_type": "view",
                      "description": "Razor view imports"
                    }},
                    "_ViewStart.cshtml": {{
                      "source_files": ["HelloASP/Views/_ViewStart.cshtml"],
                      "file_type": "view",
                      "description": "Razor view startup configuration"
                    }}
                  }},
                  "subfolders": {{
                    "Auth": {{
                      "target_files": {{
                        "Login.cshtml": {{
                          "source_files": [],
                          "file_type": "view",
                          "description": "Login view for authentication",
                          "namespace": ""
                        }}
                      }},
                      "subfolders": {{}}
                    }},
                    "Customer": {{
                      "target_files": {{
                        "Index.cshtml": {{
                          "source_files": ["HelloASP/Customers/Default.aspx"],
                          "file_type": "view",
                          "description": "Customer list view"
                        }}
                      }},
                      "subfolders": {{}}
                    }},
                    "Home": {{
                      "target_files": {{
                        "Index.cshtml": {{
                          "source_files": [],
                          "file_type": "view",
                          "description": "Home page view"
                        }}
                      }},
                      "subfolders": {{}}
                    }},
                    "Product": {{
                      "target_files": {{
                        "Index.cshtml": {{
                          "source_files": ["HelloASP/Product/ProductList.aspx"],
                          "file_type": "view",
                          "description": "Product list view"
                        }},
                        "Update.cshtml": {{
                          "source_files": [],
                          "file_type": "view",
                          "description": "Product update view"
                        }}
                      }},
                      "subfolders": {{}}
                    }},
                    "Shared": {{
                      "target_files": {{
                        "_Layout.cshtml": {{
                          "source_files": ["HelloASP/Views/Shared/_Layout.cshtml"],
                          "file_type": "view",
                          "description": "Shared layout view"
                        }}
                      }},
                      "subfolders": {{}}
                    }}
                  }}
                }},
                "Properties": {{
                  "target_files": {{
                    "launchSettings.json": {{
                      "source_files": [],
                      "file_type": "config",
                      "description": "Launch settings for the WebUI application"
                    }}
                  }},
                  "subfolders": {{}}
                }},
                "wwwroot": {{
                  "target_files": {{}},
                  "subfolders": {{
                    "content": {{
                      "target_files": {{
                        "bootstrap-grid.css": {{
                          "source_files": [],
                          "file_type": "config",
                          "description": "Bootstrap grid CSS"
                        }},
                        "Site.css": {{
                          "source_files": ["HelloASP/Content/Site.css"],
                          "file_type": "config",
                          "description": "Site-specific CSS"
                        }}
                      }},
                      "subfolders": {{}}
                    }},
                    "scripts": {{
                      "target_files": {{
                        "bootstrap.bundle.js": {{
                          "source_files": [],
                          "file_type": "config",
                          "description": "Bootstrap JavaScript bundle"
                        }},
                        "WebForms.js": {{
                          "source_files": [],
                          "file_type": "config",
                          "description": "WebForms JavaScript"
                        }},
                        "WebParts.js": {{
                          "source_files": [],
                          "file_type": "config",
                          "description": "WebParts JavaScript"
                        }},
                        "WebUIValidation.js": {{
                          "source_files": [],
                          "file_type": "config",
                          "description": "WebUI validation JavaScript"
                        }}
                      }},
                      "subfolders": {{}}
                    }}
                  }}
                }}
              }}
            }}
          }}
        ]
      }}
    ]
  }}
  """
      
      # Process LLM response
      llm = llm_config._llm
      with open('prompt_grpc.txt', 'w', encoding="utf-8") as f:
          f.write(prompt)
      
      response_new = llm.complete(prompt)
      sanitized_response = sanitize_content(str(response_new))
      
      with open("response_raw.json", "w", encoding="utf-8") as f:
          f.write(sanitized_response)
      
      try:
          json_result = json.loads(sanitized_response)
      except json.JSONDecodeError:
          json_match = re.search(r'({.*})', sanitized_response, re.DOTALL)
          if json_match:
              json_result = json.loads(json_match.group(1))
          else:
              logger.error("Failed to parse JSON from LLM response")
              raise ValueError("JSON response not found in agent output.")
      
      # Locate Gateway microservice
      gateway = next((ms for ms in json_result['microservices'] if ms['name'].lower() == 'gateway'), None)
      if not gateway:
          logger.error("Gateway microservice not found in target structure")
          raise ValueError("Gateway microservice is required for gRPC architecture")
      
      gateway_project = gateway['projects'][0]['target_structure']
      
      # Remove authentication-related files if auth_enabled = False
      if not auth_enabled:
          if 'folders' in gateway_project:
              if 'Data' in gateway_project['folders']:
                  del gateway_project['folders']['Data']
              if 'Entities' in gateway_project['folders']:
                  del gateway_project['folders']['Entities']
              if 'Controllers' in gateway_project['folders']:
                  gateway_project['folders']['Controllers']['target_files'] = {
                      k: v for k, v in gateway_project['folders']['Controllers']['target_files'].items()
                      if 'auth' not in k.lower()
                  }
      
      # Core files required for gRPC Gateway
      base_gateway_files = [
          'appsettings.json',
          'Gateway.csproj',
          'gateway.sln',
          'Program.cs',
          'Properties/launchSettings.json',
      ]
      
      # Dynamically build expected controller and proto file paths with consistent naming
      grpc_services = [ms['name'] for ms in json_result['microservices'] if ms['name'].lower() not in ['gateway', 'webui']]
      dynamic_grpc_files = []
      for service in grpc_services:
          service_base = service.lower().replace('grpc', '')
          controller_file = f'Controllers/{service}Controller.cs'
          proto_file = f'Protos/{service_base}grpc.proto'
          dynamic_grpc_files.extend([controller_file, proto_file])
      
      # Final list of required files
      required_files = base_gateway_files + dynamic_grpc_files
      
      # Check for missing files and remove redundant .proto/controller files
      if 'folders' in gateway_project and 'Protos' in gateway_project['folders']:
          existing_protos = list(gateway_project['folders']['Protos']['target_files'].keys())
          for proto in existing_protos:
              proto_service = proto.replace('.proto', '').lower()
              if proto_service in [s.lower().replace('grpc', '') for s in grpc_services]:
                  del gateway_project['folders']['Protos']['target_files'][proto]
      
      if 'folders' in gateway_project and 'Controllers' in gateway_project['folders']:
          existing_controllers = list(gateway_project['folders']['Controllers']['target_files'].keys())
          for controller in existing_controllers:
              controller_service = controller.replace('Controller.cs', '').lower()
              if controller_service in [s.lower().replace('grpc', '') for s in grpc_services]:
                  del gateway_project['folders']['Controllers']['target_files'][controller]
      
      # Check for missing files
      missing_files = [
          f for f in required_files
          if not any(
              f.lower() in (
                  f'{folder}/{file}' if folder else file
              ).lower()
              for folder, files in gateway_project.get('folders', {}).items()
              for file in files.get('target_files', {})
          ) and f not in gateway_project.get('root', {})
      ]
      
      if missing_files:
          logger.warning(f"Gateway missing required gRPC files: {missing_files}")
          
          # Ensure folder structure exists
          if 'folders' not in gateway_project:
              gateway_project['folders'] = {}
          if 'Controllers' not in gateway_project['folders']:
              gateway_project['folders']['Controllers'] = {'target_files': {}, 'subfolders': {}}
          if 'Protos' not in gateway_project['folders']:
              gateway_project['folders']['Protos'] = {'target_files': {}, 'subfolders': {}}
          if 'Properties' not in gateway_project['folders']:
              gateway_project['folders']['Properties'] = {'target_files': {}, 'subfolders': {}}
          
          # Add missing files dynamically
          for f in missing_files:
              if f == 'appsettings.json':
                  gateway_project['root']['appsettings.json'] = {
                      'source_files': [sf for sf in flattened_structure.keys() if 'web.config' in sf.lower() or 'appsettings' in sf.lower()],
                      'file_type': 'config',
                      'description': 'Configuration settings for Gateway with gRPC client endpoints and MySQL connection string if auth_enabled',
                      'instructions': 'Include logging (Information level), gRPC service endpoints for productGrpc (port 5001), cartGrpc (port 5002), orderGrpc (port 5003), webappGrpc (port 5004), and MySQL connection string if auth_enabled',
                      'namespace': ''
                  }
              elif f == 'Gateway.csproj':
                  gateway_project['root']['Gateway.csproj'] = {
                      'source_files': [sf for sf in flattened_structure.keys() if sf.lower().endswith('.csproj')],
                      'file_type': 'csproj_grpc',
                      'description': 'Gateway project file with gRPC client dependencies and MySQLConnector if auth_enabled',
                      'instructions': 'Target net8.0; include Grpc.Net.Client, Grpc.Net.ClientFactory, Microsoft.AspNetCore.Mvc, Microsoft.Extensions.Logging, and MySQLConnector if auth_enabled; reference .proto files in Protos folder',
                      'namespace': ''
                  }
              elif f == 'gateway.sln':
                  gateway_project['root']['gateway.sln'] = {
                      'source_files': [sf for sf in flattened_structure.keys() if sf.lower().endswith('.sln')],
                      'file_type': 'sln',
                      'description': 'Solution file for Gateway microservice',
                      'instructions': 'Include Gateway project and ensure compatibility with .NET 8.0',
                      'namespace': ''
                  }
              elif f == 'Program.cs':
                  gateway_project['root']['Program.cs'] = {
                      'source_files': [sf for sf in flattened_structure.keys() if 'startup.cs' in sf.lower() or 'program.cs' in sf.lower()],
                      'file_type': 'program_cs_grpc',
                      'description': 'Entry point for Gateway with gRPC client setup, no EF middleware',
                      'instructions': 'Configure ASP.NET Core with gRPC clients for productGrpc, cartGrpc, orderGrpc, and webappGrpc; set up MVC for HTTP-to-gRPC routing; use minimal API or controllers; configure logging; no EF middleware',
                      'namespace': 'Gateway'
                  }
              elif f == 'Properties/launchSettings.json':
                  gateway_project['folders']['Properties']['target_files']['launchSettings.json'] = {
                      'source_files': [sf for sf in flattened_structure.keys() if 'launchsettings' in sf.lower()],
                      'file_type': 'config',
                      'description': 'Launch settings for Gateway development',
                      'instructions': 'Include HTTP profile with port 5000, HTTPS profile with port 5005, and Development environment settings',
                      'namespace': ''
                  }
              elif f.startswith('Controllers/') and f.endswith('Controller.cs'):
                  service_name = f.replace('Controllers/', '').replace('Controller.cs', '')
                  service_base = service_name.lower().replace('grpc', '')
                  gateway_project['folders']['Controllers']['target_files'][f'{service_name}Controller.cs'] = {
                      'source_files': [
                          sf for sf in flattened_structure.keys()
                          if service_base in sf.lower() and sf.lower().endswith('.cs') and
                          ('entity' in sf.lower() or 'model' in sf.lower() or 'repository' in sf.lower() or 'aspx.cs' in sf.lower())
                      ],
                      'file_type': 'controller',
                      'description': f'Controller for routing HTTP requests to {service_name} gRPC service',
                      'instructions': f'Create an ASP.NET Core controller with async actions (Get{service_base.capitalize()}, List{service_base.capitalize()}s) to call {service_name} gRPC service using Grpc.Net.Client; inject gRPC client via constructor; use routes /api/{service_base}/get and /api/{service_base}/list',
                      'namespace': 'Gateway.Controllers',
                      'routes': [f'/api/{service_base}/get', f'/api/{service_base}/list']
                  }
              elif f.startswith('Protos/') and f.endswith('.proto'):
                  service_name = f.replace('Protos/', '').replace('.proto', '')
                  service_base = service_name.lower().replace('grpc', '')
                  gateway_project['folders']['Protos']['target_files'][f'{service_name}.proto'] = {
                      'source_files': [
                          sf for sf in flattened_structure.keys()
                          if service_base in sf.lower() and sf.lower().endswith('.cs') and
                          ('entity' in sf.lower() or 'model' in sf.lower() or 'repository' in sf.lower() or 'aspx.cs' in sf.lower())
                      ],
                      'file_type': 'proto',
                      'description': f'gRPC service definition for {service_name} microservice client',
                      'instructions': f'Define {service_base.capitalize()}Service with Get{service_base.capitalize()} (takes {service_base.capitalize()}Request with id, returns {service_base.capitalize()}Response) and List{service_base.capitalize()}s (returns {service_base.capitalize()}ListResponse); derive messages from entity/model classes',
                      'namespace': service_base
                  }
      
      # Ensure downstream microservices have .proto files with consistent naming
      for ms in json_result['microservices']:
          if ms['name'].lower() not in ['gateway', 'webui']:
              for project in ms['projects']:
                  if 'Presentation' in project['project_name']:
                      if 'folders' not in project['target_structure']:
                          project['target_structure']['folders'] = {}
                      if 'Protos' not in project['target_structure']['folders']:
                          project['target_structure']['folders']['Protos'] = {'target_files': {}, 'subfolders': {}}
                      service_base = ms['name'].lower().replace('grpc', '')
                      proto_file = f"{service_base}grpc.proto"
                      # Remove redundant .proto files
                      existing_protos = list(project['target_structure']['folders']['Protos']['target_files'].keys())
                      for proto in existing_protos:
                          if proto != proto_file and proto.replace('.proto', '').lower() == service_base:
                              del project['target_structure']['folders']['Protos']['target_files'][proto]
                      relevant_files = [
                          f for f in flattened_structure.keys()
                          if service_base in f.lower() and
                          f.lower().endswith('.cs') and
                          ('entity' in f.lower() or 'model' in f.lower() or 'repository' in f.lower()) and
                          '/' not in f.split('/')[-1]
                      ]
                      if not relevant_files:
                          relevant_files = [
                              f for f in flattened_structure.keys()
                              if service_base in f.lower() and
                              f.lower().endswith('.cs') and
                              'aspx.cs' in f.lower() and
                              '/' not in f.split('/')[-1]
                          ]
                      project['target_structure']['folders']['Protos']['target_files'][proto_file] = {
                          'source_files': relevant_files,
                          'file_type': 'proto',
                          'description': f"gRPC service definition for {ms['name']} microservice",
                          'instructions': f"Define {service_base.capitalize()}Service with Get{service_base.capitalize()} (takes {service_base.capitalize()}Request with id, returns {service_base.capitalize()}Response) and List{service_base.capitalize()}s (returns {service_base.capitalize()}ListResponse)",
                          'namespace': service_base
                      }
                      logger.debug(f"Source files for {proto_file}: {relevant_files}")
      
      # Save the updated target structure
      with open("response_grpc.json", "w", encoding="utf-8") as f:
          json.dump(json_result, f, indent=2)
      
      return json_result
    
    async def regenerate_target_structure(self, analysis_tree: Dict, current_target: Dict, comments: str) -> Dict:
        try:
            prompt = f"""
Analyze this existing microservice architecture and modify it based on the provided feedback:

Current Analysis Tree:
{json.dumps(analysis_tree, indent=2)}

Current Target Structure:
{json.dumps(current_target, indent=2)}

Feedback to Address:
{comments}

Requirements:
- Maintain microservice best practices
- Address all feedback points
- Keep independent deployability
- Preserve proper namespacing
- Ensure all files are properly mapped
- Every project must have a csproj file
- Verify source file mappings

Return modified structure following exact same schema as current target.
"""
            
            input_tokens = encoder.encode(prompt)

            response = await target_structure_creator_agent.run(
                user_prompt=prompt,
                model_settings={'temperature': 0.3}
            )

            output_tokens = encoder.encode(response)
            logger.info(f"Completed regeneration of target structure. Input tokens: {len(input_tokens)}, Output tokens: {len(output_tokens)}")


            return json.loads(response.data.model_dump_json())
        except Exception as e:
            print(f"Error regenerating target structure: {str(e)}")
            return {"projects": []}