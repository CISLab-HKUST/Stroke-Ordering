"""
Direction determination for strokes.
Determines whether a stroke should be drawn from start to end or end to start.
"""

from typing import Optional
import numpy as np

try:
    from .data_structures import Point
except ImportError:  # Allow running scripts directly from this folder.
    from data_structures import Point


def determine_direction(prev: Optional[Point], start: Point, end: Point) -> bool:
    """
    Determine the direction of the stroke.

    Args:
        prev: The previous stroke's endpoint (None if this is the first stroke)
        start: The start point of the current stroke
        end: The end point of the current stroke

    Returns:
        True if drawing from start to end is preferred, False otherwise
    """

    # Convert to float64 to avoid type issues
    p0 = np.array([start.x, start.y], dtype=np.float64)
    p1 = np.array([end.x, end.y], dtype=np.float64)

    # Case 1: Has previous stroke -> prioritize "continuous contact on paper"
    if prev is not None:
        pp = np.array([prev.x, prev.y], dtype=np.float64)
        d0 = np.linalg.norm(p0 - pp)
        d1 = np.linalg.norm(p1 - pp)
        if d0 - d1 < -1e-1:
            return True
        elif d0 - d1 > 1e-1:
            return False

    # Case 2: First stroke -> use default habit
    vec = p1 - p0
    dx, dy = vec
    tan = abs(dy / (dx + 1e-6))

    if tan > np.tan(np.pi / 12):
        # top to bottom
        return True if dy < 0 else False
    else:
        # left to right
        return True if dx > 0 else False
