import os
import aiofiles
import yaml
from typing import Dict, Optional
import shutil 
from utils import logger
import stat
from pathlib import Path

def join_paths(*paths: str) -> str:
    """
    Join paths using OS-specific separators and normalize slashes.
    
    Args:
        *paths: Path components to join
        
    Returns:
        Normalized path string using OS-specific separators
    """
    # Convert forward slashes to backslashes on Windows
    joined_path = os.path.join(*[p.replace('/', os.sep) for p in paths])
    # Normalize path
    return os.path.normpath(joined_path)

async def read_file(file_path: str) -> Optional[str]:
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: Source file not found: {file_path}")
            
            # Get parent directory
            parent_dir = path.parent
            print(f"Parent directory: {parent_dir}")
            if parent_dir.exists():
                # List only files in the specific directory
                files = [f.name for f in parent_dir.glob('*') if f.is_file()]
                if files:
                    print(f"\nFiles in {parent_dir}:")
                    for file in sorted(files):
                        print(f"  {file}")
            return None
            
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return await f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None
        

# async def load_yaml_file() -> Optional[Dict]:
#     """Load and parse a YAML file asynchronously."""
#     try:
#         # Get directory containing the current script
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         yaml_path = os.path.join(current_dir, "prompts.yml")
        
#         async with aiofiles.open(yaml_path, 'r') as f:
#             content = await f.read()
#             return yaml.safe_load(content)
#     except Exception as e:
#         print(f"Failed to load YAML file : {str(e)}")
#         return None

async def load_yaml_file() -> Optional[Dict]:
    """Load and parse a YAML file asynchronously."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, "prompts.yml")
        print(f"Loading YAML file from: {yaml_path}")  # <-- Add this
        async with aiofiles.open(yaml_path, 'r') as f:
            content = await f.read()
            parsed = yaml.safe_load(content)
            if not parsed:
                print("Warning: prompts.yml loaded but is empty or invalid.")
            else:
                print("YAML loaded successfully.")  # <-- Optional debug
            return parsed
    except Exception as e:
        print(f"Failed to load YAML file : {str(e)}")
        return None


def ensure_directory_exists(path: str) -> None:
    """Create a directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def sanitize_content(content: str) -> str:
    """
    Remove markdown code block indicators and language specifiers from generated content.
    
    Args:
        content: Raw generated content
        
    Returns:
        Sanitized content string
    """
    # Remove markdown code block indicators and language specifiers
    code_block_markers = [
        "```csharp", "```json", "```xml", "```cs", "```",
        "'''csharp", "'''json", "'''xml", "'''cs", "'''"
    ]
    
    result = content
    for marker in code_block_markers:
        result = result.replace(marker, "")
    
    return result.strip()


async def safe_remove_directory(path: str) -> bool:
    """
    Safely remove a directory and its contents asynchronously.
    Returns True if successful, False otherwise.
    """
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return True

        # First try to make all files writable
        for item in path_obj.rglob("*"):
            if item.is_file():
                item.chmod(0o666)

        # Remove files first
        for item in path_obj.rglob("*"):
            if item.is_file():
                try:
                    item.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to remove file {item}: {e}")

        # Remove directories bottom-up
        for item in sorted(path_obj.rglob("*"), key=lambda x: len(str(x.absolute())), reverse=True):
            if item.is_dir():
                try:
                    item.rmdir()
                except Exception as e:
                    logger.warning(f"Failed to remove directory {item}: {e}")

        # Remove the root directory
        try:
            path_obj.rmdir()
        except Exception as e:
            logger.warning(f"Failed to remove root directory {path}: {e}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error during directory removal: {e}")
        return False
    


def copy_static_files_to_wwwroot(source_dir: str, project_dir: str) -> None:
    """
    Copy all .css and .js files from anywhere in the source_dir
    into the wwwroot subfolders of the project_dir.
    All files are flattened; duplicate file names are skipped.
    """
    wwwroot_dir = join_paths(project_dir, "wwwroot")
    content_dir = join_paths(wwwroot_dir, "content")
    js_dir = join_paths(wwwroot_dir, "scripts")
    ensure_directory_exists(content_dir)
    ensure_directory_exists(js_dir)
    
    for root, dirs, files in os.walk(source_dir):
        # Optionally skip wwwroot folder if it exists in the source repo
        if "wwwroot" in dirs:
            dirs.remove("wwwroot")
        for file in files:
            lower_file = file.lower()
            source_file = join_paths(root, file)
            if lower_file.endswith(".css"):
                target_file = join_paths(content_dir, file)
                if not os.path.exists(target_file):
                    shutil.copy2(source_file, target_file)
            elif lower_file.endswith(".js"):
                target_file = join_paths(js_dir, file)
                if not os.path.exists(target_file):
                    shutil.copy2(source_file, target_file)


def clear_empty_folders(target_structure: dict) -> dict:
    """
    Recursively remove folders that do not contain any files.
    A folder is considered empty if both its "target_files" (list or dict)
    is empty and it has no non‑empty subfolders.
    """
    import copy
    cleaned_structure = copy.deepcopy(target_structure)

    def clean_folder(folder: dict) -> dict | None:
        # Get and clean subfolders
        subfolders = folder.get("subfolders", {})
        new_subfolders = {}
        for name, sub in subfolders.items():
            cleaned_sub = clean_folder(sub)
            if cleaned_sub is not None:
                new_subfolders[name] = cleaned_sub

        # Determine if current folder has files:
        target_files = folder.get("target_files")
        has_files = False
        if target_files is not None:
            if isinstance(target_files, dict):
                has_files = len(target_files) > 0
            elif isinstance(target_files, list):
                has_files = len(target_files) > 0

        # Folder is empty if there are no files and no subfolders with files.
        if not has_files and len(new_subfolders) == 0:
            return None

        folder["subfolders"] = new_subfolders
        return folder

    folders = cleaned_structure.get("folders", {})
    new_folders = {}
    for folder_name, folder in folders.items():
        cleaned = clean_folder(folder)
        if cleaned is not None:
            new_folders[folder_name] = cleaned
    cleaned_structure["folders"] = new_folders

    return cleaned_structure
