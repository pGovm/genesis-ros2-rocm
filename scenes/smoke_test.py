"""Minimal headless Genesis scene: a box dropped on a plane.

Usage (inside the container):
    python scenes/smoke_test.py            # GPU backend
    python scenes/smoke_test.py --cpu      # CPU fallback
    python scenes/smoke_test.py --vis      # open the Genesis viewer (needs X11)
"""

import argparse
import time

import genesis as gs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", action="store_true", help="use gs.cpu instead of gs.gpu")
    parser.add_argument("--vis", action="store_true", help="show the viewer")
    parser.add_argument("--steps", type=int, default=500)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="warning")

    scene = gs.Scene(sim_options=gs.options.SimOptions(dt=0.01), show_viewer=args.vis)
    scene.add_entity(gs.morphs.Plane())
    box = scene.add_entity(gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0.0, 0.0, 1.0)))

    t0 = time.perf_counter()
    scene.build()
    print(f"build: {time.perf_counter() - t0:.1f}s")

    t0 = time.perf_counter()
    for _ in range(args.steps):
        scene.step()
    dt = time.perf_counter() - t0

    z = float(box.get_pos()[2])
    print(f"{args.steps} steps in {dt:.2f}s ({args.steps / dt:.0f} steps/s); box z = {z:.3f}")
    # Box (half-height 0.1) should have fallen from z=1.0 and come to rest on the plane.
    assert abs(z - 0.1) < 0.02, f"unexpected resting height {z}"
    print("OK")


if __name__ == "__main__":
    main()
