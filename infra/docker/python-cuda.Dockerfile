FROM nvidia/cuda:12.4.0-base-ubuntu22.04

LABEL org.opencontainers.image.title="jeff-course-python-cuda"
LABEL org.opencontainers.image.description="Sandboxed Python+CUDA environment for jeff-course GPU exercises"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_INPUT=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        software-properties-common \
        ca-certificates \
        curl \
        gnupg \
 && add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        git \
        build-essential \
 && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/bin/python3.11 /usr/local/bin/python \
 && ln -sf /usr/bin/python3.11 /usr/local/bin/python3 \
 && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

WORKDIR /workspace

CMD ["bash"]