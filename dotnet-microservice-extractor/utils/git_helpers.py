import tempfile
import os
from git import Repo, GitCommandError

async def clone_repository(repo_url: str) -> str:
    """Clone a git repository to a temporary directory and return the path."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="migration_")
    
    try:
        # Clone the repository
        Repo.clone_from(repo_url, temp_dir)
        return temp_dir
    except GitCommandError as e:
        # Clean up the temporary directory if cloning fails
        os.rmdir(temp_dir)
        raise Exception(f"Failed to clone repository: {str(e)}")
    except Exception as e:
        # Clean up the temporary directory if any other error occurs
        os.rmdir(temp_dir)
        raise Exception(f"An unexpected error occurred: {str(e)}")