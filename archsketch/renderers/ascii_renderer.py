"""ASCII renderer for terminal output with rich visual formatting."""

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.style import Style

from ..models import Architecture, ArchitectureRole, ArchitectureNode


# Role colors for visual distinction
ROLE_COLORS = {
    ArchitectureRole.REVERSE_PROXY: "bright_magenta",
    ArchitectureRole.FRONTEND: "bright_cyan",
    ArchitectureRole.BACKEND: "bright_green",
    ArchitectureRole.DATABASE: "bright_yellow",
    ArchitectureRole.CACHE: "bright_red",
    ArchitectureRole.WORKER: "bright_blue",
    ArchitectureRole.QUEUE: "orange3",
}

# Role icons for visual interest
ROLE_ICONS = {
    ArchitectureRole.REVERSE_PROXY: ">>",
    ArchitectureRole.FRONTEND: "##",
    ArchitectureRole.BACKEND: "@@",
    ArchitectureRole.DATABASE: "[]",
    ArchitectureRole.CACHE: "<>",
    ArchitectureRole.WORKER: "**",
    ArchitectureRole.QUEUE: "~~",
}


def render_ascii(
    architecture: Architecture,
    console: Console | None = None,
    *,
    show_table: bool = True,
) -> str:
    """
    Render architecture as a beautiful ASCII diagram in the terminal.
    
    Args:
        architecture: The architecture to render
        console: Rich console for output (optional)
        show_table: If False, skip the detected technologies table (compact mode).
        
    Returns:
        String representation of the architecture
    """
    if console is None:
        console = Console()
    
    if not architecture.nodes:
        console.print("[yellow]No architecture detected.[/yellow]")
        return ""
    
    console.print()
    
    # Print the main architecture diagram
    _print_vertical_diagram(architecture, console)
    
    # Print the legend
    _print_legend(architecture, console)
    
    # Print detected technologies table (unless compact)
    if show_table:
        _print_detections_table(architecture, console)
    
    return ""


def _create_node_box(node: ArchitectureNode, width: int = 28) -> Panel:
    """Create a styled box for a node."""
    color = ROLE_COLORS.get(node.role, "white")
    icon = ROLE_ICONS.get(node.role, "**")
    
    # Build the content
    tech_name = node.technologies[0] if node.technologies else "Unknown"
    
    content = Text()
    content.append(f"{icon} ", style=f"bold {color}")
    content.append(f"{node.role.value}\n", style=f"bold {color}")
    content.append(tech_name, style=f"{color}")
    
    return Panel(
        Align.center(content),
        border_style=color,
        width=width,
        padding=(0, 1),
    )


def _print_vertical_diagram(architecture: Architecture, console: Console) -> None:
    """Print a vertical flow diagram with boxes and arrows."""
    
    # Define the flow order
    role_order = [
        ArchitectureRole.REVERSE_PROXY,
        ArchitectureRole.FRONTEND,
        ArchitectureRole.BACKEND,
        ArchitectureRole.DATABASE,
    ]
    
    # Side components (displayed alongside main flow)
    side_roles = {
        ArchitectureRole.CACHE,
        ArchitectureRole.WORKER,
        ArchitectureRole.QUEUE,
    }
    
    # Get nodes by role
    nodes_by_role: dict[ArchitectureRole, ArchitectureNode] = {}
    for node in architecture.nodes:
        nodes_by_role[node.role] = node
    
    # Build the main vertical flow
    main_flow_roles = [r for r in role_order if r in nodes_by_role]
    side_nodes = [nodes_by_role[r] for r in side_roles if r in nodes_by_role]
    
    # Print header
    header = Text()
    header.append("  ARCHITECTURE SKETCH  ", style="bold white on blue")
    console.print(Align.center(header))
    console.print()
    
    # Calculate layout
    box_width = 28
    arrow_height = 1
    
    # Print each layer
    for i, role in enumerate(main_flow_roles):
        node = nodes_by_role[role]
        
        # For backend, show side branches
        if role == ArchitectureRole.BACKEND and side_nodes:
            _print_backend_with_branches(node, side_nodes, console, box_width)
        else:
            # Print centered node
            console.print(Align.center(_create_node_box(node, box_width)))
        
        # Print arrow to next node (if not last)
        if i < len(main_flow_roles) - 1:
            _print_down_arrow(console, box_width)
    
    console.print()


def _print_backend_with_branches(
    backend_node: ArchitectureNode,
    side_nodes: list[ArchitectureNode],
    console: Console,
    box_width: int,
) -> None:
    """Print backend node with side branches to cache/worker/queue."""
    
    # Create the backend box
    backend_box = _create_node_box(backend_node, box_width)
    
    # Create side boxes
    side_boxes = [_create_node_box(n, box_width - 4) for n in side_nodes]
    
    # Print backend centered
    console.print(Align.center(backend_box))
    
    if side_nodes:
        # Print branching arrows
        num_sides = len(side_nodes)
        
        # Create arrow pattern
        center_pad = " " * (box_width // 2 - 1)
        
        if num_sides == 1:
            # Single side branch
            arrow_line = Text()
            arrow_line.append(center_pad)
            arrow_line.append("|", style="dim")
            arrow_line.append("--------", style="dim")
            arrow_line.append(">", style="bold bright_red")
            console.print(Align.center(arrow_line))
        else:
            # Multiple branches - show fork
            arrow_line = Text()
            arrow_line.append(center_pad)
            arrow_line.append("|", style="dim")
            console.print(Align.center(arrow_line))
            
            fork_line = Text()
            fork_line.append(center_pad)
            fork_line.append("+", style="dim")
            for _ in range(num_sides):
                fork_line.append("------", style="dim")
                fork_line.append("+", style="dim")
            console.print(Align.center(fork_line))
            
            # Arrows down to each
            arrows = Text()
            arrows.append(center_pad)
            arrows.append(" ", style="dim")
            for _ in range(num_sides):
                arrows.append("  v   ", style="bold bright_red")
                arrows.append(" ")
            console.print(Align.center(arrows))
        
        # Print side boxes in columns
        if len(side_boxes) == 1:
            console.print(Align.center(Columns(side_boxes, padding=(0, 2))))
        else:
            console.print(Align.center(Columns(side_boxes, padding=(0, 1))))


def _print_down_arrow(console: Console, width: int) -> None:
    """Print a down arrow between nodes."""
    arrow = Text()
    arrow.append("|", style="dim white")
    console.print(Align.center(arrow))
    
    arrow2 = Text()
    arrow2.append("v", style="bold white")
    console.print(Align.center(arrow2))


def _print_legend(architecture: Architecture, console: Console) -> None:
    """Print a color legend for roles."""
    
    legend_items = []
    seen_roles = set()
    
    for node in architecture.nodes:
        if node.role not in seen_roles:
            seen_roles.add(node.role)
            color = ROLE_COLORS.get(node.role, "white")
            icon = ROLE_ICONS.get(node.role, "**")
            
            item = Text()
            item.append(f" {icon} ", style=f"bold {color}")
            item.append(f"{node.role.value} ", style=color)
            legend_items.append(item)
    
    if legend_items:
        legend_row = Text()
        for i, item in enumerate(legend_items):
            legend_row.append_text(item)
            if i < len(legend_items) - 1:
                legend_row.append(" | ", style="dim")
        
        console.print(Align.center(Panel(
            Align.center(legend_row),
            title="[dim]Legend[/dim]",
            border_style="dim",
            padding=(0, 1),
        )))
        console.print()


def _print_detections_table(architecture: Architecture, console: Console) -> None:
    """Print a styled table of detected technologies."""
    
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
    
    # Filter to only show high-confidence detections
    high_conf = [d for d in unique_detections if d.confidence >= 0.7]
    
    if not high_conf:
        high_conf = unique_detections[:10]
    
    table = Table(
        title="[bold]Detected Technologies[/bold]",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        padding=(0, 1),
    )
    table.add_column("Technology", style="bold white", no_wrap=True)
    table.add_column("Role", style="green")
    table.add_column("Confidence", justify="center")
    table.add_column("Source", style="dim", max_width=35)
    
    # Sort by confidence
    sorted_dets = sorted(high_conf, key=lambda d: -d.confidence)
    
    for det in sorted_dets[:12]:  # Limit rows
        # Confidence bar (ASCII-safe)
        conf_pct = int(det.confidence * 100)
        if conf_pct >= 90:
            conf_style = "bold green"
            conf_bar = "[====]"
        elif conf_pct >= 70:
            conf_style = "yellow"
            conf_bar = "[=== ]"
        elif conf_pct >= 50:
            conf_style = "orange3"
            conf_bar = "[==  ]"
        else:
            conf_style = "red"
            conf_bar = "[=   ]"
        
        conf_text = Text()
        conf_text.append(f"{conf_bar} ", style=conf_style)
        conf_text.append(f"{conf_pct}%", style=conf_style)
        
        # Truncate source path
        source = det.source_file
        if len(source) > 35:
            source = "..." + source[-32:]
        
        table.add_row(
            det.tech,
            det.category.value.replace("_", " ").title(),
            conf_text,
            source,
        )
    
    console.print(table)
    console.print()
