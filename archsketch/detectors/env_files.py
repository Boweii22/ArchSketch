"""Detector for .env files."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Environment variable patterns that indicate technologies
ENV_PATTERNS = {
    # Database connections
    "DATABASE_URL": TechCategory.DATABASE,
    "DB_HOST": TechCategory.DATABASE,
    "DB_CONNECTION": TechCategory.DATABASE,
    "POSTGRES": TechCategory.DATABASE,
    "MYSQL": TechCategory.DATABASE,
    "MONGO": TechCategory.DATABASE,
    
    # Cache
    "REDIS_URL": TechCategory.CACHE,
    "REDIS_HOST": TechCategory.CACHE,
    "CACHE_URL": TechCategory.CACHE,
    "MEMCACHED": TechCategory.CACHE,
    
    # Queue
    "CELERY": TechCategory.WORKER,
    "RABBITMQ": TechCategory.QUEUE,
    "AMQP": TechCategory.QUEUE,
    "KAFKA": TechCategory.QUEUE,
    
    # API/Backend
    "API_URL": TechCategory.BACKEND,
    "BACKEND_URL": TechCategory.BACKEND,
    
    # Frontend
    "NEXT_PUBLIC": TechCategory.FRONTEND,
    "REACT_APP": TechCategory.FRONTEND,
    "VUE_APP": TechCategory.FRONTEND,
    "NUXT": TechCategory.FRONTEND,
}

# Value patterns that reveal specific technologies
VALUE_PATTERNS = {
    "postgresql": ("PostgreSQL", TechCategory.DATABASE),
    "postgres": ("PostgreSQL", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "mongodb": ("MongoDB", TechCategory.DATABASE),
    "redis": ("Redis", TechCategory.CACHE),
    "amqp": ("RabbitMQ", TechCategory.QUEUE),
    "rabbitmq": ("RabbitMQ", TechCategory.QUEUE),
}


def detect_from_env_files(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from .env files.
    
    Args:
        file_path: Path to the .env file
        
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
    
    for line in content.splitlines():
        line = line.strip()
        
        if not line or line.startswith("#"):
            continue
        
        # Parse KEY=VALUE
        if "=" not in line:
            continue
        
        key, _, value = line.partition("=")
        key = key.strip().upper()
        value = value.strip().lower()
        
        # Check key patterns
        for pattern, category in ENV_PATTERNS.items():
            if pattern in key:
                # Check value for specific technology
                for val_pattern, (tech_name, tech_category) in VALUE_PATTERNS.items():
                    if val_pattern in value and tech_name not in detected_techs:
                        detected_techs.add(tech_name)
                        detections.append(
                            TechnologyDetection(
                                source_file=source,
                                tech=tech_name,
                                category=tech_category,
                                confidence=0.8,
                                details=f"Environment variable {key} contains {val_pattern}",
                            )
                        )
                        break
                break
        
        # Check values directly for technology hints
        for val_pattern, (tech_name, category) in VALUE_PATTERNS.items():
            if val_pattern in value and tech_name not in detected_techs:
                detected_techs.add(tech_name)
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.7,
                        details=f"Found '{val_pattern}' in environment value",
                    )
                )
    
    return detections
