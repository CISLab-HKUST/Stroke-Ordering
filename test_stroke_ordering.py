"""
Unit tests for stroke_ordering_standalone library.

Run with: python test_stroke_ordering.py
"""

import sys
import os

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
from data_structures import Point, Curve, Path, Sketch, create_sketch_from_polylines
from animated_drawer import AnimatedDrawer
from compute_cost import cost_individual, cost_transition
from direction import determine_direction


def test_point():
    """Test Point class."""
    print("Testing Point class...")
    p1 = Point(0, 0)
    p2 = Point(3, 4)

    assert p1.x == 0
    assert p1.y == 0
    assert p2.x == 3
    assert p2.y == 4

    # Test distance calculation
    distance = p1.distance_to(p2)
    assert abs(distance - 5.0) < 1e-6, f"Expected 5.0, got {distance}"

    print("  ✓ Point class tests passed")


def test_curve():
    """Test Curve class."""
    print("Testing Curve class...")
    p1 = Point(0, 0)
    p2 = Point(3, 4)

    curve = Curve(p1, p2)
    assert curve.p_start == p1
    assert curve.p_end == p2

    length = curve.length()
    assert abs(length - 5.0) < 1e-6, f"Expected 5.0, got {length}"

    print("  ✓ Curve class tests passed")


def test_path():
    """Test Path class."""
    print("Testing Path class...")
    path = Path()

    assert len(path) == 0

    curve1 = Curve(Point(0, 0), Point(1, 1))
    curve2 = Curve(Point(1, 1), Point(2, 0))

    path.add_curve(curve1)
    path.add_curve(curve2)

    assert len(path) == 2
    assert path.get_start_point() == Point(0, 0)
    assert path.get_end_point() == Point(2, 0)

    print("  ✓ Path class tests passed")


def test_sketch():
    """Test Sketch class."""
    print("Testing Sketch class...")
    sketch = Sketch(width=800, height=600)

    assert sketch.width == 800
    assert sketch.height == 600
    assert len(sketch) == 0

    path1 = Path()
    path1.add_curve(Curve(Point(0, 0), Point(100, 100)))
    sketch.add_path(path1)

    assert len(sketch) == 1

    print("  ✓ Sketch class tests passed")


def test_polyline_conversion():
    """Test polyline format conversion."""
    print("Testing polyline conversion...")

    polylines = [
        [0, 0, 0, 0, 100, 100],
        [0, 100, 100, 0, 200, 0],
    ]

    sketch = create_sketch_from_polylines(polylines, width=800, height=800)
    assert len(sketch) == 2
    assert len(sketch.paths[0]) == 1

    print("  ✓ Polyline conversion tests passed")


def test_direction_determination():
    """Test stroke direction determination."""
    print("Testing direction determination...")

    # Test with no previous point
    start = Point(0, 0)
    end = Point(100, 100)
    direction = determine_direction(None, start, end)
    assert isinstance(direction, (bool, int))

    # Test with previous point
    prev = Point(-50, -50)
    direction = determine_direction(prev, start, end)
    assert isinstance(direction, (bool, int))

    print("  ✓ Direction determination tests passed")


def test_cost_functions():
    """Test cost computation functions."""
    print("Testing cost functions...")

    # Create simple polylines
    polyline1 = [0, 0, 0, 0, 100, 100, 0, 200, 0]
    polyline2 = [0, 200, 100, 0, 300, 200, 0, 400, 0]

    # Test individual cost
    cost = cost_individual(polyline1)
    assert isinstance(cost, float)
    assert cost >= 0

    # Test transition cost
    prox, col = cost_transition(polyline1, polyline2)
    assert isinstance(prox, float)
    assert isinstance(col, float)
    assert prox >= 0
    assert col >= 0

    print("  ✓ Cost function tests passed")


def test_animated_drawer_simple():
    """Test AnimatedDrawer with a simple sketch."""
    print("Testing AnimatedDrawer with simple sketch...")

    # Create simple 2-stroke sketch
    sketch = Sketch(width=800, height=800)

    path1 = Path()
    path1.add_curve(Curve(Point(100, 100), Point(200, 200)))
    sketch.add_path(path1)

    path2 = Path()
    path2.add_curve(Curve(Point(200, 200), Point(300, 100)))
    sketch.add_path(path2)

    # Run ordering
    drawer = AnimatedDrawer(max_k=2, verbose=False)
    result = drawer.get_stroke_order(sketch)

    assert result is not None
    assert "solution" in result
    assert "cost" in result
    assert "directions" in result

    assert len(result["solution"]) == 2
    assert len(result["directions"]) == 2

    print("  ✓ AnimatedDrawer simple test passed")


def test_animated_drawer_run():
    """Test AnimatedDrawer.run() method."""
    print("Testing AnimatedDrawer.run() method...")

    sketch = Sketch(width=800, height=800)

    for i in range(3):
        path = Path()
        path.add_curve(Curve(Point(100 + i * 50, 100), Point(150 + i * 50, 150)))
        sketch.add_path(path)

    drawer = AnimatedDrawer(max_k=2, verbose=False)
    ordered_sketch = drawer.run(sketch)

    assert ordered_sketch is not None
    assert len(ordered_sketch) == len(sketch)

    print("  ✓ AnimatedDrawer.run() test passed")


def test_empty_sketch():
    """Test handling of empty or single-path sketches."""
    print("Testing edge cases...")

    # Empty sketch
    sketch = Sketch(width=800, height=800)
    drawer = AnimatedDrawer(verbose=False)
    result = drawer.get_stroke_order(sketch)

    assert result is not None
    assert result["solution"] == []

    # Single path sketch
    sketch.add_path(Path())
    result = drawer.get_stroke_order(sketch)

    assert result is not None
    assert len(result["solution"]) <= 1

    print("  ✓ Edge case tests passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Running Stroke Ordering Standalone Tests")
    print("=" * 70 + "\n")

    tests = [
        test_point,
        test_curve,
        test_path,
        test_sketch,
        test_polyline_conversion,
        test_direction_determination,
        test_cost_functions,
        test_animated_drawer_simple,
        test_animated_drawer_run,
        test_empty_sketch,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    import sys

    success = run_all_tests()
    sys.exit(0 if success else 1)
