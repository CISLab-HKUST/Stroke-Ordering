"""
Independent data structures for stroke ordering.
Provides Point, Curve, Path, and Sketch classes.
"""

from typing import List, Tuple, Optional
import numpy as np


class Point:
    """Represents a 2D point."""

    def __init__(self, x: float, y: float):
        """
        Initialize a Point.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return f"Point({self.x:.2f}, {self.y:.2f})"

    def __eq__(self, other):
        return (
            isinstance(other, Point)
            and np.isclose(self.x, other.x)
            and np.isclose(self.y, other.y)
        )

    def distance_to(self, other: "Point") -> float:
        """Calculate Euclidean distance to another point."""
        return np.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Curve:
    """Represents a line segment between two points."""

    def __init__(self, p_start: Point, p_end: Point):
        """
        Initialize a Curve.

        Args:
            p_start: Start point
            p_end: End point
        """
        self.p_start = p_start
        self.p_end = p_end

    def __repr__(self):
        return f"Curve({self.p_start} -> {self.p_end})"

    @staticmethod
    def from_line(points: List[Point]) -> "Curve":
        """Create a Curve from a line (list of 2 points)."""
        if len(points) < 2:
            raise ValueError("Need at least 2 points to create a Curve")
        return Curve(points[0], points[1])

    def length(self) -> float:
        """Get the length of this curve."""
        return self.p_start.distance_to(self.p_end)


class Path:
    """Represents a stroke (sequence of curves)."""

    def __init__(self, curves: Optional[List[Curve]] = None):
        """
        Initialize a Path.

        Args:
            curves: List of Curve objects
        """
        self.curves = curves if curves is not None else []

    def __repr__(self):
        return f"Path({len(self.curves)} curves)"

    def __len__(self):
        return len(self.curves)

    def get_start_point(self) -> Optional[Point]:
        """Get the starting point of the path."""
        return self.curves[0].p_start if self.curves else None

    def get_end_point(self) -> Optional[Point]:
        """Get the ending point of the path."""
        return self.curves[-1].p_end if self.curves else None

    def length(self) -> float:
        """Get the total length of the path."""
        return sum(curve.length() for curve in self.curves) if self.curves else 0.0

    def add_curve(self, curve: Curve):
        """Add a curve to the path."""
        self.curves.append(curve)

    def to_polyline(self) -> List[float]:
        """
        Convert path to polyline format (flat list of [t, x, y] tuples).
        Format: [t0, x0, y0, t1, x1, y1, ...]
        """
        polyline = []
        for i, curve in enumerate(self.curves):
            if i == 0:
                polyline.extend([0, curve.p_start.x, curve.p_start.y])

            # Only add if not too close to previous
            if (
                len(polyline) == 0
                or np.linalg.norm(
                    np.array([curve.p_start.x, curve.p_start.y])
                    - np.array(polyline[-2:])
                )
                > 1
            ):
                polyline.extend([0, curve.p_start.x, curve.p_start.y])

        # Add end point
        if self.curves:
            end = self.curves[-1].p_end
            if (
                len(polyline) == 0
                or np.linalg.norm(np.array([end.x, end.y]) - np.array(polyline[-2:]))
                > 1
            ):
                polyline.extend([0, end.x, end.y])

        return polyline


class Sketch:
    """Represents a sketch consisting of multiple paths."""

    def __init__(
        self,
        width: float = 800,
        height: float = 800,
        paths: Optional[List[Path]] = None,
    ):
        """
        Initialize a Sketch.

        Args:
            width: Canvas width
            height: Canvas height
            paths: List of Path objects
        """
        self.width = float(width)
        self.height = float(height)
        self.paths = paths if paths is not None else []

    def __repr__(self):
        return f"Sketch({self.width}x{self.height}, {len(self.paths)} paths)"

    def __len__(self):
        return len(self.paths)

    def add_path(self, path: Path):
        """Add a path to the sketch."""
        self.paths.append(path)

    def get_paths_as_polylines(self) -> List[List[float]]:
        """Get all paths converted to polyline format."""
        return [path.to_polyline() for path in self.paths if path.curves]


def create_sketch_from_polylines(
    polylines: List[List[float]], width: float = 800, height: float = 800
) -> Sketch:
    """
    Create a Sketch from a list of polylines.

    Args:
        polylines: List of polylines in [t, x, y, ...] format
        width: Canvas width
        height: Canvas height

    Returns:
        Sketch object
    """
    sketch = Sketch(width=width, height=height)

    for polyline in polylines:
        if len(polyline) < 6:  # Need at least 2 points
            continue

        path = Path()
        for i in range(1, len(polyline) // 3):
            p_start = Point(polyline[3 * i - 2], polyline[3 * i - 1])
            p_end = Point(polyline[3 * i + 1], polyline[3 * i + 2])
            path.add_curve(Curve(p_start, p_end))

        sketch.add_path(path)

    return sketch


def create_sketch_from_svg(svg_file: str) -> Sketch:
    """
    Create a Sketch from an SVG file.

    Extracts path and line elements from SVG and converts them to Sketch.

    Args:
        svg_file: Path to the SVG file

    Returns:
        Sketch object with paths extracted from SVG
    """
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        raise ImportError("xml module is required to parse SVG files")

    # Parse SVG file
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Extract viewBox or use default size
    viewBox = root.get("viewBox")
    if viewBox:
        parts = viewBox.split()
        width = float(parts[2])
        height = float(parts[3])
    else:
        width = _parse_svg_number(root.get("width", 800))
        height = _parse_svg_number(root.get("height", 800))

    sketch = Sketch(width=width, height=height)

    # Extract all path elements
    for path_elem in root.findall(".//{*}path"):
        d = path_elem.get("d")
        if d:
            points = _parse_svg_path(d)
            if len(points) >= 2:
                path = Path()
                for i in range(len(points) - 1):
                    path.add_curve(Curve(points[i], points[i + 1]))
                sketch.add_path(path)

    # Extract line elements
    for line_elem in root.findall(".//{*}line"):
        x1 = float(line_elem.get("x1", 0))
        y1 = float(line_elem.get("y1", 0))
        x2 = float(line_elem.get("x2", 0))
        y2 = float(line_elem.get("y2", 0))

        path = Path()
        path.add_curve(Curve(Point(x1, y1), Point(x2, y2)))
        sketch.add_path(path)

    # Extract polyline elements
    for polyline_elem in root.findall(".//{*}polyline"):
        points_str = polyline_elem.get("points")
        if points_str:
            points = _parse_svg_points(points_str)
            if len(points) >= 2:
                path = Path()
                for i in range(len(points) - 1):
                    path.add_curve(Curve(points[i], points[i + 1]))
                sketch.add_path(path)

    # Extract polygon elements
    for polygon_elem in root.findall(".//{*}polygon"):
        points_str = polygon_elem.get("points")
        if points_str:
            points = _parse_svg_points(points_str)
            if len(points) >= 2:
                path = Path()
                for i in range(len(points) - 1):
                    path.add_curve(Curve(points[i], points[i + 1]))
                sketch.add_path(path)

    return sketch


def _parse_svg_number(value) -> float:
    """Parse an SVG numeric attribute that may include units like px."""
    import re

    match = re.search(r"-?\d+\.?\d*|-?\.\d+", str(value))
    return float(match.group(0)) if match else 800.0


def _parse_svg_path(d: str) -> List[Point]:
    """
    Parse SVG path d attribute and return list of points.
    Simplified parser that handles M (move), L (line), and Z (close) commands.

    Args:
        d: SVG path d attribute string

    Returns:
        List of Point objects
    """
    points = []
    current_pos = Point(0, 0)
    subpath_start = None

    # Split by command letters
    import re

    commands = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]", d)
    parts = re.split(r"[MmLlHhVvCcSsQqTtAaZz]", d)

    for i, cmd in enumerate(commands):
        if i + 1 >= len(parts):
            break

        coords_str = parts[i + 1].strip()
        if not coords_str:
            continue

        # Parse coordinates
        coords = re.findall(r"-?\d+\.?\d*|-?\.\d+", coords_str)
        coords = [float(c) for c in coords]

        if cmd in ["M", "m"]:  # Move; extra pairs are implicit lines.
            if len(coords) >= 2:
                x, y = coords[0], coords[1]
                if cmd == "m":  # Relative
                    current_pos = Point(current_pos.x + x, current_pos.y + y)
                else:  # Absolute
                    current_pos = Point(x, y)
                points.append(current_pos)
                subpath_start = current_pos

                for j in range(2, len(coords), 2):
                    if j + 1 < len(coords):
                        x, y = coords[j], coords[j + 1]
                        if cmd == "m":
                            current_pos = Point(current_pos.x + x, current_pos.y + y)
                        else:
                            current_pos = Point(x, y)
                        points.append(current_pos)

        elif cmd in ["L", "l"]:  # Line
            for j in range(0, len(coords), 2):
                if j + 1 < len(coords):
                    x, y = coords[j], coords[j + 1]
                    if cmd == "l":  # Relative
                        current_pos = Point(current_pos.x + x, current_pos.y + y)
                    else:  # Absolute
                        current_pos = Point(x, y)
                    points.append(current_pos)

        elif cmd in ["H", "h"]:  # Horizontal line
            for x in coords:
                current_pos = (
                    Point(current_pos.x + x, current_pos.y)
                    if cmd == "h"
                    else Point(x, current_pos.y)
                )
                points.append(current_pos)

        elif cmd in ["V", "v"]:  # Vertical line
            for y in coords:
                current_pos = (
                    Point(current_pos.x, current_pos.y + y)
                    if cmd == "v"
                    else Point(current_pos.x, y)
                )
                points.append(current_pos)

        elif cmd in ["C", "c"]:  # Cubic Bezier; approximate by its endpoint.
            step = 6
            for j in range(0, len(coords), step):
                if j + 5 < len(coords):
                    x, y = coords[j + 4], coords[j + 5]
                    current_pos = (
                        Point(current_pos.x + x, current_pos.y + y)
                        if cmd == "c"
                        else Point(x, y)
                    )
                    points.append(current_pos)

        elif cmd in [
            "S",
            "s",
            "Q",
            "q",
        ]:  # Smooth cubic/quadratic; approximate by endpoint.
            step = 4
            for j in range(0, len(coords), step):
                if j + 3 < len(coords):
                    x, y = coords[j + 2], coords[j + 3]
                    current_pos = (
                        Point(current_pos.x + x, current_pos.y + y)
                        if cmd.islower()
                        else Point(x, y)
                    )
                    points.append(current_pos)

        elif cmd in ["T", "t"]:  # Smooth quadratic; approximate by endpoint.
            for j in range(0, len(coords), 2):
                if j + 1 < len(coords):
                    x, y = coords[j], coords[j + 1]
                    current_pos = (
                        Point(current_pos.x + x, current_pos.y + y)
                        if cmd == "t"
                        else Point(x, y)
                    )
                    points.append(current_pos)

        elif cmd in ["A", "a"]:  # Arc; approximate by endpoint.
            step = 7
            for j in range(0, len(coords), step):
                if j + 6 < len(coords):
                    x, y = coords[j + 5], coords[j + 6]
                    current_pos = (
                        Point(current_pos.x + x, current_pos.y + y)
                        if cmd == "a"
                        else Point(x, y)
                    )
                    points.append(current_pos)

        elif cmd == "Z" or cmd == "z":  # Close path
            if subpath_start is not None and current_pos != subpath_start:
                current_pos = subpath_start
                points.append(current_pos)

    return points


def _parse_svg_points(points_str: str) -> List[Point]:
    """
    Parse SVG points attribute (for polyline/polygon).

    Args:
        points_str: SVG points attribute string

    Returns:
        List of Point objects
    """
    import re

    coords = re.findall(r"-?\d+\.?\d*|-?\.\d+", points_str)
    coords = [float(c) for c in coords]

    points = []
    for i in range(0, len(coords), 2):
        if i + 1 < len(coords):
            points.append(Point(coords[i], coords[i + 1]))

    return points
