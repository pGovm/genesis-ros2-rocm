# Notes: open items

Findings for the open questions in the project handoff. Each item records what was tested,
on which versions, and the result.

## Test environment

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU (Blackwell, `sm_120`) |
| Host driver | 595.99.02 |
| Host | Ubuntu 24.04, Docker 29.10.0, Docker Compose v5.8.0 |
| Image | `genesis-ros2:cuda-govind` (`ros:jazzy-ros-base`, Python 3.12) |
| PyTorch | 2.14.1+cu130 (CUDA 13.0) |
| Genesis | `genesis-world` 1.4.7 |

## 1. Does Genesis run on Blackwell (`sm_120`)?

**Result: yes.** Tested 2026-11-22.

**PyTorch.** Inside the container:

```
torch.cuda.get_arch_list()  -> ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120']
torch.cuda.is_available()   -> True
```

**Genesis.** [`scenes/smoke_test.py`](../scenes/smoke_test.py) drops a 0.2 m box onto a plane
with `gs.init(backend=gs.gpu)`. It checks that the box comes to rest at z = 0.1.

```
docker compose run --rm sim python scenes/smoke_test.py
```

| Measure | Value |
|---|---|
| `scene.build()` | 73.7 s |
| 500 steps (dt = 0.01) | 0.17 s (about 3000 steps/s) |
| Final box height | 0.100 (expected 0.1) |

**Notes**
- The build time is probably dominated by first-time kernel compilation. Not yet checked:
  whether Genesis caches compiled kernels, and whether that cache survives across containers
  (`docker compose run --rm` starts from a fresh container each time).
- The CPU fallback (`--cpu`) wasn't needed and hasn't been tested.
- Only the headless path was tested. The viewer (`--vis`) belongs to item 4.

## 2. gs_ros: Jazzy, `use_sim_time` / `/clock`, loading our URDFs

Not yet tested.

## 3. Does Quadrants need anything beyond the host driver and Container Toolkit?

Not yet tested. Item 1 shows that the GPU backend works with only the driver and the
Container Toolkit on the host.

## 4. Display forwarding for RViz and the Genesis viewer (X11 vs Wayland)

Not yet tested.

## 5. Multi-robot / namespacing in gs_ros

Not yet tested.

## 6. (Deferred) Genesis ROCm build on the target AMD GPU

Deferred until the CUDA development path works.
