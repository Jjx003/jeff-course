#!/usr/bin/env bash
# Build every jeff-course sandbox image locally.
#
# Works in plain bash on Linux/macOS and in Git Bash on Windows (Docker
# Desktop binds the `docker` CLI on PATH the same way in both).
#
# Usage:
#   bash infra/docker/build.sh            # build all images
#   bash infra/docker/build.sh cpp        # build a single image (cpp|python|python-cuda)
#
# Bump the tag suffix here AND in src/lib/server/sandbox/runtime/docker.ts
# (IMAGE_* constants) whenever the Dockerfile contents change.

set -euo pipefail

# Resolve script dir even when invoked via symlink. `cd -P` collapses any
# Windows-style separators that Git Bash leaves behind.
SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

build_image () {
  local key="$1"
  local tag dockerfile
  case "$key" in
    cpp)
      tag="jeff-course/cpp:1"
      dockerfile="cpp.Dockerfile"
      ;;
    python)
      tag="jeff-course/python:1"
      dockerfile="python.Dockerfile"
      ;;
    python-cuda)
      tag="jeff-course/python-cuda:1"
      dockerfile="python-cuda.Dockerfile"
      ;;
    *)
      echo "Unknown image key: $key" >&2
      echo "Valid: cpp | python | python-cuda" >&2
      exit 2
      ;;
  esac

  echo ""
  echo "==> Building ${tag} from ${dockerfile}"
  (
    cd "${SCRIPT_DIR}"
    docker build -t "${tag}" -f "${dockerfile}" .
  )
}

if [ $# -eq 0 ]; then
  build_image cpp
  build_image python
  build_image python-cuda
else
  for key in "$@"; do
    build_image "$key"
  done
fi

echo ""
echo "All requested images built."
