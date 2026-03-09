"""Mermaid diagram renderer."""

from pathlib import Path

from ..models import Architecture
from ..utils import sanitize_id


def render_mermaid(architecture: Architecture) -> str:
    """
    Render architecture as a Mermaid diagram.
    
    Args:
        architecture: The architecture to render
        
    Returns:
        Mermaid diagram as a string
    """
    if not architecture.nodes:
        return "graph TD\n  Empty[No architecture detected]"
    
    lines: list[str] = ["graph TD"]
    
    # Create node definitions with sanitized IDs
    node_ids: dict[str, str] = {}
    for node in architecture.nodes:
        # Create a mermaid-safe ID
        safe_id = sanitize_id(node.id)
        node_ids[node.id] = safe_id
        
        # Create the label
        label = node.display_label()
        
        # Add node definition
        lines.append(f"  {safe_id}[{label}]")
    
    # Add empty line before edges
    if architecture.edges:
        lines.append("")
    
    # Create edges
    for edge in architecture.edges:
        source_id = node_ids.get(edge.source)
        target_id = node_ids.get(edge.target)
        
        if source_id and target_id:
            lines.append(f"  {source_id} --> {target_id}")
    
    return "\n".join(lines)


def export_mermaid(architecture: Architecture, output_path: str | Path) -> Path:
    """
    Export architecture as a Mermaid diagram file.
    
    Args:
        architecture: The architecture to render
        output_path: Path to write the .mmd file
        
    Returns:
        Path to the created file
    """
    output = Path(output_path)
    
    # Ensure .mmd extension
    if output.suffix not in (".mmd", ".md"):
        output = output.with_suffix(".mmd")
    
    content = render_mermaid(architecture)
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")
    
    return output
