"""Inference engine for deriving architecture from detections."""

from ..models import (
    Architecture,
    ArchitectureEdge,
    ArchitectureNode,
    ArchitectureRole,
    TechCategory,
    TechnologyDetection,
)
from ..utils import sanitize_id


class InferenceEngine:
    """
    Rule-based inference engine that converts technology detections
    into architecture nodes and edges.
    """
    
    def __init__(self):
        self.architecture = Architecture()
    
    def infer(self, detections: list[TechnologyDetection]) -> Architecture:
        """
        Infer architecture from a list of technology detections.
        
        Args:
            detections: List of detected technologies
            
        Returns:
            Architecture with nodes and edges
        """
        self.architecture = Architecture(detections=detections)
        
        # Group detections by category
        by_category: dict[TechCategory, list[TechnologyDetection]] = {}
        for det in detections:
            if det.category not in by_category:
                by_category[det.category] = []
            by_category[det.category].append(det)
        
        # Create nodes for each role
        self._create_nodes(by_category)
        
        # Create edges between nodes
        self._create_edges()
        
        return self.architecture
    
    def _create_nodes(self, by_category: dict[TechCategory, list[TechnologyDetection]]) -> None:
        """Create architecture nodes from categorized detections."""
        
        # Frontend node
        frontend_techs = self._get_primary_techs(by_category.get(TechCategory.FRONTEND, []))
        if frontend_techs:
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="frontend",
                    label=f"Frontend: {frontend_techs[0]}",
                    role=ArchitectureRole.FRONTEND,
                    technologies=frontend_techs,
                )
            )
        
        # Backend node
        backend_techs = self._get_primary_techs(by_category.get(TechCategory.BACKEND, []))
        if backend_techs:
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="backend",
                    label=f"Backend: {backend_techs[0]}",
                    role=ArchitectureRole.BACKEND,
                    technologies=backend_techs,
                )
            )
        
        # Database node
        db_techs = self._get_primary_techs(by_category.get(TechCategory.DATABASE, []))
        if db_techs:
            # Filter out ORMs for the primary label, prefer actual DBs
            primary_dbs = [t for t in db_techs if t not in ("SQLAlchemy", "Prisma", "TypeORM", "Sequelize", "SQLModel", "Tortoise ORM", "Peewee")]
            label_tech = primary_dbs[0] if primary_dbs else db_techs[0]
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="database",
                    label=f"Database: {label_tech}",
                    role=ArchitectureRole.DATABASE,
                    technologies=db_techs,
                )
            )
        
        # Cache node
        cache_techs = self._get_primary_techs(by_category.get(TechCategory.CACHE, []))
        if cache_techs:
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="cache",
                    label=f"Cache: {cache_techs[0]}",
                    role=ArchitectureRole.CACHE,
                    technologies=cache_techs,
                )
            )
        
        # Reverse proxy node
        proxy_techs = self._get_primary_techs(by_category.get(TechCategory.REVERSE_PROXY, []))
        if proxy_techs:
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="reverse_proxy",
                    label=f"Reverse Proxy: {proxy_techs[0]}",
                    role=ArchitectureRole.REVERSE_PROXY,
                    technologies=proxy_techs,
                )
            )
        
        # Worker node
        worker_techs = self._get_primary_techs(by_category.get(TechCategory.WORKER, []))
        if worker_techs:
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="worker",
                    label=f"Worker: {worker_techs[0]}",
                    role=ArchitectureRole.WORKER,
                    technologies=worker_techs,
                )
            )
        
        # Queue node
        queue_techs = self._get_primary_techs(by_category.get(TechCategory.QUEUE, []))
        if queue_techs:
            self.architecture.nodes.append(
                ArchitectureNode(
                    id="queue",
                    label=f"Queue: {queue_techs[0]}",
                    role=ArchitectureRole.QUEUE,
                    technologies=queue_techs,
                )
            )
    
    def _create_edges(self) -> None:
        """Create edges based on common architecture patterns."""
        
        has_frontend = self.architecture.has_role(ArchitectureRole.FRONTEND)
        has_backend = self.architecture.has_role(ArchitectureRole.BACKEND)
        has_database = self.architecture.has_role(ArchitectureRole.DATABASE)
        has_cache = self.architecture.has_role(ArchitectureRole.CACHE)
        has_proxy = self.architecture.has_role(ArchitectureRole.REVERSE_PROXY)
        has_worker = self.architecture.has_role(ArchitectureRole.WORKER)
        has_queue = self.architecture.has_role(ArchitectureRole.QUEUE)
        
        # Reverse proxy connections
        if has_proxy:
            if has_frontend:
                self.architecture.edges.append(
                    ArchitectureEdge(
                        source="reverse_proxy",
                        target="frontend",
                        relation="routes",
                    )
                )
            if has_backend:
                self.architecture.edges.append(
                    ArchitectureEdge(
                        source="reverse_proxy",
                        target="backend",
                        relation="routes",
                    )
                )
        
        # Frontend to backend
        if has_frontend and has_backend:
            self.architecture.edges.append(
                ArchitectureEdge(
                    source="frontend",
                    target="backend",
                    relation="calls",
                )
            )
        
        # Backend to database
        if has_backend and has_database:
            self.architecture.edges.append(
                ArchitectureEdge(
                    source="backend",
                    target="database",
                    relation="queries",
                )
            )
        
        # Backend to cache
        if has_backend and has_cache:
            self.architecture.edges.append(
                ArchitectureEdge(
                    source="backend",
                    target="cache",
                    relation="caches",
                )
            )
        
        # Backend to queue
        if has_backend and has_queue:
            self.architecture.edges.append(
                ArchitectureEdge(
                    source="backend",
                    target="queue",
                    relation="publishes",
                )
            )
        
        # Worker connections
        if has_worker:
            if has_queue:
                self.architecture.edges.append(
                    ArchitectureEdge(
                        source="worker",
                        target="queue",
                        relation="consumes",
                    )
                )
            if has_database:
                self.architecture.edges.append(
                    ArchitectureEdge(
                        source="worker",
                        target="database",
                        relation="queries",
                    )
                )
            if has_cache:
                self.architecture.edges.append(
                    ArchitectureEdge(
                        source="worker",
                        target="cache",
                        relation="uses",
                    )
                )
        
        # Frontend-only with database (e.g., Jamstack with direct DB access)
        if has_frontend and has_database and not has_backend:
            self.architecture.edges.append(
                ArchitectureEdge(
                    source="frontend",
                    target="database",
                    relation="queries",
                )
            )
    
    def _get_primary_techs(self, detections: list[TechnologyDetection]) -> list[str]:
        """
        Get unique technology names from detections, sorted by confidence.
        """
        # Sort by confidence and deduplicate
        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
        
        seen: set[str] = set()
        techs: list[str] = []
        
        for det in sorted_dets:
            if det.tech not in seen:
                seen.add(det.tech)
                techs.append(det.tech)
        
        return techs
