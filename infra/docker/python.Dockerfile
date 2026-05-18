# jeff-course Python sandbox image (CPU-only fallback).
#
# Used when the user picks the "Container" run mode without GPU. uv handles
# requirements.txt resolution + venv caching; the cache itself is bind
# mounted from the host at /root/.cache/uv so the second run skips
# downloads entirely.
#
# We install `git` and `build-essential` so that pure-source dependencies
# (e.g. older packages without prebuilt wheels) can compile inside the
# container.

FROM python:3.11-slim

LABEL org.opencontainers.image.title="jeff-course-python"
LABEL org.opencontainers.image.description="Sandboxed CPU-only Python environment for jeff-course exercises"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_INPUT=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        git \
        build-essential \
        ca-certificates \
        curl \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir uv

# uv installs into /usr/local/bin via pip already; make sure that's on PATH
# (it is by default for python:slim, this is defensive).
ENV PATH="/usr/local/bin:${PATH}"

WORKDIR /workspace

CMD ["bash"]
