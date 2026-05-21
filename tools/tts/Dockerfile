FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_PROJECT_ENVIRONMENT=/opt/jeff-course-tts
ENV PATH="/root/.local/bin:${UV_PROJECT_ENVIRONMENT}/bin:${PATH}"

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    libsndfile1 \
    sox \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv python install 3.11

WORKDIR /app/tools/tts
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --python 3.11

COPY . .
ENTRYPOINT ["uv", "run", "--frozen", "--python", "3.11", "qwen_tts_pipeline.py"]
