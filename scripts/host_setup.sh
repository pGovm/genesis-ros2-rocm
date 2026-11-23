#!/usr/bin/env bash
# One-time (per user/machine) host setup for the Genesis + ROS2 container
# Write the .env file for docker compose and allows containers to the use the X display

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

cat > "$ENV_FILE" <<EOF
USERNAME=$(id -un)
USER_UID=$(id -u)
USER_GID=$(id -g)
EOF

echo "Wrote $ENV_FILE:"
sed 's/^/ /' "$ENV_FILE"

# Let containers connect to the X server
if command -v xhost >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
    xhost +local:docker >/dev/null
    echo "X11 access granted to local container (DISPLAY:$DISPLAY)."
else
    echo "Warning: xhost not found or DISPLAY unset; GUI apps (RViz, Genesis viewer) won't open."  >&2
fi