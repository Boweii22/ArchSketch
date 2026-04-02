"""Detector for .csproj / .fsproj / .vbproj files (C#/.NET projects)."""

import re
from pathlib import Path

from ..models import TechCategory, TechnologyDetection

TECH_PATTERNS = {
    # Web frameworks / hosting
    "microsoft.aspnetcore": ("ASP.NET Core", TechCategory.BACKEND),
    "microsoft.aspnet.mvc": ("ASP.NET MVC", TechCategory.BACKEND),
    "microsoft.aspnet.webapi": ("ASP.NET Web API", TechCategory.BACKEND),
    "carter": ("Carter", TechCategory.BACKEND),
    "fastendpoints": ("FastEndpoints", TechCategory.BACKEND),
    "minimal.apis": ("Minimal APIs", TechCategory.BACKEND),

    # Frontend / Blazor
    "microsoft.aspnetcore.components.webassembly": ("Blazor WASM", TechCategory.FRONTEND),
    "blazor": ("Blazor", TechCategory.FRONTEND),

    # Database / ORM
    "microsoft.entityframeworkcore": ("Entity Framework Core", TechCategory.DATABASE),
    "microsoft.entityframework": ("Entity Framework", TechCategory.DATABASE),
    "npgsql": ("PostgreSQL", TechCategory.DATABASE),
    "mysql.data": ("MySQL", TechCategory.DATABASE),
    "pomelo.entityframeworkcore.mysql": ("MySQL", TechCategory.DATABASE),
    "mongodb.driver": ("MongoDB", TechCategory.DATABASE),
    "dapper": ("Dapper", TechCategory.DATABASE),
    "system.data.sqlite": ("SQLite", TechCategory.DATABASE),
    "microsoft.data.sqlite": ("SQLite", TechCategory.DATABASE),
    "cosmos": ("Azure Cosmos DB", TechCategory.DATABASE),
    "marten": ("Marten", TechCategory.DATABASE),

    # Cache
    "stackexchange.redis": ("Redis", TechCategory.CACHE),
    "microsoft.extensions.caching.stackexchangeredis": ("Redis", TechCategory.CACHE),

    # Queue / messaging
    "masstransit": ("MassTransit", TechCategory.QUEUE),
    "nservicebus": ("NServiceBus", TechCategory.QUEUE),
    "rabbitmq.client": ("RabbitMQ", TechCategory.QUEUE),
    "confluent.kafka": ("Kafka", TechCategory.QUEUE),
    "azure.messaging.servicebus": ("Azure Service Bus", TechCategory.QUEUE),

    # Worker
    "hangfire": ("Hangfire", TechCategory.WORKER),
    "quartz": ("Quartz.NET", TechCategory.WORKER),
    "coravel": ("Coravel", TechCategory.WORKER),
}


def detect_from_csproj(file_path: Path) -> list[TechnologyDetection]:
    """Detect technologies from a .csproj / .fsproj / .vbproj file."""
    detections: list[TechnologyDetection] = []
    source = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return detections

    suffix = file_path.suffix.lower()
    lang = {"csproj": "C#", "fsproj": "F#", "vbproj": "VB.NET"}.get(suffix.lstrip("."), "C#")

    detections.append(TechnologyDetection(
        source_file=source,
        tech=lang,
        category=TechCategory.BACKEND,
        confidence=0.95,
        details=f"{file_path.name} found — .NET project",
    ))

    detected_techs: set[str] = {lang}

    # Extract all PackageReference Include= values
    for match in re.finditer(r'PackageReference\s+Include="([^"]+)"', content, re.IGNORECASE):
        pkg = match.group(1).lower()
        for pattern, (tech_name, category) in TECH_PATTERNS.items():
            if pattern in pkg:
                if tech_name not in detected_techs:
                    detected_techs.add(tech_name)
                    detections.append(TechnologyDetection(
                        source_file=source,
                        tech=tech_name,
                        category=category,
                        confidence=0.9,
                        details=f"Found '{match.group(1)}' in {file_path.name}",
                    ))

    return detections
