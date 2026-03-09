"""Detector for Kubernetes manifests (*.yaml with kind: Deployment, Service, etc.)."""

import re
from pathlib import Path

import yaml

from ..models import TechCategory, TechnologyDetection

# Kubernetes kinds that suggest architecture roles
KIND_ROLES = {
    "Deployment": TechCategory.BACKEND,
    "StatefulSet": TechCategory.BACKEND,
    "DaemonSet": TechCategory.BACKEND,
    "Service": TechCategory.BACKEND,
    "Ingress": TechCategory.REVERSE_PROXY,
    "CronJob": TechCategory.WORKER,
    "Job": TechCategory.WORKER,
}

# Image name patterns
IMAGE_PATTERNS = {
    "postgres": ("PostgreSQL", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "mongo": ("MongoDB", TechCategory.DATABASE),
    "redis": ("Redis", TechCategory.CACHE),
    "nginx": ("Nginx", TechCategory.REVERSE_PROXY),
    "rabbitmq": ("RabbitMQ", TechCategory.QUEUE),
    "kafka": ("Kafka", TechCategory.QUEUE),
    "elasticsearch": ("Elasticsearch", TechCategory.DATABASE),
}


def detect_from_kubernetes(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect architecture from Kubernetes YAML manifests.
    
    Args:
        file_path: Path to a .yaml or .yml file
        
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
    
    # Handle multi-document YAML
    docs = []
    try:
        for doc in yaml.safe_load_all(content):
            if doc:
                docs.append(doc)
    except yaml.YAMLError:
        # Fallback: look for kind: in raw content
        if re.search(r"^\s*kind:\s*\w+", content, re.MULTILINE | re.IGNORECASE):
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="Kubernetes",
                    category=TechCategory.CONTAINER,
                    confidence=0.8,
                    details="Kubernetes manifest (YAML parse skipped)",
                )
            )
        return detections
    
    for data in docs:
        if not isinstance(data, dict):
            continue
        
        kind = data.get("kind", "")
        if kind:
            role = KIND_ROLES.get(kind)
            if role:
                name = data.get("metadata", {}).get("name", kind)
                detections.append(
                    TechnologyDetection(
                        source_file=source,
                        tech=f"K8s {kind}",
                        category=role,
                        confidence=0.8,
                        details=f"Kubernetes {kind}: {name}",
                    )
                )
        
        # Check container images
        spec = data.get("spec", {})
        if isinstance(spec, dict):
            containers = spec.get("containers", spec.get("template", {}).get("spec", {}).get("containers", []))
            if not isinstance(containers, list):
                containers = []
            for cont in containers:
                if isinstance(cont, dict):
                    image = cont.get("image", "")
                    if image:
                        image_lower = image.lower()
                        for pattern, (tech_name, category) in IMAGE_PATTERNS.items():
                            if pattern in image_lower:
                                detections.append(
                                    TechnologyDetection(
                                        source_file=source,
                                        tech=tech_name,
                                        category=category,
                                        confidence=0.9,
                                        details=f"K8s container image: {image}",
                                    )
                                )
                                break
    
    if docs and "Kubernetes" not in {d.tech for d in detections}:
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="Kubernetes",
                category=TechCategory.CONTAINER,
                confidence=0.85,
                details="Kubernetes manifest detected",
            )
        )
    
    return detections
