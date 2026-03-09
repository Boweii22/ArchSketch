"""Detector for docker-compose.yml files."""

import re
from pathlib import Path

import yaml

from ..models import TechCategory, TechnologyDetection

# Image patterns to detect
IMAGE_PATTERNS = {
    # Databases
    "postgres": ("PostgreSQL", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "mariadb": ("MariaDB", TechCategory.DATABASE),
    "mongo": ("MongoDB", TechCategory.DATABASE),
    "redis": ("Redis", TechCategory.CACHE),
    "memcached": ("Memcached", TechCategory.CACHE),
    
    # Message queues
    "rabbitmq": ("RabbitMQ", TechCategory.QUEUE),
    "kafka": ("Kafka", TechCategory.QUEUE),
    "nats": ("NATS", TechCategory.QUEUE),
    
    # Web servers / Reverse proxies
    "nginx": ("Nginx", TechCategory.REVERSE_PROXY),
    "traefik": ("Traefik", TechCategory.REVERSE_PROXY),
    "caddy": ("Caddy", TechCategory.REVERSE_PROXY),
    "haproxy": ("HAProxy", TechCategory.REVERSE_PROXY),
    
    # Search
    "elasticsearch": ("Elasticsearch", TechCategory.DATABASE),
    "opensearch": ("OpenSearch", TechCategory.DATABASE),
    "meilisearch": ("Meilisearch", TechCategory.DATABASE),
}

# Service name patterns
SERVICE_NAME_PATTERNS = {
    "frontend": TechCategory.FRONTEND,
    "web": TechCategory.FRONTEND,
    "client": TechCategory.FRONTEND,
    "ui": TechCategory.FRONTEND,
    "backend": TechCategory.BACKEND,
    "api": TechCategory.BACKEND,
    "server": TechCategory.BACKEND,
    "app": TechCategory.BACKEND,
    "worker": TechCategory.WORKER,
    "celery": TechCategory.WORKER,
    "queue": TechCategory.QUEUE,
    "db": TechCategory.DATABASE,
    "database": TechCategory.DATABASE,
    "cache": TechCategory.CACHE,
    "proxy": TechCategory.REVERSE_PROXY,
    "nginx": TechCategory.REVERSE_PROXY,
}


def detect_from_docker_compose(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from a docker-compose.yml file.
    
    Args:
        file_path: Path to the docker-compose file
        
    Returns:
        List of detected technologies
    """
    detections: list[TechnologyDetection] = []
    source = str(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return detections
    
    if not isinstance(data, dict):
        return detections
    
    services = data.get("services", {})
    if not isinstance(services, dict):
        return detections
    
    detected_techs: set[str] = set()
    
    for service_name, service_config in services.items():
        if not isinstance(service_config, dict):
            continue
        
        # Check image field
        image = service_config.get("image", "")
        if image:
            image_lower = image.lower()
            for pattern, (tech_name, category) in IMAGE_PATTERNS.items():
                if pattern in image_lower:
                    if tech_name not in detected_techs:
                        detected_techs.add(tech_name)
                        detections.append(
                            TechnologyDetection(
                                source_file=source,
                                tech=tech_name,
                                category=category,
                                confidence=0.95,
                                details=f"Docker service '{service_name}' uses image '{image}'",
                            )
                        )
                    break
        
        # Check service name for role hints
        service_lower = service_name.lower()
        for pattern, category in SERVICE_NAME_PATTERNS.items():
            if pattern in service_lower:
                # Create a detection based on service name
                role_name = f"{service_name} (Docker)"
                if role_name not in detected_techs:
                    detected_techs.add(role_name)
                    detections.append(
                        TechnologyDetection(
                            source_file=source,
                            tech=service_name,
                            category=category,
                            confidence=0.6,
                            details=f"Service name '{service_name}' suggests {category.value}",
                        )
                    )
                break
        
        # Check for build context (indicates custom app)
        build = service_config.get("build")
        if build:
            context = build if isinstance(build, str) else build.get("context", "")
            if context and service_name not in detected_techs:
                # Determine likely category from service name
                category = TechCategory.BACKEND
                for pattern, cat in SERVICE_NAME_PATTERNS.items():
                    if pattern in service_lower:
                        category = cat
                        break
                
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech=f"{service_name} (custom)",
                        category=category,
                        confidence=0.5,
                        details=f"Docker service '{service_name}' has build context",
                    )
                )
        
        # Check depends_on for relationships (useful for inference later)
        depends_on = service_config.get("depends_on", [])
        if isinstance(depends_on, dict):
            depends_on = list(depends_on.keys())
        
        # Environment variables can reveal database connections
        environment = service_config.get("environment", {})
        if isinstance(environment, dict):
            env_str = str(environment).lower()
            if "postgres" in env_str and "PostgreSQL" not in detected_techs:
                detected_techs.add("PostgreSQL")
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech="PostgreSQL",
                        category=TechCategory.DATABASE,
                        confidence=0.7,
                        details=f"PostgreSQL config in '{service_name}' environment",
                    )
                )
            if "mysql" in env_str and "MySQL" not in detected_techs:
                detected_techs.add("MySQL")
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech="MySQL",
                        category=TechCategory.DATABASE,
                        confidence=0.7,
                        details=f"MySQL config in '{service_name}' environment",
                    )
                )
            if "redis" in env_str and "Redis" not in detected_techs:
                detected_techs.add("Redis")
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech="Redis",
                        category=TechCategory.CACHE,
                        confidence=0.7,
                        details=f"Redis config in '{service_name}' environment",
                    )
                )
    
    return detections
