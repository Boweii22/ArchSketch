"""Detector for Procfile (Heroku-style process types)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Process type -> architecture role
PROCESS_ROLES = {
    "web": TechCategory.BACKEND,      # or FRONTEND if static; default backend
    "worker": TechCategory.WORKER,
    "worker:": TechCategory.WORKER,
    "clock": TechCategory.WORKER,
    "clock:": TechCategory.WORKER,
    "scheduler": TechCategory.WORKER,
    "release": TechCategory.BACKEND,
    "api": TechCategory.BACKEND,
}

# Command hints -> technology
COMMAND_HINTS = {
    "gunicorn": ("Gunicorn", TechCategory.BACKEND),
    "uvicorn": ("FastAPI/Starlette", TechCategory.BACKEND),
    "celery": ("Celery", TechCategory.WORKER),
    "node": ("Node.js", TechCategory.BACKEND),
    "npm": ("Node.js", TechCategory.BACKEND),
    "yarn": ("Node.js", TechCategory.BACKEND),
    "next": ("Next.js", TechCategory.FRONTEND),
    "nuxt": ("Nuxt.js", TechCategory.FRONTEND),
    "python": ("Python", TechCategory.BACKEND),
    "java": ("Java", TechCategory.BACKEND),
    "rails": ("Rails", TechCategory.BACKEND),
    "puma": ("Rails/Puma", TechCategory.BACKEND),
    "sidekiq": ("Sidekiq", TechCategory.WORKER),
}


def detect_from_procfile(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect architecture from a Procfile (process type: command).
    
    Args:
        file_path: Path to the Procfile
        
    Returns:
        List of detected technologies
    """
    detections: list[TechnologyDetection] = []
    source = str(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        # Format: process_type: command
        if ":" not in line:
            continue
        
        proc_type, _, command = line.partition(":")
        proc_type = proc_type.strip().lower()
        command = command.strip()
        
        # Map process type to role
        role = PROCESS_ROLES.get(proc_type) or PROCESS_ROLES.get(proc_type + ":")
        if role:
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech=f"Procfile {proc_type}",
                    category=role,
                    confidence=0.85,
                    details=f"Procfile process type '{proc_type}': {command[:50]}",
                )
            )
        
        # Infer tech from command
        command_lower = command.lower()
        for hint, (tech_name, category) in COMMAND_HINTS.items():
            if hint in command_lower:
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.75,
                        details=f"Procfile command uses '{hint}'",
                    )
                )
                break
    
    return detections
