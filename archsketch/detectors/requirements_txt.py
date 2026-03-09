"""Detector for requirements.txt and pyproject.toml files (Python projects)."""

import re
from pathlib import Path
from typing import Optional

from ..models import TechCategory, TechnologyDetection

# Technology patterns for Python packages
TECH_PATTERNS = {
    # Backend frameworks
    "fastapi": ("FastAPI", TechCategory.BACKEND),
    "flask": ("Flask", TechCategory.BACKEND),
    "django": ("Django", TechCategory.BACKEND),
    "starlette": ("Starlette", TechCategory.BACKEND),
    "tornado": ("Tornado", TechCategory.BACKEND),
    "sanic": ("Sanic", TechCategory.BACKEND),
    "aiohttp": ("aiohttp", TechCategory.BACKEND),
    
    # Database clients
    "psycopg2": ("PostgreSQL", TechCategory.DATABASE),
    "psycopg": ("PostgreSQL", TechCategory.DATABASE),
    "asyncpg": ("PostgreSQL", TechCategory.DATABASE),
    "mysqlclient": ("MySQL", TechCategory.DATABASE),
    "pymysql": ("MySQL", TechCategory.DATABASE),
    "aiomysql": ("MySQL", TechCategory.DATABASE),
    "pymongo": ("MongoDB", TechCategory.DATABASE),
    "motor": ("MongoDB", TechCategory.DATABASE),
    "sqlalchemy": ("SQLAlchemy", TechCategory.DATABASE),
    "sqlmodel": ("SQLModel", TechCategory.DATABASE),
    "tortoise-orm": ("Tortoise ORM", TechCategory.DATABASE),
    "peewee": ("Peewee", TechCategory.DATABASE),
    
    # Cache
    "redis": ("Redis", TechCategory.CACHE),
    "aioredis": ("Redis", TechCategory.CACHE),
    "python-memcached": ("Memcached", TechCategory.CACHE),
    "pymemcache": ("Memcached", TechCategory.CACHE),
    
    # Worker/Queue
    "celery": ("Celery", TechCategory.WORKER),
    "rq": ("RQ", TechCategory.WORKER),
    "dramatiq": ("Dramatiq", TechCategory.WORKER),
    "huey": ("Huey", TechCategory.WORKER),
    
    # Queue backends
    "kombu": ("Kombu", TechCategory.QUEUE),
    "pika": ("RabbitMQ", TechCategory.QUEUE),
}


def parse_requirement_line(line: str) -> Optional[str]:
    """Extract package name from a requirements.txt line."""
    line = line.strip()
    
    if not line or line.startswith("#") or line.startswith("-"):
        return None
    
    # Remove version specifiers and extras
    match = re.match(r"^([a-zA-Z0-9_-]+)", line)
    if match:
        return match.group(1).lower()
    
    return None


def detect_from_requirements(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from requirements.txt or pyproject.toml.
    
    Args:
        file_path: Path to the requirements file
        
    Returns:
        List of detected technologies
    """
    detections: list[TechnologyDetection] = []
    source = str(file_path)
    filename = file_path.name.lower()
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections
    
    packages: set[str] = set()
    
    if filename == "requirements.txt" or filename.endswith(".txt"):
        # Parse requirements.txt format
        for line in content.splitlines():
            pkg = parse_requirement_line(line)
            if pkg:
                packages.add(pkg)
    
    elif filename == "pyproject.toml":
        # Simple extraction from pyproject.toml - look for dependency patterns
        # This is a simplified parser; a full TOML parser would be more robust
        dep_section = False
        for line in content.splitlines():
            line_lower = line.lower().strip()
            
            if "dependencies" in line_lower and "=" in line:
                dep_section = True
                continue
            
            if dep_section:
                if line.strip().startswith("]"):
                    dep_section = False
                    continue
                
                # Extract package name from quoted string
                match = re.search(r'"([a-zA-Z0-9_-]+)', line)
                if match:
                    packages.add(match.group(1).lower())
    
    elif filename == "pipfile":
        # Simple Pipfile parsing
        for line in content.splitlines():
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*=', line.strip())
            if match:
                packages.add(match.group(1).lower())
    
    # Match packages to technologies
    detected_techs: set[str] = set()
    
    for pkg in packages:
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in pkg or pkg == pattern:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(
                        TechnologyDetection(
                            source_file=source,
                            tech=tech_name,
                            category=category,
                            confidence=0.9,
                            details=f"Found '{pkg}' in {filename}",
                        )
                    )
    
    return detections
