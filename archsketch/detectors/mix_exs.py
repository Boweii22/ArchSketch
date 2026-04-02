"""Detector for mix.exs files (Elixir projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

TECH_PATTERNS = {
    # Web frameworks
    "phoenix": ("Phoenix", TechCategory.BACKEND),
    "plug": ("Plug", TechCategory.BACKEND),
    "absinthe": ("Absinthe (GraphQL)", TechCategory.BACKEND),
    "bandit": ("Bandit", TechCategory.BACKEND),

    # Database / ORM
    "ecto": ("Ecto", TechCategory.DATABASE),
    "ecto_sql": ("Ecto SQL", TechCategory.DATABASE),
    "postgrex": ("PostgreSQL", TechCategory.DATABASE),
    "myxql": ("MySQL", TechCategory.DATABASE),
    "mongodb_driver": ("MongoDB", TechCategory.DATABASE),
    "sqlite_ecto3": ("SQLite", TechCategory.DATABASE),
    "ash": ("Ash Framework", TechCategory.DATABASE),

    # Cache
    "redix": ("Redis", TechCategory.CACHE),
    "nebulex": ("Nebulex Cache", TechCategory.CACHE),
    "cachex": ("Cachex", TechCategory.CACHE),

    # Queue / Worker
    "oban": ("Oban", TechCategory.WORKER),
    "exq": ("Exq", TechCategory.WORKER),
    "quantum": ("Quantum", TechCategory.WORKER),
    "broadway": ("Broadway", TechCategory.QUEUE),
    "amqp": ("RabbitMQ", TechCategory.QUEUE),
    "brod": ("Kafka", TechCategory.QUEUE),
    "kafka_ex": ("Kafka", TechCategory.QUEUE),
}


def detect_from_mix_exs(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a mix.exs file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    detections.append(TechnologyDetection(
        source_file=source,
        tech="Elixir",
        category=TechCategory.BACKEND,
        confidence=0.95,
        details="mix.exs found — Elixir project",
    ))

    detected_techs: set[str] = {"Elixir"}

    # Deps look like: {:phoenix, "~> 1.7"}  or  {:ecto_sql, "~> 3.10"}
    for match in re.finditer(r'\{:([a-zA-Z0-9_]+)\s*,', content):
        dep = match.group(1).lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if dep == pattern:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found ':{dep}' in mix.exs",
                    ))

    return detections
