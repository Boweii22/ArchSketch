"""File scanner for discovering architecture-related files."""

import os
from dataclasses import dataclass, field
from pathlib import Path


# Files that reveal architecture information
IMPORTANT_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "Dockerfile",
    ".env",
    ".env.example",
    ".env.local",
    "nginx.conf",
    "Procfile",
    "Makefile",
}

# Directories to skip during scanning
SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "eggs",
    "*.egg-info",
}


@dataclass
class ScanResult:
    """Result of scanning a project directory."""
    root_path: Path
    files: dict[str, list[Path]] = field(default_factory=dict)
    
    def get_files(self, filename: str) -> list[Path]:
        """Get all found files matching a filename."""
        return self.files.get(filename, [])
    
    def has_file(self, filename: str) -> bool:
        """Check if a file type was found."""
        return filename in self.files and len(self.files[filename]) > 0
    
    def all_files(self) -> list[Path]:
        """Get all discovered files as a flat list."""
        result = []
        for file_list in self.files.values():
            result.extend(file_list)
        return result
    
    def summary(self) -> dict[str, int]:
        """Get a summary of files found by type."""
        return {name: len(paths) for name, paths in self.files.items()}


def should_skip_dir(dirname: str) -> bool:
    """Check if a directory should be skipped."""
    if dirname.startswith("."):
        return True
    if dirname in SKIP_DIRS:
        return True
    if dirname.endswith(".egg-info"):
        return True
    return False


def scan_directory(path: str | Path) -> ScanResult:
    """
    Scan a directory for architecture-related files.
    
    Args:
        path: Root directory to scan
        
    Returns:
        ScanResult containing all discovered important files
    """
    root = Path(path).resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    
    result = ScanResult(root_path=root)
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out directories we should skip (modifies in-place)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        
        for filename in filenames:
            # Check for exact matches
            if filename in IMPORTANT_FILES:
                full_path = Path(dirpath) / filename
                if filename not in result.files:
                    result.files[filename] = []
                result.files[filename].append(full_path)
            
            # Check for Dockerfile variants (Dockerfile.prod, Dockerfile.dev, etc.)
            elif filename.startswith("Dockerfile"):
                full_path = Path(dirpath) / filename
                if "Dockerfile" not in result.files:
                    result.files["Dockerfile"] = []
                result.files["Dockerfile"].append(full_path)
            
            # Check for docker-compose variants
            elif filename.startswith("docker-compose") and filename.endswith((".yml", ".yaml")):
                full_path = Path(dirpath) / filename
                key = "docker-compose.yml"
                if key not in result.files:
                    result.files[key] = []
                result.files[key].append(full_path)
            
            # Check for .env variants
            elif filename.startswith(".env"):
                full_path = Path(dirpath) / filename
                if ".env" not in result.files:
                    result.files[".env"] = []
                result.files[".env"].append(full_path)
    
    return result
