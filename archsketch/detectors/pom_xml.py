"""Detector for Maven pom.xml files (Java/Kotlin projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Maven artifact patterns: artifactId or groupId:artifactId
TECH_PATTERNS = {
    # Spring Boot
    "spring-boot-starter": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-web": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-data-jpa": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-data-mongodb": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-data-redis": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-amqp": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-security": ("Spring Boot", TechCategory.BACKEND),
    "spring-boot-starter-graphql": ("Spring Boot", TechCategory.BACKEND),
    
    # Database
    "postgresql": ("PostgreSQL", TechCategory.DATABASE),
    "mysql-connector": ("MySQL", TechCategory.DATABASE),
    "mongodb": ("MongoDB", TechCategory.DATABASE),
    "redis": ("Redis", TechCategory.CACHE),
    "jedis": ("Redis", TechCategory.CACHE),
    "lettuce": ("Redis", TechCategory.CACHE),
    
    # Message queues
    "spring-kafka": ("Kafka", TechCategory.QUEUE),
    "amqp-client": ("RabbitMQ", TechCategory.QUEUE),
    
    # Other Java backends
    "micronaut": ("Micronaut", TechCategory.BACKEND),
    "quarkus": ("Quarkus", TechCategory.BACKEND),
    "vert.x": ("Vert.x", TechCategory.BACKEND),
    "javax.servlet": ("Jakarta Servlet", TechCategory.BACKEND),
}


def detect_from_pom_xml(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from a Maven pom.xml file.
    
    Args:
        file_path: Path to the pom.xml file
        
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
    
    # Normalize: strip comments and collapse whitespace for simpler matching
    content_no_comments = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    content_lower = content_no_comments.lower()
    
    detected_techs: set[str] = set()
    
    # Match dependency artifactId (and common groupId:artifactId)
    # Pattern: <artifactId>spring-boot-starter-web</artifactId>
    artifact_pattern = re.compile(
        r"<artifactId>\s*([^<]+)\s*</artifactId>",
        re.IGNORECASE,
    )
    
    for match in artifact_pattern.finditer(content):
        artifact_id = match.group(1).strip().lower()
        
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in artifact_id or artifact_id == pattern:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(
                        TechnologyDetection(
                            source_file=source,
                            tech=tech_name,
                            category=category,
                            confidence=0.9,
                            details=f"Found artifact '{artifact_id}' in pom.xml",
                        )
                    )
                break
    
    # Also check for Spring Boot in parent
    if "spring-boot" in content_lower and "Spring Boot" not in detected_techs:
        detected_techs.add("Spring Boot")
        detections.append(
            TechnologyDetection(
                source_file=source,
                tech="Spring Boot",
                category=TechCategory.BACKEND,
                confidence=0.85,
                details="Spring Boot parent or dependency in pom.xml",
            )
        )
    
    return detections
