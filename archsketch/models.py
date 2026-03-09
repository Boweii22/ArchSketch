"""Data models for ArchSketch."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TechCategory(str, Enum):
    """Categories of detected technologies."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    CACHE = "cache"
    REVERSE_PROXY = "reverse_proxy"
    WORKER = "worker"
    QUEUE = "queue"
    CONTAINER = "container"
    UNKNOWN = "unknown"


class ArchitectureRole(str, Enum):
    """Roles in the architecture."""
    FRONTEND = "Frontend"
    BACKEND = "Backend"
    DATABASE = "Database"
    CACHE = "Cache"
    REVERSE_PROXY = "Reverse Proxy"
    WORKER = "Worker"
    QUEUE = "Queue"


@dataclass
class TechnologyDetection:
    """Represents a detected technology from a source file."""
    source_file: str
    tech: str
    category: TechCategory
    confidence: float = 1.0
    details: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.tech} ({self.category.value}) from {self.source_file}"


@dataclass
class ArchitectureNode:
    """A node in the architecture graph."""
    id: str
    label: str
    role: ArchitectureRole
    technologies: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)  # file paths that contributed (for explain/tooltips)
    
    def __str__(self) -> str:
        tech_str = ", ".join(self.technologies) if self.technologies else "Unknown"
        return f"[{self.role.value}: {tech_str}]"
    
    def display_label(self) -> str:
        """Get a display label for rendering."""
        if self.technologies:
            return f"{self.role.value}: {self.technologies[0]}"
        return self.role.value
    
    def explanation(self) -> str:
        """Short explanation for tooltips/annotations."""
        if self.sources:
            short = self.sources[0]
            if len(short) > 40:
                short = "..." + short[-37:]
            return f"From: {short}"
        return f"Inferred as {self.role.value}"


@dataclass
class ArchitectureEdge:
    """An edge connecting two architecture nodes."""
    source: str
    target: str
    relation: str = "connects"
    
    def __str__(self) -> str:
        return f"{self.source} --[{self.relation}]--> {self.target}"


@dataclass
class Architecture:
    """Complete architecture representation."""
    nodes: list[ArchitectureNode] = field(default_factory=list)
    edges: list[ArchitectureEdge] = field(default_factory=list)
    detections: list[TechnologyDetection] = field(default_factory=list)
    
    def get_node(self, node_id: str) -> Optional[ArchitectureNode]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def has_role(self, role: ArchitectureRole) -> bool:
        """Check if architecture has a node with given role."""
        return any(node.role == role for node in self.nodes)
