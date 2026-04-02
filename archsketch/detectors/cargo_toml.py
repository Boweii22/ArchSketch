"""Detector for Cargo.toml files (Rust projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

TECH_PATTERNS = {
    # Web frameworks
    "actix-web": ("Actix Web", TechCategory.BACKEND),
    "actix_web": ("Actix Web", TechCategory.BACKEND),
    "axum": ("Axum", TechCategory.BACKEND),
    "rocket": ("Rocket", TechCategory.BACKEND),
    "warp": ("Warp", TechCategory.BACKEND),
    "hyper": ("Hyper", TechCategory.BACKEND),
    "tide": ("Tide", TechCategory.BACKEND),
    "poem": ("Poem", TechCategory.BACKEND),
    "salvo": ("Salvo", TechCategory.BACKEND),
    "ntex": ("ntex", TechCategory.BACKEND),

    # Databases / ORMs
    "sqlx": ("SQLx", TechCategory.DATABASE),
    "diesel": ("Diesel ORM", TechCategory.DATABASE),
    "sea-orm": ("SeaORM", TechCategory.DATABASE),
    "sea_orm": ("SeaORM", TechCategory.DATABASE),
    "tokio-postgres": ("PostgreSQL", TechCategory.DATABASE),
    "postgres": ("PostgreSQL", TechCategory.DATABASE),
    "mysql_async": ("MySQL", TechCategory.DATABASE),
    "mysql": ("MySQL", TechCategory.DATABASE),
    "rusqlite": ("SQLite", TechCategory.DATABASE),
    "mongodb": ("MongoDB", TechCategory.DATABASE),

    # Cache
    "redis": ("Redis", TechCategory.CACHE),
    "deadpool-redis": ("Redis", TechCategory.CACHE),
    "fred": ("Redis", TechCategory.CACHE),

    # Queue / messaging
    "lapin": ("RabbitMQ", TechCategory.QUEUE),
    "rdkafka": ("Kafka", TechCategory.QUEUE),
    "async-nats": ("NATS", TechCategory.QUEUE),
}


def detect_from_cargo_toml(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a Cargo.toml file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    # Always emit Rust as the language / backend runtime
    detections.append(TechnologyDetection(
        source_file=source,
        tech="Rust",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="Cargo.toml found — Rust project",
    ))

    detected_techs: set[str] = {"Rust"}

    # Extract bare dependency names from [dependencies] / [dev-dependencies]
    # Handles both `name = "version"` and `name = { version = "..." }` forms
    for match in re.finditer(r'^([a-zA-Z0-9_-]+)\s*=', content, re.MULTILINE):
        pkg = match.group(1).strip().lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pkg == pattern or pkg == pattern.replace("-", "_"):
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{pkg}' in Cargo.toml",
                    ))

    return detections
