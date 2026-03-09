"""Detector for package.json files (Node.js/JavaScript projects)."""

import json
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

# Technology patterns to detect in dependencies
TECH_PATTERNS = {
    # Frontend frameworks
    "react": ("React", TechCategory.FRONTEND),
    "next": ("Next.js", TechCategory.FRONTEND),
    "vue": ("Vue.js", TechCategory.FRONTEND),
    "nuxt": ("Nuxt.js", TechCategory.FRONTEND),
    "@angular/core": ("Angular", TechCategory.FRONTEND),
    "svelte": ("Svelte", TechCategory.FRONTEND),
    
    # Backend frameworks
    "express": ("Express", TechCategory.BACKEND),
    "@nestjs/core": ("NestJS", TechCategory.BACKEND),
    "fastify": ("Fastify", TechCategory.BACKEND),
    "koa": ("Koa", TechCategory.BACKEND),
    "hapi": ("Hapi", TechCategory.BACKEND),
    
    # Database clients
    "pg": ("PostgreSQL", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "mysql2": ("MySQL", TechCategory.DATABASE),
    "mongodb": ("MongoDB", TechCategory.DATABASE),
    "mongoose": ("MongoDB", TechCategory.DATABASE),
    "sqlite3": ("SQLite", TechCategory.DATABASE),
    "prisma": ("Prisma", TechCategory.DATABASE),
    "@prisma/client": ("Prisma", TechCategory.DATABASE),
    "typeorm": ("TypeORM", TechCategory.DATABASE),
    "sequelize": ("Sequelize", TechCategory.DATABASE),
    
    # Cache
    "redis": ("Redis", TechCategory.CACHE),
    "ioredis": ("Redis", TechCategory.CACHE),
    
    # Queue/Worker
    "bull": ("Bull Queue", TechCategory.QUEUE),
    "bullmq": ("BullMQ", TechCategory.QUEUE),
    "agenda": ("Agenda", TechCategory.QUEUE),
}


def detect_from_package_json(file_path: Path) -> list[TechnologyDetection]:
    """
    Detect technologies from a package.json file.
    
    Args:
        file_path: Path to the package.json file
        
    Returns:
        List of detected technologies
    """
    detections: list[TechnologyDetection] = []
    source = str(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return detections
    
    # Gather all dependencies
    all_deps: set[str] = set()
    
    for dep_key in ["dependencies", "devDependencies", "peerDependencies"]:
        if dep_key in data and isinstance(data[dep_key], dict):
            all_deps.update(data[dep_key].keys())
    
    # Check for technology patterns
    detected_techs: set[str] = set()
    
    for dep in all_deps:
        dep_lower = dep.lower()
        
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in dep_lower or dep_lower == pattern:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(
                        TechnologyDetection(
                            source_file=source,
                            tech=tech_name,
                            category=category,
                            confidence=0.9,
                            details=f"Found '{dep}' in dependencies",
                        )
                    )
    
    # Check scripts for hints
    scripts = data.get("scripts", {})
    if isinstance(scripts, dict):
        script_text = " ".join(str(v) for v in scripts.values())
        
        if "next" in script_text and "Next.js" not in detected_techs:
            detections.append(
                TechnologyDetection(
                    source_file=source,
                    tech="Next.js",
                    category=TechCategory.FRONTEND,
                    confidence=0.7,
                    details="Found 'next' in scripts",
                )
            )
    
    return detections
