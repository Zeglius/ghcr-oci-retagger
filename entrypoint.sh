#!/bin/bash

set -euo pipefail

# Login into Github Container Registry in skopeo
echo "${GITHUB_TOKEN}" | skopeo login ghcr.io -u "${GITHUB_ACTOR}" --password-stdin

# Execute retaging script
exec /bin/uv run /work/retag.py
