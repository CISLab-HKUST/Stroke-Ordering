"""
Export ordered sketches as SVG, GIF, and MP4.
"""

from pathlib import Path as FilePath
from typing import Dict, List, Tuple
import html

try:
    from .data_structures import Sketch, Path
except ImportError:  # Allow running scripts directly from this folder.
    from data_structures import Sketch, Path


def _ordered_paths(sketch: Sketch, result: Dict) -> List[Tuple[int, Path, bool]]:
    ordered = []
    for order, stroke_index in enumerate(result["solution"], start=1):
        direction = result["directions"][order - 1]
        ordered.append((order, sketch.paths[stroke_index], direction))
    return ordered


def _path_points(path: Path, forward: bool = True) -> List[Tuple[float, float]]:
    points = []
    if not path.curves:
        return points
    points.append((path.curves[0].p_start.x, path.curves[0].p_start.y))
    for curve in path.curves:
        points.append((curve.p_end.x, curve.p_end.y))
    if not forward:
        points.reverse()
    return points


def _polyline_d(points: List[Tuple[float, float]]) -> str:
    if not points:
        return ""
    first, *rest = points
    commands = [f"M {first[0]:.3f} {first[1]:.3f}"]
    commands.extend(f"L {x:.3f} {y:.3f}" for x, y in rest)
    return " ".join(commands)


def save_ordered_svg(
    sketch: Sketch,
    result: Dict,
    output_file: str,
    show_labels: bool = False,
    include_metadata: bool = False,
) -> None:
    """Save an SVG whose path element order is the computed stroke order."""
    output = FilePath(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '<?xml version="1.0" ?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:ev="http://www.w3.org/2001/xml-events" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'baseProfile="full" '
            f'width="{sketch.width:g}" height="{sketch.height:g}" '
            f'version="1.1" viewBox="0 0 {sketch.width:g} {sketch.height:g}">'
        ),
        "\t<defs/>",
    ]

    labels = []
    for order, path, direction in _ordered_paths(sketch, result):
        points = _path_points(path, direction)
        if not points:
            continue

        metadata = ""
        if include_metadata:
            direction_text = "forward" if direction else "reverse"
            metadata = f' data-stroke-order="{order}" data-direction="{direction_text}"'
        lines.append(
            f'\t<path d="{html.escape(_polyline_d(points))}" fill="none"'
            f'{metadata} stroke="#000000" stroke-linecap="round" stroke-width="1"/>'
        )

        if show_labels:
            x, y = points[0]
            labels.append(
                f'\t<text x="{x + 4:.3f}" y="{y - 4:.3f}" '
                f'font-family="Arial, sans-serif" font-size="18" '
                f'fill="#d22">{order}</text>'
            )

    if show_labels:
        lines.extend(labels)
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")