"""Detector for Dockerfile files."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Base image patterns
BASE_IMAGE_PATTERNS = {
    "node": ("Node.js", TechCategory.BACKEND),
    "python": ("Python", TechCategory.BACKEND),
    "golang": ("Go", TechCategory.BACKEND),
    "rust": ("Rust", TechCategory.BACKEND),
    "openjdk": ("Java", TechCategory.BACKEND),
    "ruby": ("Ruby", TechCategory.BACKEND),
    "php": ("PHP", TechCategory.BACKEND),
    "dotnet": (".NET", TechCategory.BACKEND),
    "nginx": ("Nginx", TechCategory.REVERSE_PROXY),
}

# Command patterns that indicate technologies
COMMAND_PATTERNS = {
    "npm": ("Node.js", TechCategory.BACKEND),
    "yarn": ("Node.js", TechCategory.BACKEND),
    "pnpm": ("Node.js", TechCategory.BACKEND),
    "pip": ("Python", TechCategory.BACKEND),
    "poetry": ("Python", TechCategory.BACKEND),
    "cargo": ("Rust", TechCategory.BACKEND),
    "go build": ("Go", TechCategory.BACKEND),
    "mvn": ("Maven/Java", TechCategory.BACKEND),
    "gradle": ("Gradle/Java", TechCategory.BACKEND),
}


def detect_from_dockerfile(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from a Dockerfile.
    
    Args:
        file_path: Path to the Dockerfile
        
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
    
    detected_techs: set[str] = set()
    
    # Parse FROM instructions
    from_pattern = re.compile(r"^FROM\s+(\S+)", re.MULTILINE | re.IGNORECASE)
    for match in from_pattern.finditer(content):
        image = match.group(1).lower()
        
        for pattern, (tech_name, category) in BASE_IMAGE_PATTERNS.items():
            if pattern in image:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(
                        TechnologyDetection(
                            source_file=source,
                            tech=tech_name,
                            category=category,
                            confidence=0.85,
                            details=f"Base image: {match.group(1)}",
                        )
                    )
                break
    
    # Check RUN commands for technology hints
    content_lower = content.lower()
    for pattern, (tech_name, category) in COMMAND_PATTERNS.items():
        if pattern in content_lower and tech_name not in detected_techs:
            detected_techs.add(tech_name)
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech=tech_name,
                    category=category,
                    confidence=0.7,
                    details=f"Found '{pattern}' command in Dockerfile",
                )
            )
    
    # Check for framework-specific files being copied
    if "next.config" in content_lower and "Next.js" not in detected_techs:
        detected_techs.add("Next.js")
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="Next.js",
                category=TechCategory.FRONTEND,
                confidence=0.8,
                details="next.config file referenced in Dockerfile",
            )
        )
    
    # Detect container role (always add this as it's useful)
    detections.append(
        TechnologyDetection(
            source_file=source,
            tech="Docker",
            category=TechCategory.CONTAINER,
            confidence=1.0,
            details="Dockerfile present",
        )
    )
    
    return detections
