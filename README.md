# gs-ros2-rocm

An Isaac Sim-like robot simulation environment for ROS 2 that targets **AMD ROCm**.
[Genesis](https://github.com/Genesis-Embodied-AI/Genesis) is the physics engine, and the
[`gs_ros`](https://github.com/vybhav-ibr/genesis_ros) bridge connects it to ROS 2 topics,
services, `ros2_control` and RViz.

Everything runs in Docker. The host needs no ROS 2 installation.

## Status

| Part | State |
|---|---|
| CUDA container (development on NVIDIA) | Builds; GPU and bridge testing in progress |
| ROCm container (target on AMD) | Planned, not started |
| Results of open questions | Recorded in [docs/notes.md](docs/notes.md) |

Development currently happens on an NVIDIA RTX 5060 (Blackwell, `sm_120`) using the CUDA
variant. The ROCm variant will reuse the same ROS 2 and bridge layers and change only the
GPU-specific parts.

## Requirements

**Host**
- Linux (developed on Ubuntu 24.04)
- Docker Engine with Docker Compose v2.20 or newer (needed for `include:` in the compose file)
- An X server for GUI apps. On Wayland desktops, XWayland provides this.

**For the CUDA variant**
- An NVIDIA driver supporting CUDA 13.0 or newer
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

You don't need a CUDA toolkit on the host. PyTorch's wheels bundle the CUDA runtime, and the
container gets the driver from the host at run time.

## Quick start

```bash
# 1. Clone with submodules (the bridge and its nested simulation_interfaces)
git clone --recurse-submodules <repo-url> gs-ros2-rocm
cd gs-ros2-rocm

# 2. Write .env with your username/UID/GID and allow containers to use the display.
#    Rerun after each login: the display permission resets.
./scripts/host_setup.sh

# 3. Build the image (first build downloads several GB)
docker compose build

# 4. Start the container and open a shell in it
docker compose up -d
docker compose exec sim bash
```

Inside the container, build the ROS 2 workspace:

```bash
colcon build --symlink-install
source install/setup.bash
```

New shells source ROS 2 and the workspace automatically. Stop the container with
`docker compose down`.

If you already cloned without `--recurse-submodules`, run:

```bash
git submodule update --init --recursive
```

## Checking the GPU

```bash
docker compose run --rm sim bash -c '
  id
  python -c "import torch; print(torch.__version__, torch.cuda.get_arch_list(), torch.cuda.is_available())"
  nvidia-smi
'
```

Expected:
- `uid=` and `gid=` match your host user
- the arch list contains your GPU's architecture (`sm_120` for RTX 50-series)
- `is_available()` prints `True`

If Genesis fails on the GPU, use `gs.init(backend=gs.cpu)` to keep working on the bridge
while the GPU issue is investigated.

## Repository layout

```
.
├── docker-compose.yml           # entry point; includes the variant below with ./.env
├── docker/
│   ├── Dockerfile               # ROS 2 Jazzy + Python venv (PyTorch, Genesis) + your user
│   └── docker-compose.cuda.yml  # CUDA/NVIDIA service definition
├── scripts/
│   └── host_setup.sh            # writes .env, grants X11 access
├── src/                         # colcon workspace
│   └── genesis_ros/             # submodule: gs_ros, gs_ros_interfaces, demos
├── scenes/                      # standalone Genesis test scripts
└── docs/                        # notes and test results
```

## How the container is set up

**Base image.** `ros:jazzy-ros-base` (Ubuntu 24.04, Python 3.12), with ROS packages added
individually: RViz, `robot_state_publisher`, `xacro`, `ros2_control` and `ros2_controllers`.
Dependencies of the packages in `src/` are installed with `rosdep` at build time.

**Python.** PyTorch and `genesis-world` are installed into a venv at `/opt/venv`. The venv is
created with `--system-site-packages`, so ROS 2's `rclpy` is visible from it. Build arguments
in `docker/docker-compose.cuda.yml` choose the versions:
- `TORCH_INDEX_URL` selects the PyTorch wheel index (default `cu130`)
- `GENESIS_VERSION` pins Genesis (empty installs the latest release)

**Your user.** The image creates a user with your host username, UID and GID, with
passwordless `sudo`. `scripts/host_setup.sh` writes these to `.env`, and compose passes them
in as build arguments. Files the container creates in the mounted repo (`build/`,
`install/`, `log/`) are then owned by you on the host. Each user builds their own image,
tagged `genesis-ros2:cuda-<username>`.

The layers that don't depend on the user (apt packages, PyTorch, Genesis, rosdep) come first
in the Dockerfile, so they're cached once and shared between users.

**Workspace.** The repo is bind-mounted at `/home/<username>/genesis_ws`. Edits on the host
appear in the container immediately.

**Networking and display.**
- `network_mode: host` and `ipc: host` let ROS 2 discovery and shared-memory transport work
  without port mapping.
- GUI apps reach the host's X server through `/tmp/.X11-unix`.
- `NVIDIA_DRIVER_CAPABILITIES=all` gives the container OpenGL as well as CUDA, which the
  Genesis viewer and RViz need.

## Day-to-day use

| Task | Command |
|---|---|
| Open another shell | `docker compose exec sim bash` |
| Run one command | `docker compose exec sim bash -ic 'ros2 topic list'` |
| Install a Python package temporarily | `sudo /opt/venv/bin/pip install <pkg>` |
| Apply Dockerfile changes | `docker compose build && docker compose up -d` |
| Root shell | `docker compose exec -u root sim bash` |

Notes:
- `bash -ic` is needed for one-off commands. Plain `exec` doesn't run an interactive shell,
  so ROS 2 isn't sourced.
- Packages installed with `pip` are lost when the container is recreated. Add anything
  permanent to the Dockerfile.
- `docker compose restart` doesn't pick up a rebuilt image. Use `up -d`, which recreates the
  container.

## Troubleshooting

**`required variable USERNAME is missing a value`.** `.env` is missing or empty. Run
`./scripts/host_setup.sh`.

**GUI apps don't open (`could not connect to display`).** The X11 permission resets on
logout. Rerun `./scripts/host_setup.sh`.

**Builds end with a long "sending tarball" step.** The active buildx builder uses the
`docker-container` driver, so the image must be copied into Docker after every build. Switch
to the built-in builder with `docker buildx use default`.

**`rosdep install` fails during the build.** The error names the dependency it couldn't
resolve. Either install it another way (for example, add its source repo under `src/`) or
skip it with `--skip-keys <key>` in the Dockerfile.

**Disk usage.** The image is about 10 GB unpacked. Most of that is the CUDA libraries bundled
with PyTorch. Use `docker system df` to see usage, `docker image prune` to remove old
untagged images left by rebuilds, and `docker builder prune` to clear the build cache.

## Using the gs_ros bridge

See the [gs_ros README](src/genesis_ros/README.md) for the bridge's features and demos.

The bridge's example configs (`src/genesis_ros/configs/*.yaml`) contain URDF paths such as
`src/gs_ros2_control_demos/urdf/...`. These assume the bridge repo was cloned directly into
`src/`, which isn't the case here. Copy a config and change the paths before using it, for
example to `/home/<username>/genesis_ws/src/genesis_ros/gs_ros2_control_demos/urdf/...`.

Also check these before running the configs:
- `panda_demo.yaml` refers to a Panda URDF that isn't in the repo. Start with
  `diff_demo.yaml` instead.
- `parent_config.yaml` contains paths from the original author's machine.

## Roadmap

1. Confirm Genesis runs on the GPU in the CUDA container.
2. Run the bridge with a demo robot, check its topics, and view it in RViz.
3. Test `ros2_control` controllers and `use_sim_time` with the bridge's `/clock`.
4. Add a ROCm variant: a `docker-compose.rocm.yml` with a ROCm PyTorch index and `/dev/kfd`
   and `/dev/dri` devices, sharing the same Dockerfile.
5. Define a stable ROS 2 interface over the simulator so other backends could sit behind it.

## Acknowledgements

- [Genesis](https://github.com/Genesis-Embodied-AI/Genesis), the physics engine
- [gs_ros](https://github.com/vybhav-ibr/genesis_ros), the ROS 2 bridge
- [Ryzers](https://github.com/AMDResearch/Ryzers), a reference for running ROS on AMD/ROCm
