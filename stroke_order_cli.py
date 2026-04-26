"""
Command line interface for SVG stroke ordering.
"""

import argparse
from pathlib import Path

try:
    from .animated_drawer import AnimatedDrawer
    from .data_structures import create_sketch_from_svg
    from .export import save_animation, save_ordered_svg
except ImportError:  # Allow running as: python stroke_order_cli.py input.svg
    from animated_drawer import AnimatedDrawer
    from data_structures import create_sketch_from_svg
    from export import save_animation, save_ordered_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Order SVG strokes and export animation files."
    )
    parser.add_argument("input_svg", help="Input SVG file.")
    parser.add_argument(
        "-o", "--output-dir", default="outputs", help="Directory for generated files."
    )
    parser.add_argument(
        "--max-k", type=int, default=4, help="Nearest-neighbor graph degree."
    )
    parser.add_argument(
        "--w",
        type=float,
        default=0.1111111,
        help="Proximity/collinearity blend weight.",
    )
    parser.add_argument("--fps", type=int, default=12, help="Animation frame rate.")
    parser.add_argument(
        "--frames-per-stroke",
        type=int,
        default=8,
        help="Frames used to draw each stroke.",
    )
    parser.add_argument(
        "--no-gif", action="store_true", help="Do not write GIF output."
    )
    parser.add_argument(
        "--no-mp4", action="store_true", help="Do not write MP4 output."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print branch-and-bound progress."
    )
    parser.add_argument(
        "--show-labels",
        action="store_true",
        help="Draw red numeric labels in the ordered SVG.",
    )
    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Add data-stroke-order and data-direction attributes to SVG paths.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_svg = Path(args.input_svg)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sketch = create_sketch_from_svg(str(input_svg))
    drawer = AnimatedDrawer(max_k=args.max_k, w=args.w, verbose=args.verbose)
    result = drawer.get_stroke_order(sketch)
    if not result:
        raise RuntimeError("Failed to compute stroke ordering.")

    stem = input_svg.stem
    ordered_svg = output_dir / f"{stem}_ordered.svg"
    save_ordered_svg(
        sketch,
        result,
        str(ordered_svg),
        show_labels=args.show_labels,
        include_metadata=args.include_metadata,
    )

    gif_file = output_dir / f"{stem}.gif"
    mp4_file = output_dir / f"{stem}.mp4"
    if not args.no_gif:
        save_animation(sketch, result, str(gif_file), args.fps, args.frames_per_stroke)
    if not args.no_mp4:
        save_animation(sketch, result, str(mp4_file), args.fps, args.frames_per_stroke)

    print(f"Loaded {len(sketch.paths)} strokes from {input_svg}")
    print(f"Order: {result['solution']}")
    print(f"Directions: {result['directions']}")
    print(f"Cost: {result['cost']:.6f}")
    print(f"Wrote: {ordered_svg}")
    if not args.no_gif:
        print(f"Wrote: {gif_file}")
    if not args.no_mp4:
        print(f"Wrote: {mp4_file}")


if __name__ == "__main__":
    main()
