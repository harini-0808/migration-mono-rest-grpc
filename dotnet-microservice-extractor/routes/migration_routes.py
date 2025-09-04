import hashlib
import aiofiles
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Literal, Optional
from models.response_models import ResponseModel
from services.migration_service import Migrator
from services.analysis_service import ProjectAnalyzer
from utils.file_utils import ensure_directory_exists, safe_remove_directory, clear_empty_folders
from utils.git_helpers import clone_repository
from utils import logger
import os
import zipfile
import tempfile
import base64
from config.db_config import Base, SessionLocal, engine
from sqlalchemy.orm import Session
from models.db import Analysis
from fastapi.responses import FileResponse
from services.target_structure_rag_service import TargetStructureRagService
from config.llm_config import pydantic_ai_model
from pydantic_ai import Agent
import json
from sqlalchemy import inspect
from auth import get_current_user, create_access_token, verify_password, oauth2_scheme
from models.db import User

Base.metadata.create_all(bind=engine)

# Check if api_type column exists, if not, add it
def ensure_api_type_column_exists():
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('analysis')]
        if 'api_type' not in columns:
            with engine.connect() as connection:
                connection.execute("ALTER TABLE analysis ADD COLUMN api_type VARCHAR(20)")
                connection.commit()
                logger.info("Added missing api_type column to analysis table")
    except Exception as e:
        logger.error(f"Error checking/adding api_type column: {str(e)}")

# Check if zip_content column exists, if not, add it
def ensure_zip_content_column_exists():
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('analysis')]
        if 'zip_content' not in columns:
            with engine.connect() as connection:
                connection.execute("ALTER TABLE analysis ADD COLUMN zip_content LONGTEXT")
                connection.commit()
                logger.info("Added missing zip_content column to analysis table")
    except Exception as e:
        logger.error(f"Error checking/adding zip_content column: {str(e)}")

ensure_api_type_column_exists()
ensure_zip_content_column_exists()

def get_db():  
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FileRecommendation(BaseModel):
    description: str
    file_type: Literal['controller', 'config', 'view', 'model', 'repository']

class AnalysisRequest(BaseModel):
    repo_url: Optional[str] = None
    target_version: Literal["net6.0", "net7.0", "net8.0"]
    api_type: Literal["rest", "grpc"]
    instruction: Optional[str] = None
    source_type: Optional[Literal["git", "zip"]] = None

class MigrationRequest(BaseModel):
    analysis_id: str
    target_structure: Dict
    instruction: Optional[str] = None

class RegenerationRequest(BaseModel):
    analysis_id: str
    target_structure: Dict
    comments: str

class RecommendRequest(BaseModel):
    file_name: str

file_recommendation_agent = Agent(
    model=pydantic_ai_model,
    result_type=FileRecommendation,
    system_prompt="You are an expert .NET code reviewer specialized in providing concise file recommendations. Your responses should include only a brief description (around 100 words) of the file's purpose and classify it as one of: controller, config, view, model, or repository.",
)

router = APIRouter()

current_dir = os.getcwd()
output_dir = os.path.join(current_dir, 'output')
try:
    ensure_directory_exists(path=output_dir)
    logger.info(f"Output directory created/verified at: {output_dir}")
except Exception as e:
    logger.error(f"Failed to create output directory: {e}")
    raise HTTPException(status_code=500, detail="Failed to create output directory")

async def store_zip_content(zip_file: UploadFile) -> str:
    """Store ZIP file content as base64 encoded string."""
    try:
        content = await zip_file.read()
        # Reset file pointer for potential reuse
        await zip_file.seek(0)
        return base64.b64encode(content).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to store ZIP content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store ZIP content: {str(e)}")

async def restore_zip_content(zip_content_b64: str, temp_dir: str) -> str:
    """Restore ZIP file from base64 content and extract it."""
    try:
        # Decode base64 content
        zip_content = base64.b64decode(zip_content_b64)
       
        # Ensure the temporary directory exists
        ensure_directory_exists(temp_dir)
        zip_path = os.path.join(temp_dir, "restored.zip")
       
        # Write ZIP content to file
        with open(zip_path, 'wb') as f:
            f.write(zip_content)
       
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
       
        # Remove the ZIP file after extraction
        os.remove(zip_path)
       
        # Find the root directory of the extracted content
        extracted_dirs = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        if len(extracted_dirs) == 1:
            return extracted_dirs[0]  # Use the single root directory if present
        return temp_dir  # Otherwise, use the temp_dir directly
    except Exception as e:
        logger.error(f"Failed to restore ZIP content: {str(e)}")
        await safe_remove_directory(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to restore ZIP content: {str(e)}")

async def extract_zip_file(zip_file: UploadFile, temp_dir: str) -> str:
    """Extract the uploaded ZIP file to a temporary directory and return the path."""
    try:
        # Ensure the temporary directory exists
        ensure_directory_exists(temp_dir)
        zip_path = os.path.join(temp_dir, "uploaded.zip")
       
        # Save the uploaded ZIP file
        async with aiofiles.open(zip_path, 'wb') as f:
            content = await zip_file.read()
            await f.write(content)
       
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
       
        # Remove the ZIP file after extraction
        os.remove(zip_path)
       
        # Find the root directory of the extracted content
        extracted_dirs = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        if len(extracted_dirs) == 1:
            return extracted_dirs[0]  # Use the single root directory if present
        return temp_dir  # Otherwise, use the temp_dir directly
    except Exception as e:
        logger.error(f"Failed to extract ZIP file: {str(e)}")
        await safe_remove_directory(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to extract ZIP file: {str(e)}")

@router.post("/register")
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password and create user
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = User(username=username, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/analyze", response_model=ResponseModel)
async def analyze_repository(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo_url: Optional[str] = Form(None),
    target_version: Literal["net6.0", "net7.0", "net8.0"] = Form("net8.0"),
    api_type: Literal["rest", "grpc"] = Form("rest"),
    instruction: Optional[str] = Form(None),
    source_type: Optional[Literal["git", "zip"]] = Form(None),
    zip_file: Optional[UploadFile] = File(None)
):
    temp_dir = None
    try:
        # Add debug logging
        logger.info(f"Received parameters: repo_url='{repo_url}', zip_file={zip_file.filename if zip_file else None}, source_type='{source_type}'")
       
        # Auto-detect source type if not provided
        if source_type is None:
            if repo_url and repo_url.strip():
                source_type = "git"
            elif zip_file:
                source_type = "zip"
            else:
                logger.error(f"No valid input provided. repo_url='{repo_url}', zip_file={zip_file}")
                raise HTTPException(status_code=400, detail="Either repository URL or ZIP file must be provided")
       
        # Validate input based on source_type
        if source_type == "git" and (not repo_url or not repo_url.strip()):
            raise HTTPException(status_code=400, detail="Repository URL is required for git source type")
        if source_type == "zip" and not zip_file:
            raise HTTPException(status_code=400, detail="ZIP file is required for zip source type")
        if source_type == "zip" and zip_file and not zip_file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Uploaded file must be a ZIP file")
       
        # Set up temporary directory
        temp_dir = tempfile.mkdtemp(prefix="migration_")
       
        # Store ZIP content if uploaded
        zip_content_b64 = None
        if source_type == "zip" and zip_file:
            zip_content_b64 = await store_zip_content(zip_file)
       
        # Handle source based on source_type
        if source_type == "git":
            temp_dir = await clone_repository(repo_url)
            logger.info(f"Repository cloned to: {temp_dir}")
        else:  # source_type == "zip"
            temp_dir = await extract_zip_file(zip_file, temp_dir)
            logger.info(f"ZIP file extracted to: {temp_dir}")
 
        # Create analyzer with local path
        analyzer = ProjectAnalyzer(temp_dir)
        basic_tree = await analyzer.create_basic_tree()
        analysis_tree = await analyzer.create_analyzed_tree()
 
        logger.info("Created analysis")
       
        default_instruction = f"Use the best of your knowledge to split into microservices considering the API type is {api_type}"
        instruction = instruction or default_instruction
               
        logger.info("Generating target structure")
 
        # Select the appropriate method based on api_type
        if api_type == "rest":
            target_structure = await analyzer.create_target_structure(
                analyzed_structure=analysis_tree,
                target_version=target_version,
                instruction=instruction
            )
        elif api_type == "grpc":
            target_structure = await analyzer.create_grpc_target_structure(
                analyzed_structure=analysis_tree,
                target_version=target_version,
                instruction=instruction
            )
        else:
            raise ValueError("Invalid api_type specified")
 
        target_structure = clear_empty_folders(target_structure)
        logger.info("Target structure generated and cleaned")
        with open('target.json', 'w') as f:
            f.write(json.dumps(target_structure, indent=4))
       
        # Create DB record
        analysis_data = {
            "repo_url": repo_url or "Uploaded ZIP",
            "target_version": target_version,
            "api_type": api_type,
            "basic_tree": basic_tree,
            "analysis_tree": analysis_tree,
            "zip_content": zip_content_b64
        }
       
        new_analysis = Analysis(
            repo_url=analysis_data["repo_url"],
            target_version=analysis_data["target_version"],
            api_type=analysis_data["api_type"],
            structure=analysis_data["basic_tree"],
            analysis=analysis_data["analysis_tree"],
            instruction=instruction,
            zip_content=analysis_data["zip_content"]
        )
       
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        logger.info("Analysis data saved to database")
       
        return ResponseModel(
            status="success",
            data={
                "analysis_id": new_analysis.id,
                "repo_url": repo_url or "Uploaded ZIP",
                "target_version": target_version,
                "api_type": api_type,
                "structure": basic_tree,
                "target_structure": target_structure
            }
        )
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_dir and os.path.exists(temp_dir):
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            await safe_remove_directory(temp_dir)
            logger.info("Cleanup completed")
        if db:
            db.close()

@router.post("/migrate", response_model=None)
async def migrate_repository(
    request: MigrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temp_dir = None
    try:
        # Get analysis from DB
        analysis = db.query(Analysis).filter(Analysis.id == request.analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis with id {request.analysis_id} not found")
 
        if not isinstance(request.target_structure, dict) or 'microservices' not in request.target_structure:
            raise HTTPException(status_code=400, detail="Invalid target structure format. Expected key 'microservices' not found.")
 
        # Get instruction: prefer request.instruction, fall back to analysis.instruction
        instruction = request.instruction
        if not instruction and hasattr(analysis, 'instruction'):
            instruction = analysis.instruction
        if not instruction:
            logger.warning("No instruction provided; using default")
            instruction = "split into microservices"
 
        # Determine source type from analysis
        repo_url = analysis.repo_url
        is_zip = repo_url == "Uploaded ZIP"
       
        # Set up temporary directory
        temp_dir = tempfile.mkdtemp(prefix="migration_")
       
        # Handle source based on whether it was originally a ZIP or git
        if not is_zip:
            temp_dir = await clone_repository(repo_url)
            logger.info(f"Repository cloned to: {temp_dir}")
        else:
            # For ZIP-based projects, restore from stored content
            if not hasattr(analysis, 'zip_content') or not analysis.zip_content:
                raise HTTPException(status_code=400, detail="ZIP content not found in analysis. Please re-upload the ZIP file.")
           
            temp_dir = await restore_zip_content(analysis.zip_content, temp_dir)
            logger.info(f"ZIP content restored to: {temp_dir}")
 
        # Instantiate Migrator and initialize output and source directories
        migration_service = Migrator()
        await migration_service.initialize(output_dir=output_dir, source_dir=temp_dir)
 
        with open('request.json', 'w') as f:
            f.write(json.dumps(request.target_structure, indent=4))
 
        # Initialize the shared RAG services using the provided JSON data
        rag_initialized = migration_service.rag_service.initialize(
            json_data=request.target_structure,
            temp_dir=temp_dir,
            force_rebuild=True
        )
        if not rag_initialized:
            raise HTTPException(status_code=500, detail="Failed to initialize target structure RAG service")
        logger.info("Target structure RAG service initialized successfully")
       
        analysis_initialized = migration_service.analysis_rag_service.initialize(
            json_data=analysis.analysis,
            temp_dir=temp_dir,
            force_rebuild=True
        )
        if not analysis_initialized:
            raise HTTPException(status_code=500, detail="Failed to initialize analysis RAG service")
        logger.info("Analysis RAG service initialized successfully")
 
        repo_name = repo_url.split('/')[-1].replace('.git', '') if not is_zip else "migrated_project"
        api_type = getattr(analysis, "api_type", "rest") or "rest"
       
        # Select processing method based on api_type
        if api_type == "rest":
            migration_result = await migration_service.process_and_zip_projects(
                target_structure=request.target_structure,
                target_version=analysis.target_version,
                repo_name=repo_name
            )
        elif api_type == "grpc":
            migration_result = await migration_service.process_and_zip_projects_grpc(
                target_structure=request.target_structure,
                target_version=analysis.target_version,
                repo_name=repo_name
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid api_type specified")
 
        zip_file_path = migration_result.get("zip_file")
        if not os.path.exists(zip_file_path):
            raise HTTPException(status_code=500, detail="Zip file not found")
 
        # Return the zip file as a download
        return FileResponse(
            zip_file_path,
            media_type="application/zip",
            filename=f"{repo_name}.zip"
        )
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_dir and os.path.exists(temp_dir):
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            await safe_remove_directory(temp_dir)
            logger.info("Cleanup completed")

@router.post("/regenerate", response_model=ResponseModel)
async def regenerate_structure(
    request: RegenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Fetch and validate analysis
        analysis = db.query(Analysis).filter(Analysis.id == request.analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis with id {request.analysis_id} not found")
 
        # Validate target structure
        if not isinstance(request.target_structure, dict) or 'projects' not in request.target_structure:
            raise HTTPException(status_code=400, detail="Invalid target structure format")
 
        # Initialize analyzer with proper settings
        analyzer = ProjectAnalyzer(project_path=analysis.repo_url)
 
        # Generate new structure
        new_structure = await analyzer.regenerate_target_structure(
            analysis_tree=analysis.analysis,
            current_target=request.target_structure,
            comments=request.comments
        )
 
        if not new_structure or 'projects' not in new_structure:
            raise HTTPException(status_code=500, detail="Failed to generate valid target structure")
 
        return ResponseModel(
            status="success",
            data={
                "analysis_id": request.analysis_id,
                "target_structure": new_structure,
                "original_version": analysis.target_version
            }
        )
    except Exception as e:
        logger.error(f"Regeneration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend", response_model=ResponseModel)
async def recommend_file(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        prompt = f"Analyze this file and provide a brief description and file type recommendation:\n\nfile_name: {request.file_name}"
        analysis = await file_recommendation_agent.run(
            user_prompt=prompt,
            model_settings={'temperature': 0.2}
        )
 
        logger.info(f"Recommendation generated: {analysis.data}")
       
        if not analysis:
            recommendation = {
                "description": "No analysis available for this file.",
                "file_type": "unknown"
            }
        else:
            recommendation = {
                "description": analysis.data.description,
                "file_type": analysis.data.file_type
            }
           
        return ResponseModel(
            status="success",
            data=recommendation
        )
    except Exception as e:
        logger.error(f"Recommendation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))