"""ASCII renderer for terminal output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from ..models import Architecture, ArchitectureRole


def render_ascii(architecture: Architecture, console: Console | None = None) -> str:
    """
    Render architecture as ASCII art in the terminal.
    
    Args:
        architecture: The architecture to render
        console: Rich console for output (optional)
        
    Returns:
        String representation of the architecture
    """
    if console is None:
        console = Console()
    
    if not architecture.nodes:
        console.print("[yellow]No architecture detected.[/yellow]")
        return ""
    
    # Build output lines
    lines: list[str] = []
    
    # Create a simple flow diagram
    lines.append("")
    lines.append(_build_flow_diagram(architecture))
    lines.append("")
    
    # Print with Rich
    console.print(Panel(
        "\n".join(lines),
        title="[bold blue]Architecture Sketch[/bold blue]",
        border_style="blue",
    ))
    
    # Also show detected technologies table
    _print_detections_table(architecture, console)
    
    return "\n".join(lines)


def _build_flow_diagram(architecture: Architecture) -> str:
    """Build a simple ASCII flow diagram."""
    
    # Define display order for roles
    role_order = [
        ArchitectureRole.REVERSE_PROXY,
        ArchitectureRole.FRONTEND,
        ArchitectureRole.BACKEND,
        ArchitectureRole.DATABASE,
        ArchitectureRole.CACHE,
        ArchitectureRole.WORKER,
        ArchitectureRole.QUEUE,
    ]
    
    # Create node labels map
    node_labels: dict[str, str] = {}
    for node in architecture.nodes:
        node_labels[node.id] = node.display_label()
    
    # Group nodes by their role for ordering
    nodes_by_role: dict[ArchitectureRole, list[str]] = {}
    for node in architecture.nodes:
        if node.role not in nodes_by_role:
            nodes_by_role[node.role] = []
        nodes_by_role[node.role].append(node.id)
    
    # Build adjacency for edges
    outgoing: dict[str, list[str]] = {}
    for edge in architecture.edges:
        if edge.source not in outgoing:
            outgoing[edge.source] = []
        outgoing[edge.source].append(edge.target)
    
    lines: list[str] = []
    
    # Simple horizontal flow representation
    main_flow: list[str] = []
    side_branches: list[tuple[str, str]] = []  # (from_node, side_node)
    
    # Determine main flow path
    for role in role_order:
        if role in nodes_by_role:
            for node_id in nodes_by_role[role]:
                if role in (ArchitectureRole.CACHE, ArchitectureRole.QUEUE, ArchitectureRole.WORKER):
                    # These are typically side branches
                    for source_id, targets in outgoing.items():
                        if node_id in targets and source_id in node_labels:
                            side_branches.append((source_id, node_id))
                else:
                    main_flow.append(node_id)
    
    # Build main flow line
    if main_flow:
        main_parts = [f"[{node_labels[nid]}]" for nid in main_flow]
        main_line = " --> ".join(main_parts)
        lines.append(main_line)
    
    # Add side branches
    for source_id, side_id in side_branches:
        if side_id in node_labels:
            # Calculate indent based on source position
            if source_id in main_flow:
                idx = main_flow.index(source_id)
                indent = sum(len(f"[{node_labels[nid]}]") + 5 for nid in main_flow[:idx])
                indent += len(f"[{node_labels[source_id]}]") // 2
                lines.append(" " * indent + f"\\--> [{node_labels[side_id]}]")
    
    return "\n".join(lines) if lines else "[No components detected]"


def _print_detections_table(architecture: Architecture, console: Console) -> None:
    """Print a table of detected technologies."""
    
    if not architecture.detections:
        return
    
    # Deduplicate detections for display
    seen: set[str] = set()
    unique_detections = []
    for det in architecture.detections:
        key = f"{det.tech}:{det.category.value}"
        if key not in seen:
            seen.add(key)
            unique_detections.append(det)
    
    table = Table(title="Detected Technologies", show_header=True)
    table.add_column("Technology", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Confidence", style="yellow")
    table.add_column("Source", style="dim")
    
    # Sort by category then by confidence
    sorted_dets = sorted(
        unique_detections,
        key=lambda d: (d.category.value, -d.confidence),
    )
    
    for det in sorted_dets:
        conf_str = f"{det.confidence:.0%}"
        # Truncate source path for display
        source = det.source_file
        if len(source) > 40:
            source = "..." + source[-37:]
        
        table.add_row(det.tech, det.category.value, conf_str, source)
    
    console.print()
    console.print(table)
