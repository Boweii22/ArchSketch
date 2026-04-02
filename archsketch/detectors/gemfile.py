"""Detector for Gemfile files (Ruby projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

TECH_PATTERNS = {
    # Web frameworks
    "rails": ("Ruby on Rails", TechCategory.BACKEND),
    "sinatra": ("Sinatra", TechCategory.BACKEND),
    "hanami": ("Hanami", TechCategory.BACKEND),
    "roda": ("Roda", TechCategory.BACKEND),
    "padrino": ("Padrino", TechCategory.BACKEND),
    "grape": ("Grape", TechCategory.BACKEND),

    # Database
    "pg": ("PostgreSQL", TechCategory.DATABASE),
    "mysql2": ("MySQL", TechCategory.DATABASE),
    "sqlite3": ("SQLite", TechCategory.DATABASE),
    "mongoid": ("MongoDB", TechCategory.DATABASE),
    "mongo": ("MongoDB", TechCategory.DATABASE),
    "sequel": ("Sequel", TechCategory.DATABASE),
    "activerecord": ("ActiveRecord", TechCategory.DATABASE),
    "rom-rb": ("ROM", TechCategory.DATABASE),

    # Cache
    "redis": ("Redis", TechCategory.CACHE),
    "dalli": ("Memcached", TechCategory.CACHE),

    # Worker / Queue
    "sidekiq": ("Sidekiq", TechCategory.WORKER),
    "resque": ("Resque", TechCategory.WORKER),
    "delayed_job": ("Delayed Job", TechCategory.WORKER),
    "good_job": ("Good Job", TechCategory.WORKER),
    "sneakers": ("Sneakers", TechCategory.WORKER),

    # Messaging
    "bunny": ("RabbitMQ", TechCategory.QUEUE),
    "ruby-kafka": ("Kafka", TechCategory.QUEUE),
    "karafka": ("Kafka", TechCategory.QUEUE),
}


def detect_from_gemfile(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a Gemfile."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    detections.append(TechnologyDetection(
        source_file=source,
        tech="Ruby",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="Gemfile found — Ruby project",
    ))

    detected_techs: set[str] = {"Ruby"}

    # gem 'name' or gem "name"
    for match in re.finditer(r"""gem\s+['"]([a-zA-Z0-9_-]+)['"]""", content):
        gem = match.group(1).lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if gem == pattern or gem.startswith(pattern):
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found gem '{match.group(1)}' in Gemfile",
                    ))

    return detections
