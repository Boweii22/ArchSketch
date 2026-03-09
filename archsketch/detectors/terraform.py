"""Detector for Terraform files (*.tf)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Resource/provider patterns -> label and category
RESOURCE_PATTERNS = {
    # Cloud DB / storage
    "aws_rds": ("AWS RDS", TechCategory.DATABASE),
    "aws_dynamodb": ("AWS DynamoDB", TechCategory.DATABASE),
    "aws_elasticache": ("AWS ElastiCache", TechCategory.CACHE),
    "google_sql": ("Google Cloud SQL", TechCategory.DATABASE),
    "azurerm_mysql": ("Azure MySQL", TechCategory.DATABASE),
    "azurerm_postgresql": ("Azure PostgreSQL", TechCategory.DATABASE),
    "azurerm_redis": ("Azure Redis", TechCategory.CACHE),
    
    # Compute / runtime
    "aws_lambda": ("AWS Lambda", TechCategory.BACKEND),
    "aws_ecs": ("AWS ECS", TechCategory.CONTAINER),
    "aws_eks": ("AWS EKS", TechCategory.CONTAINER),
    "google_cloud_run": ("Google Cloud Run", TechCategory.BACKEND),
    "azurerm_container_group": ("Azure Container", TechCategory.CONTAINER),
    
    # Load balancing / proxy
    "aws_lb": ("AWS ALB/NLB", TechCategory.REVERSE_PROXY),
    "aws_alb": ("AWS ALB", TechCategory.REVERSE_PROXY),
    "google_compute_backend": ("GCP Backend", TechCategory.REVERSE_PROXY),
    
    # Message queue
    "aws_sqs": ("AWS SQS", TechCategory.QUEUE),
    "aws_sns": ("AWS SNS", TechCategory.QUEUE),
    "google_pubsub": ("Google Pub/Sub", TechCategory.QUEUE),
}


def detect_from_terraform(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect infrastructure from Terraform .tf files.
    
    Args:
        file_path: Path to a .tf file
        
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
    
    content_lower = content.lower()
    detected: set[str] = set()
    
    # resource "aws_rds_instance" "main" or resource "aws_lambda_function"
    resource_pattern = re.compile(
        r'resource\s+["\']([a-z0-9_]+)["\']',
        re.IGNORECASE,
    )
    for match in resource_pattern.finditer(content):
        resource_type = match.group(1).lower()
        # Match prefix (e.g. aws_rds_instance -> aws_rds)
        for pattern, (tech_name, category) in RESOURCE_PATTERNS.items():
            if resource_type.startswith(pattern) or pattern in resource_type:
                key = f"{tech_name}:{category.value}"
                if key not in detected:
                    detected.add(key)
                    detections.append(
                        TechnologyDetection(
                            source_file=source,
                            tech=tech_name,
                            category=category,
                            confidence=0.85,
                            details=f"Terraform resource type: {resource_type}",
                        )
                    )
                break
    
    # provider blocks
    if "terraform" in content_lower or "provider " in content_lower:
        if "Terraform" not in {d.tech for d in detections}:
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="Terraform",
                    category=TechCategory.CONTAINER,
                    confidence=0.9,
                    details="Terraform configuration",
                )
            )
    
    return detections
