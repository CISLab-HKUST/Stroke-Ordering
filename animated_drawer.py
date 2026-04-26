"""
Main stroke ordering implementation: AnimatedDrawer
Optimizes the drawing sequence of strokes in a sketch.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from operator import itemgetter

try:
    from .data_structures import Sketch
    from .compute_cost import cost_individual, cost_transition, compute_T_junctions
    from .direction import determine_direction
    from .tsp_bnb import solve_tsp
except ImportError:  # Allow running scripts directly from this folder.
    from data_structures import Sketch
    from compute_cost import cost_individual, cost_transition, compute_T_junctions
    from direction import determine_direction
    from tsp_bnb import solve_tsp


class AnimatedDrawer:
    """
    Stroke ordering algorithm based on "Animated Construction of Line Drawings".

    This method analyzes stroke relationships, computes transition costs between strokes,
    and determines the optimal drawing order using a branch-and-bound algorithm.
    """

    def __init__(
        self,
        max_k: int = 4,
        w: float = 0.1111111,
        verbose: bool = False,
    ):
        """
        Initialize the AnimatedDrawer.

        Args:
            max_k: Maximum number of closest strokes to consider for each stroke
            w: Weight parameter for combining proximity (1-w) and collinearity (w) costs
            verbose: Whether to print progress information
        """
        self.max_k = max_k
        self.w = w
        self.verbose = verbose

    def run(self, sketch: Sketch) -> Sketch:
        """
        Run the stroke ordering algorithm.

        Args:
            sketch: Input Sketch object with unordered strokes

        Returns:
            Sketch with strokes reordered according to the optimized drawing sequence
        """
        result = self._animated_drawing(sketch)

        if result is None:
            # Return original sketch if ordering failed
            return sketch

        # Reorder paths according to solution
        paths = [sketch.paths[i] for i in result["solution"]]
        ret_sketch = Sketch(height=sketch.height, width=sketch.width, paths=paths)
        return ret_sketch

    def get_stroke_order(self, sketch: Sketch) -> Dict[str, Any]:
        """
        Get the stroke ordering information.

        Args:
            sketch: Input Sketch object

        Returns:
            Dictionary containing:
                - 'solution': list of path indices in order
                - 'cost': total cost of the ordering
                - 'directions': list of booleans indicating stroke direction
        """
        return self._animated_drawing(sketch)

    def _get_cost_bi(self, cost_bi: List[List[float]], i: int, j: int) -> float:
        """
        Get the cost between two strokes from a bidirectional cost matrix.

        Args:
            cost_bi: Bidirectional cost matrix (upper triangular)
            i: Index of first stroke
            j: Index of second stroke

        Returns:
            Cost value
        """
        if i == j:
            return 0
        else:
            ii = min(i, j)
            jj = max(i, j)
            return cost_bi[ii][jj - ii - 1]

    def _animated_drawing(self, sketch: Sketch) -> Optional[Dict[str, Any]]:
        """
        Create an animated drawing from a static sketch.

        Args:
            sketch: The static sketch to animate

        Returns:
            Dictionary with optimization result or None if failed
        """
        if not sketch.paths or len(sketch.paths) < 2:
            # Single path or empty sketch
            return {
                "solution": list(range(len(sketch.paths))),
                "cost": 0,
                "directions": [True] * len(sketch.paths),
            }

        max_k = self.max_k
        w = self.w
        strokes_txy = []
        cost_uni = []

        # Convert paths to polyline format and compute individual costs
        for path in sketch.paths:
            if path.curves is None or len(path.curves) < 1:
                continue

            polyline_path = []
            for curve in path.curves:
                if len(polyline_path) == 0:
                    polyline_path.append(0)
                    polyline_path.append(curve.p_start.x)
                    polyline_path.append(curve.p_start.y)
                elif (
                    np.linalg.norm(
                        np.array(polyline_path[-2:])
                        - np.array([curve.p_start.x, curve.p_start.y])
                    )
                    > 1
                ):
                    polyline_path.append(0)
                    polyline_path.append(curve.p_start.x)
                    polyline_path.append(curve.p_start.y)

            if (
                np.linalg.norm(
                    np.array(polyline_path[-2:])
                    - np.array([path.curves[-1].p_end.x, path.curves[-1].p_end.y])
                )
                > 1
            ):
                polyline_path.append(0)
                polyline_path.append(path.curves[-1].p_end.x)
                polyline_path.append(path.curves[-1].p_end.y)

            strokes_txy.append(polyline_path)
            cost = cost_individual(polyline_path)
            cost_uni.append(cost)

        if len(strokes_txy) < 2:
            # Insufficient strokes to order
            return {
                "solution": list(range(len(strokes_txy))),
                "cost": 0,
                "directions": [True] * len(strokes_txy),
            }

        # Compute transition costs
        cost_bi_pro = []
        cost_bi_col = []

        for sid1 in range(len(strokes_txy) - 1):
            cost_bi_pro_row = []
            cost_bi_col_row = []
            for sid2 in range(sid1 + 1, len(strokes_txy)):
                pro, col = cost_transition(strokes_txy[sid1], strokes_txy[sid2])
                cost_bi_pro_row.append(pro)
                cost_bi_col_row.append(col)
            cost_bi_pro.append(cost_bi_pro_row)
            cost_bi_col.append(cost_bi_col_row)

        # Detect T-junctions
        T_junctions = []
        for sid1 in range(len(strokes_txy)):
            for sid2 in range(len(strokes_txy)):
                if sid1 != sid2:
                    c = compute_T_junctions(strokes_txy[sid1], strokes_txy[sid2])
                    if c > 0:
                        T_junctions.append([sid1, sid2])

        # Build k-NN graph
        vertex_pair = []
        edge_weight = []
        n = len(cost_uni)

        neighbors_to_consider = min(max_k, n - 1)

        for i in range(n):

            all_pro_for_i = []
            for j in range(n):
                if j != i:
                    all_pro_for_i.append(self._get_cost_bi(cost_bi_pro, i, j))
                else:
                    all_pro_for_i.append(999999999)

            for k in range(neighbors_to_consider):
                # get the index of the k-th closest stroke
                j = sorted(enumerate(all_pro_for_i), key=itemgetter(1))[k][0]

                if [i, j] in T_junctions:
                    # add j, i
                    vertex_pair.append((j, i))
                    edge_weight.append(
                        w * self._get_cost_bi(cost_bi_pro, j, i)
                        + (1 - w) * self._get_cost_bi(cost_bi_col, j, i)
                    )
                elif [j, i] in T_junctions:
                    # add i, j
                    vertex_pair.append((i, j))
                    edge_weight.append(
                        w * self._get_cost_bi(cost_bi_pro, i, j)
                        + (1 - w) * self._get_cost_bi(cost_bi_col, i, j)
                    )
                else:
                    # add both directions
                    vertex_pair.append((j, i))
                    edge_weight.append(
                        w * self._get_cost_bi(cost_bi_pro, j, i)
                        + (1 - w) * self._get_cost_bi(cost_bi_col, j, i)
                    )
                    vertex_pair.append((i, j))
                    edge_weight.append(
                        w * self._get_cost_bi(cost_bi_pro, i, j)
                        + (1 - w) * self._get_cost_bi(cost_bi_col, i, j)
                    )

        weight_binary = {}
        for i in range(len(vertex_pair)):
            weight_binary[str(vertex_pair[i][0]) + "," + str(vertex_pair[i][1])] = (
                edge_weight[i]
            )

        weight_unary = cost_uni

        # Solve TSP using branch-and-bound
        result = solve_tsp(weight_unary, weight_binary, verbose=self.verbose)

        if result is None or "solution" not in result:
            print("Warning: Failed to find optimal stroke order")
            return None

        # Determine stroke directions
        directions = []
        for i in range(len(result["solution"])):
            index = result["solution"][i]
            if i == 0:
                prev = None
            elif directions[-1]:
                prev = sketch.paths[result["solution"][i - 1]].curves[-1].p_end
            else:
                prev = sketch.paths[result["solution"][i - 1]].curves[0].p_start

            current_path = sketch.paths[index]
            start = current_path.curves[0].p_start
            end = current_path.curves[-1].p_end

            directions.append(determine_direction(prev, start, end))

        result["directions"] = directions

        if self.verbose:
            print(f"Optimal solution: {result['solution']}")
            print(f"Cost: {result['cost']}")
            print(f"Directions: {result['directions']}")

        return result
