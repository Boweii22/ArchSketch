"""Graphviz/SVG renderer for architecture diagrams."""

from pathlib import Path

from ..models import Architecture
from ..utils import sanitize_id


def render_dot(architecture: Architecture) -> str:
    """
    Render architecture as a Graphviz DOT string.
    
    Args:
        architecture: The architecture to render
        
    Returns:
        DOT format string
    """
    if not architecture.nodes:
        return 'digraph G { Empty [label="No architecture detected"] }'
    
    lines: list[str] = [
        "digraph Architecture {",
        "  rankdir=TB;",
        "  node [shape=box, style=rounded, fontname=Arial, fontsize=10];",
        "  edge [fontname=Arial, fontsize=9];",
        "",
    ]
    
    # Node definitions with labels
    node_ids: dict[str, str] = {}
    for node in architecture.nodes:
        safe_id = sanitize_id(node.id)
        node_ids[node.id] = safe_id
        label = node.display_label().replace('"', '\\"')
        lines.append(f'  {safe_id} [label="{label}"];')
    
    lines.append("")
    
    # Edges
    for edge in architecture.edges:
        source_id = node_ids.get(edge.source)
        target_id = node_ids.get(edge.target)
        if source_id and target_id:
            lines.append(f"  {source_id} -> {target_id};")
    
    lines.append("}")
    return "\n".join(lines)


def export_svg(architecture: Architecture, output_path: str | Path) -> Path:
    """
    Export architecture as an SVG file using Graphviz.
    
    Requires the 'graphviz' Python package and Graphviz binaries installed.
    Install: pip install graphviz
    System: https://graphviz.org/download/
    
    Args:
        architecture: The architecture to render
        output_path: Path to write the .svg file
        
    Returns:
        Path to the created file
        
    Raises:
        RuntimeError: If graphviz is not installed or dot fails
    """
    try:
        import graphviz
    except ImportError as e:
        raise RuntimeError(
            "Graphviz export requires the 'graphviz' package. "
            "Install with: pip install graphviz\n"
            "You also need Graphviz binaries: https://graphviz.org/download/"
        ) from e
    
    output = Path(output_path)
    if output.suffix.lower() != ".svg":
        output = output.with_suffix(".svg")
    
    dot_source = render_dot(architecture)
    
    try:
        dot = graphviz.Source(dot_source)
        dot.render(
            filename=output.stem,
            directory=str(output.parent),
            format="svg",
            cleanup=True,
        )
    except graphviz.ExecutableNotFound as e:
        raise RuntimeError(
            "Graphviz 'dot' executable not found. "
            "Install Graphviz and add its bin folder to PATH: "
            "https://graphviz.org/download/ "
            "On Windows, typical path: C:\\Program Files\\Graphviz\\bin"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to generate SVG: {e}. "
            "Ensure Graphviz is installed and 'dot' is in your PATH."
        ) from e
    
    # graphviz renders to output.parent/output.stem.svg
    result = output.parent / f"{output.stem}.svg"
    return result


def export_dot(architecture: Architecture, output_path: str | Path) -> Path:
    """
    Export architecture as a .dot file (no Graphviz binary required).
    
    Args:
        architecture: The architecture to render
        output_path: Path to write the .dot file
        
    Returns:
        Path to the created file
    """
    output = Path(output_path)
    if output.suffix.lower() != ".dot":
        output = output.with_suffix(".dot")
    
    content = render_dot(architecture)
    output.write_text(content, encoding="utf-8")
    return output
