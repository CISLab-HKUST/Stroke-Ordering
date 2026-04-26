"""
Stroke Ordering Standalone - An independent stroke ordering library.

This library provides stroke ordering optimization for sketches without
any dependencies on the main SketchKit framework.

Main components:
- data_structures: Point, Curve, Path, Sketch classes
- compute_cost: Cost computation functions
- direction: Stroke direction determination
- tsp_bnb: TSP solving using branch-and-bound
- animated_drawer: Main AnimatedDrawer class
"""

from .data_structures import (
    Point,
    Curve,
    Path,
    Sketch,
    create_sketch_from_polylines,
    create_sketch_from_svg,
)
from .animated_drawer import AnimatedDrawer
from .compute_cost import (
    cost_individual,
    cost_transition,
    compute_T_junctions,
    stroke_length,
    curvatures,
)
from .direction import determine_direction
from .export import save_animation, save_ordered_svg

__version__ = "1.0.0"
__all__ = [
    "Point",
    "Curve",
    "Path",
    "Sketch",
    "create_sketch_from_polylines",
    "create_sketch_from_svg",
    "AnimatedDrawer",
    "cost_individual",
    "cost_transition",
    "compute_T_junctions",
    "stroke_length",
    "curvatures",
    "determine_direction",
    "save_animation",
    "save_ordered_svg",
]
